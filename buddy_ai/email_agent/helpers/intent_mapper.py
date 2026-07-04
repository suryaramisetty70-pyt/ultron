# buddy_ai/email_agent/helpers/intent_mapper.py
# Maps raw voice/text commands to structured email intents
# Compatible with command_normalizer.py in the Buddy AI ecosystem

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EmailIntent:
    action: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_command: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# RULE-BASED PATTERN MATCHING (fast path — no AI call needed)
# ─────────────────────────────────────────────────────────────────────────────

# Each entry: (compiled_pattern, action_name, param_extractor_fn or None)
_PATTERNS: List[Tuple[re.Pattern, str, Optional[callable]]] = []


def _register(pattern: str, action: str, extractor=None):
    _PATTERNS.append((re.compile(pattern, re.IGNORECASE), action, extractor))


def _extract_sender(m: re.Match) -> Dict:
    return {"sender": (m.group("sender") or "").strip()}

def _extract_subject(m: re.Match) -> Dict:
    return {"subject": (m.group("subject") or "").strip()}

def _extract_to_and_purpose(m: re.Match) -> Dict:
    return {
        "to": (m.group("to") or "").strip(),
        "purpose": (m.group("purpose") or "").strip(),
    }

def _extract_query(m: re.Match) -> Dict:
    return {"query": (m.group("query") or "").strip()}

def _extract_tone(m: re.Match) -> Dict:
    return {"tone": (m.group("tone") or "professional").strip()}


# NOTE: Pattern ORDER matters — more specific patterns must precede general ones.

# ── OTP (before search to avoid "find verification codes" matching search) ──────
_register(r"\b(otp|one.?time\s+password|verification\s+codes?)\b", "check_otp")

# ── SEARCH ────────────────────────────────────────────────────────────────────
_register(r"\b(search|find|look\s+for)\s+(?P<query>.+)", "search", _extract_query)
_register(r"\bemails?\s+about\s+(?P<query>.+)", "search", _extract_query)

# ── SUMMARIZE (before read_today / read_inbox to avoid being swallowed) ───────
_register(r"\b(summarize|summary)\b.*(thread|conversation)\b", "summarize_thread")
_register(r"\b(summarize|summary|brief|overview)\b.*(inbox|emails?|messages?|today)\b", "summarize_inbox")
_register(r"\bmorning\s+brief\b", "summarize_inbox")
_register(r"\bvoice\s+summary\b", "voice_summary")
_register(r"\b(summarize|summary)\b", "summarize_inbox")
_register(r"\bwhat.?s\s+(new|happening|going\s+on)\b", "summarize_inbox")

# ── URGENT / ATTENTION (before read_important which matches "important") ──────
_register(r"\bwhat\s+needs?\s+(urgent|immediate|my)\s+(attention|response|reply)\b", "check_urgent")
_register(r"\b(urgent|critical)\s+(emails?|messages?|attention)\b", "check_urgent")
_register(r"\bneeds?\s+attention\b", "check_urgent")
_register(r"\b(spam|scam|phish)\b", "check_spam")

# ── CATEGORIES (specific, before generic read/check patterns) ─────────────────
_register(r"\b(job|career|recruitment|hiring|interview)\s*(emails?|messages?)?\b", "check_job_emails")
_register(r"\b(bank|finance|account|transaction)\s*(emails?|alerts?)?\b", "check_bank_alerts")
_register(r"\bsecurity\s+alerts?\b", "check_bank_alerts")
_register(r"\b(college|university|exam|admission|result)\s*(emails?|messages?)?\b", "check_college")
_register(r"\b(promotion|newsletter|offer|deal|sale)\s*(emails?|messages?)?\b", "check_promotions")

# ── AUTOMATION ────────────────────────────────────────────────────────────────
_register(r"\b(archive|clean\s+up)\s+(promotions?|newsletters?|deals?)\b", "archive_promotions")
_register(r"\b(vacation|out\s+of\s+office|ooo)\s*(mode|responder|reply)?\b", "vacation_mode")
_register(r"\b(schedule|send\s+later|delay)\b.*\b(email|message)\b", "schedule_send")
_register(r"\b(follow.?up|reminder)\b", "follow_up")
_register(r"\b(label|tag|categorize|organize)\b", "auto_label")
_register(r"\b(download|save)\s+(attachments?|files?)\b", "download_attachments")

# ── SEND / REPLY / FORWARD ────────────────────────────────────────────────────
_register(r"\b(reply[-\s]?all|respond\s+to\s+all)\b", "reply_all")
_register(
    r"\b(reply|respond)\s+(in\s+a?\s*)?(?P<tone>professional|formal|friendly|brief|casual|apologetic|assertive)\s*(tone|way|manner|style)?\b",
    "reply",
    _extract_tone,
)
_register(r"\b(reply|respond)\s*(professionally|formally|briefly|friendly|assertively)?\b", "reply")
_register(r"\b(forward)\b", "forward")
_register(r"\b(draft|prepare|write\s+up)\b", "draft")
_register(
    r"\b(send|compose|write|email)\s+(an?\s+)?(email|message)?\s*(to\s+)?(?P<to>[\w\s.@+-]+?)(\s+about\s+(?P<purpose>.+))?$",
    "send",
    _extract_to_and_purpose,
)

# ── READ (general — last so specifics above win) ──────────────────────────────
_register(r"\b(unread|new)\s+(emails?|messages?|mail)\b", "read_unread")
_register(r"\b(show|read|get|check)\s+unread\b", "read_unread")
_register(r"\b(important|starred|priority)\s+(emails?|messages?)\b", "read_important")
_register(r"\btoday.?s?\s+(emails?|messages?|mail)\b", "read_today")
_register(r"\b(emails?|messages?)\s+from\s+(?P<sender>[\w\s.@+-]+)", "read_by_sender", _extract_sender)
_register(r"\bfrom\s+(?P<sender>[\w\s.@+-]+)", "read_by_sender", _extract_sender)
_register(r"\b(about|subject|regarding)\s+(?P<subject>.+)", "read_by_subject", _extract_subject)
_register(r"\b(attachments?|files?|documents?)\s*(emails?|messages?)?\b", "read_with_attachments")
_register(r"\b(thread|conversation|chain)\b", "read_thread")
_register(r"\b(check|open|show|read|get)\b.*(inbox|emails|mail)\b", "read_inbox")


def normalize_command(raw_text: str) -> EmailIntent:
    """
    Fast rule-based intent classification.
    Returns EmailIntent with confidence score.
    Falls through to action='unknown' if no rule matches.
    """
    text = raw_text.strip()

    # Strip common buddy wake prefixes
    text = re.sub(r"^(buddy\s+|hey\s+buddy\s+|ok\s+buddy\s+)", "", text, flags=re.IGNORECASE)

    for pattern, action, extractor in _PATTERNS:
        m = pattern.search(text)
        if m:
            params: Dict[str, Any] = {}
            if extractor:
                try:
                    params = extractor(m)
                    # Clean empty strings
                    params = {k: v for k, v in params.items() if v}
                except (IndexError, AttributeError):
                    pass
            return EmailIntent(
                action=action,
                confidence=0.85,
                parameters=params,
                raw_command=raw_text,
            )

    return EmailIntent(
        action="unknown",
        confidence=0.0,
        parameters={},
        raw_command=raw_text,
    )


# ─────────────────────────────────────────────────────────────────────────────
# INTENT → HANDLER ROUTING TABLE
# Used by EmailAgent.handle_command() to dispatch to the right method
# ─────────────────────────────────────────────────────────────────────────────

INTENT_ROUTING: Dict[str, str] = {
    "read_inbox":           "_handle_read_inbox",
    "read_unread":          "_handle_read_unread",
    "read_important":       "_handle_read_important",
    "read_today":           "_handle_read_today",
    "read_by_sender":       "_handle_read_by_sender",
    "read_by_subject":      "_handle_read_by_subject",
    "read_with_attachments":"_handle_read_with_attachments",
    "read_thread":          "_handle_read_thread",
    "search":               "_handle_search",
    "summarize_inbox":      "_handle_summarize_inbox",
    "summarize_thread":     "_handle_summarize_thread",
    "voice_summary":        "_handle_voice_summary",
    "check_urgent":         "_handle_check_urgent",
    "check_spam":           "_handle_check_spam",
    "send":                 "_handle_send",
    "reply":                "_handle_reply",
    "reply_all":            "_handle_reply_all",
    "forward":              "_handle_forward",
    "draft":                "_handle_draft",
    "check_job_emails":     "_handle_check_job_emails",
    "check_bank_alerts":    "_handle_check_bank_alerts",
    "check_otp":            "_handle_check_otp",
    "check_college":        "_handle_check_college",
    "check_promotions":     "_handle_check_promotions",
    "archive_promotions":   "_handle_archive_promotions",
    "vacation_mode":        "_handle_vacation_mode",
    "schedule_send":        "_handle_schedule_send",
    "follow_up":            "_handle_follow_up",
    "auto_label":           "_handle_auto_label",
    "download_attachments": "_handle_download_attachments",
}


def route_intent(action: str) -> Optional[str]:
    """Return the handler method name for a given action string."""
    return INTENT_ROUTING.get(action)
