# buddy_ai/email_agent/helpers/response_formatter.py
# Formats email data into human-readable text and voice-friendly output

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from .email_parser import ParsedEmail


def _relative_time(dt: Optional[datetime]) -> str:
    if not dt:
        return "unknown time"
    now = datetime.now(tz=dt.tzinfo)
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60} minutes ago"
    if seconds < 86400:
        return f"{seconds // 3600} hours ago"
    if seconds < 172800:
        return "yesterday"
    return dt.strftime("%b %d")


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    return f"{size_bytes / (1024*1024):.1f}MB"


def format_email_list_text(emails: List[ParsedEmail], title: str = "Emails") -> str:
    """Format a list of emails for text display."""
    if not emails:
        return f"No {title.lower()} found."

    lines = [f"📬 {title} ({len(emails)} messages)\n" + "─" * 50]
    for i, email in enumerate(emails, 1):
        unread_marker = "🔵 " if email.is_unread else "   "
        important_marker = "⭐ " if email.is_important else ""
        attachment_marker = "📎 " if email.has_attachments else ""
        time_str = _relative_time(email.date)

        lines.append(
            f"{unread_marker}{i:2}. {important_marker}{attachment_marker}"
            f"From: {email.sender_display or email.sender_email}\n"
            f"      Subject: {email.subject}\n"
            f"      {time_str} — {email.snippet[:80]}..."
        )
    return "\n\n".join(lines)


def format_email_list_voice(emails: List[ParsedEmail], title: str = "Emails") -> str:
    """Format email list for voice narration (TTS-friendly)."""
    if not emails:
        return f"You have no {title.lower()}."

    unread_count = sum(1 for e in emails if e.is_unread)
    parts = [f"You have {len(emails)} {title.lower()}, {unread_count} unread."]

    for i, email in enumerate(emails[:10], 1):
        time_str = _relative_time(email.date)
        parts.append(
            f"Number {i}: From {email.sender_display or email.sender_email}, "
            f"subject: {email.subject}, received {time_str}."
        )

    if len(emails) > 10:
        parts.append(f"And {len(emails) - 10} more messages.")

    return " ".join(parts)


def format_single_email_text(email: ParsedEmail) -> str:
    """Format a single email for detailed reading."""
    lines = [
        "─" * 60,
        f"From:    {email.sender_display} <{email.sender_email}>",
        f"To:      {', '.join(email.recipients)}",
    ]
    if email.cc:
        lines.append(f"CC:      {', '.join(email.cc)}")
    lines += [
        f"Subject: {email.subject}",
        f"Date:    {email.date.strftime('%A, %B %d %Y at %I:%M %p') if email.date else 'Unknown'}",
        f"Labels:  {', '.join(email.labels) if email.labels else 'None'}",
    ]
    if email.has_attachments:
        att_list = ", ".join(
            f"{a.filename} ({_format_size(a.size)})" for a in email.attachments
        )
        lines.append(f"Attachments: {att_list}")
    lines += ["─" * 60, "", email.body_text or email.snippet]
    return "\n".join(lines)


def format_single_email_voice(email: ParsedEmail) -> str:
    """Format a single email for voice reading."""
    time_str = email.date.strftime("%A at %I:%M %p") if email.date else "unknown time"
    parts = [
        f"Email from {email.sender_display or email.sender_email}, received {time_str}.",
        f"Subject: {email.subject}.",
    ]
    if email.has_attachments:
        parts.append(f"This email has {len(email.attachments)} attachment(s).")
    body_preview = (email.body_text or email.snippet)[:600].strip()
    parts.append(body_preview)
    return " ".join(parts)


def format_classification_voice(classification: Any, subject: str) -> str:
    """Turn an EmailClassification into a voice-friendly status report."""
    parts = []
    if classification.is_urgent:
        parts.append(f"⚠️ This email is marked URGENT.")
    if classification.is_phishing:
        parts.append(f"🚨 WARNING: This email appears to be a PHISHING attempt.")
    if classification.is_spam:
        parts.append(f"🗑️ This email looks like spam.")
    if classification.is_otp:
        parts.append(f"🔐 This is an OTP or verification code email.")
    if classification.is_job_related:
        parts.append(f"💼 This is a job-related email.")
    if classification.is_bank_alert:
        parts.append(f"🏦 This is a bank or security alert.")
    if classification.deadline:
        parts.append(f"📅 Deadline detected: {classification.deadline}.")
    if classification.action_required:
        parts.append(f"✅ Action required: {classification.action_required}.")
    if classification.contacts_mentioned:
        parts.append(f"👤 Contacts mentioned: {', '.join(classification.contacts_mentioned[:3])}.")
    if classification.meetings_detected:
        parts.append(f"📆 Meeting mentioned: {classification.meetings_detected[0]}.")
    if not parts:
        parts.append(f"Category: {classification.category}. Priority: {classification.priority_score}/10.")
    return " ".join(parts)


def format_send_confirmation(to: str, subject: str, body_preview: str, tone: str = "") -> str:
    """Format a voice confirmation prompt before sending."""
    tone_text = f" ({tone} tone)" if tone else ""
    return (
        f"Ready to send an email{tone_text}.\n"
        f"To: {to}\n"
        f"Subject: {subject}\n"
        f"Preview: {body_preview[:200]}...\n\n"
        f"Say 'confirm' or 'yes' to send, or 'cancel' to abort."
    )


def format_send_confirmation_voice(to: str, subject: str) -> str:
    return (
        f"I'm ready to send an email to {to}, with subject: {subject}. "
        f"Should I go ahead and send it? Say yes to confirm or no to cancel."
    )


def format_thread_text(emails: List[ParsedEmail], thread_subject: str) -> str:
    """Format a full email thread for reading."""
    lines = [f"📧 Thread: {thread_subject}", f"   {len(emails)} messages", "═" * 60]
    for i, email in enumerate(emails, 1):
        time_str = email.date.strftime("%b %d, %I:%M %p") if email.date else "?"
        lines += [
            f"\n[{i}/{len(emails)}] {email.sender_display} — {time_str}",
            "─" * 40,
            (email.body_text or email.snippet)[:800],
        ]
    return "\n".join(lines)


def format_attachment_list(emails: List[ParsedEmail]) -> str:
    """List all attachments found across emails."""
    all_attachments = []
    for email in emails:
        for att in email.attachments:
            all_attachments.append({
                "filename": att.filename,
                "size": att.size,
                "type": att.mime_type,
                "from": email.sender_display,
                "subject": email.subject,
                "date": _relative_time(email.date),
            })

    if not all_attachments:
        return "No attachments found."

    lines = [f"📎 Found {len(all_attachments)} attachments:"]
    for i, att in enumerate(all_attachments, 1):
        lines.append(
            f"{i}. {att['filename']} ({_format_size(att['size'])}) "
            f"— from {att['from']} — {att['date']}"
        )
    return "\n".join(lines)


def build_inbox_stats(emails: List[ParsedEmail]) -> Dict[str, Any]:
    """Compute summary statistics for a list of emails."""
    unread = [e for e in emails if e.is_unread]
    important = [e for e in emails if e.is_important]
    with_attachments = [e for e in emails if e.has_attachments]
    starred = [e for e in emails if e.is_starred]

    senders: Dict[str, int] = {}
    for e in emails:
        key = e.sender_display or e.sender_email
        senders[key] = senders.get(key, 0) + 1
    top_senders = sorted(senders.items(), key=lambda x: -x[1])[:5]

    return {
        "total": len(emails),
        "unread": len(unread),
        "important": len(important),
        "with_attachments": len(with_attachments),
        "starred": len(starred),
        "top_senders": top_senders,
    }
