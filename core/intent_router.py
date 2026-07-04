# core/intent_router.py
"""
Intent Router - Phase 1
Routes user text to the correct agent based on keyword/pattern matching.
Async-compatible. No external ML model required.
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Intent(Enum):
    EMAIL_READ        = "email_read"
    EMAIL_COMPOSE     = "email_compose"
    EMAIL_REPLY       = "email_reply"
    EMAIL_DELETE      = "email_delete"
    CODE_WRITE        = "code_write"
    CODE_EXPLAIN      = "code_explain"
    CODE_DEBUG        = "code_debug"
    CODE_RUN          = "code_run"
    GENERAL           = "general"
    UNKNOWN           = "unknown"


@dataclass
class RouteResult:
    intent: Intent
    agent: str                    # "gmail" | "coding" | "general"
    confidence: float             # 0.0 – 1.0
    matched_pattern: Optional[str]
    original_text: str


# ---------------------------------------------------------------------------
# Pattern definitions
# Each tuple: (regex_pattern, Intent, confidence_score)
# Patterns are tried top-to-bottom; first match wins.
# ---------------------------------------------------------------------------
_EMAIL_PATTERNS: list[tuple[str, Intent, float]] = [
    # Read / check
    (r"\b(read|check|show|open|get|fetch|list)\b.{0,30}\b(email|mail|inbox|message)\b", Intent.EMAIL_READ,    0.95),
    (r"\b(any\s+new|unread|latest)\b.{0,20}\b(email|mail|message)\b",                   Intent.EMAIL_READ,    0.90),
    (r"\bcheck\s+my\s+(inbox|mail)\b",                                                    Intent.EMAIL_READ,    0.95),

    # Compose / send
    (r"\b(send|write|compose|draft|create)\b.{0,30}\b(email|mail|message)\b",            Intent.EMAIL_COMPOSE, 0.95),
    (r"\bemail\s+(to|someone|him|her|them)\b",                                            Intent.EMAIL_COMPOSE, 0.85),

    # Reply
    (r"\b(reply|respond|answer)\b.{0,20}\b(email|mail|message|this)\b",                  Intent.EMAIL_REPLY,   0.95),
    (r"\bwrite\s+back\b",                                                                 Intent.EMAIL_REPLY,   0.85),

    # Delete / archive
    (r"\b(delete|remove|archive|trash)\b.{0,20}\b(email|mail|message|it)\b",             Intent.EMAIL_DELETE,  0.90),
]

_CODE_PATTERNS: list[tuple[str, Intent, float]] = [
    # Write / generate
    (r"\b(write|create|generate|build|make|code)\b.{0,30}\b(function|class|script|program|module|code|snippet)\b", Intent.CODE_WRITE,   0.95),
    (r"\b(implement|code\s+up|program)\b",                                                                          Intent.CODE_WRITE,   0.90),
    (r"\bwrite\s+(me\s+)?(a\s+)?(python|javascript|js|typescript|ts|java|c\+\+|rust|go|bash)\b",                   Intent.CODE_WRITE,   0.95),

    # Explain
    (r"\b(explain|describe|what\s+does|how\s+does)\b.{0,30}\b(code|function|class|method|script|this)\b",          Intent.CODE_EXPLAIN, 0.90),
    (r"\bwhat\s+is\s+this\s+code\b",                                                                                Intent.CODE_EXPLAIN, 0.85),

    # Debug / fix
    (r"\b(debug|fix|find\s+(the\s+)?bug|troubleshoot|resolve|correct)\b.{0,30}\b(code|error|bug|issue|problem)\b", Intent.CODE_DEBUG,   0.95),
    (r"\b(why\s+is\s+this\s+(not\s+)?working|broken|throwing\s+an\s+error)\b",                                     Intent.CODE_DEBUG,   0.85),

    # Run / execute
    (r"\b(run|execute|test|launch)\b.{0,20}\b(code|script|file|program|this)\b",                                   Intent.CODE_RUN,     0.90),
]
_SUMMARY_PATTERNS: list[tuple[str, Intent, float]] = [

    (
        r"\b(summary|summarize|overview|digest|brief)\b",

        Intent.EMAIL_READ,

        0.95
    ),

    (
        r"\bimportant\s+(emails|mail|messages)\b",

        Intent.EMAIL_READ,

        0.95
    ),

    (
        r"\bunread\s+(emails|mail|messages)\b",

        Intent.EMAIL_READ,

        0.90
    ),
]

_GENERAL_PATTERNS: list[tuple[str, Intent, float]] = [
    (r"\b(what\s+(is|are|time|day)|tell\s+me|who\s+is|when\s+is|where\s+is)\b", Intent.GENERAL, 0.70),
    (r"\b(hello|hi|hey|good\s+(morning|afternoon|evening))\b",                   Intent.GENERAL, 0.60),
]

_ALL_PATTERNS = (

    _EMAIL_PATTERNS

    + _SUMMARY_PATTERNS

    + _CODE_PATTERNS

    + _GENERAL_PATTERNS
)

# Agent mapping
_INTENT_TO_AGENT: dict[Intent, str] = {
    Intent.EMAIL_READ:    "gmail",
    Intent.EMAIL_COMPOSE: "gmail",
    Intent.EMAIL_REPLY:   "gmail",
    Intent.EMAIL_DELETE:  "gmail",
    Intent.CODE_WRITE:    "coding",
    Intent.CODE_EXPLAIN:  "coding",
    Intent.CODE_DEBUG:    "coding",
    Intent.CODE_RUN:      "coding",
    Intent.GENERAL:       "general",
    Intent.UNKNOWN:       "general",
}


class IntentRouter:
    """
    Stateless intent router. Call `route(text)` from sync code,
    or `await route_async(text)` from async code.
    """

    def __init__(self, compiled_patterns: bool = True):
        self._patterns = [
            (re.compile(pat, re.IGNORECASE), intent, conf, pat)
            for pat, intent, conf in _ALL_PATTERNS
        ] if compiled_patterns else _ALL_PATTERNS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, text: str) -> RouteResult:
        """Synchronous routing. Safe to call from anywhere."""
        return self._match(text)

    async def route_async(self, text: str) -> RouteResult:
        """Async-compatible wrapper — no blocking I/O, just awaitable."""
        return self._match(text)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _match(self, text: str) -> RouteResult:
        if not text or not text.strip():
            return RouteResult(
                intent=Intent.UNKNOWN,
                agent="general",
                confidence=0.0,
                matched_pattern=None,
                original_text=text,
            )

        cleaned = text.strip().lower()
        best: Optional[tuple[Intent, float, str]] = None

        for compiled_pat, intent, conf, raw_pat in self._patterns:
            if compiled_pat.search(cleaned):
                if best is None or conf > best[1]:
                    best = (intent, conf, raw_pat)
                if conf >= 0.95:          # early exit on high-confidence match
                    break

        if best is None:
            logger.debug("No pattern matched for: %r — defaulting to UNKNOWN", text)
            return RouteResult(
                intent=Intent.UNKNOWN,
                agent="general",
                confidence=0.0,
                matched_pattern=None,
                original_text=text,
            )

        intent, conf, matched_pat = best
        agent = _INTENT_TO_AGENT[intent]

        logger.info(
            "Routed %r → intent=%s  agent=%s  confidence=%.2f",
            text[:60], intent.value, agent, conf,
        )

        return RouteResult(
            intent=intent,
            agent=agent,
            confidence=conf,
            matched_pattern=matched_pat,
            original_text=text,
        )