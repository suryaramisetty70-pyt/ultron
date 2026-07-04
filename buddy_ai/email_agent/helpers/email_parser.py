# buddy_ai/email_agent/helpers/email_parser.py
# Parses raw Gmail API messages into clean structured objects

from __future__ import annotations
import base64
import re
import html
from dataclasses import dataclass, field
from datetime import datetime
from email import policy
from email.parser import BytesParser
from typing import Any, Dict, List, Optional

import html2text
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


@dataclass
class EmailAttachment:
    filename: str
    mime_type: str
    size: int
    attachment_id: str
    data: Optional[bytes] = None


@dataclass
class ParsedEmail:
    message_id: str
    thread_id: str
    subject: str
    sender: str
    sender_email: str
    recipients: List[str]
    cc: List[str]
    bcc: List[str]
    date: Optional[datetime]
    body_text: str
    body_html: str
    snippet: str
    labels: List[str]
    is_read: bool
    is_starred: bool
    is_important: bool
    attachments: List[EmailAttachment]
    raw_headers: Dict[str, str] = field(default_factory=dict)

    @property
    def is_unread(self) -> bool:
        return not self.is_read

    @property
    def has_attachments(self) -> bool:
        return len(self.attachments) > 0

    @property
    def sender_display(self) -> str:
        return self.sender if self.sender else self.sender_email

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "sender": self.sender_display,
            "sender_email": self.sender_email,
            "recipients": self.recipients,
            "date": self.date.isoformat() if self.date else None,
            "snippet": self.snippet,
            "labels": self.labels,
            "is_read": self.is_read,
            "is_starred": self.is_starred,
            "is_important": self.is_important,
            "has_attachments": self.has_attachments,
            "attachments": [
                {"filename": a.filename, "mime_type": a.mime_type, "size": a.size}
                for a in self.attachments
            ],
            "body_preview": self.body_text[:500] if self.body_text else self.snippet,
        }


def _get_header(headers: List[Dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _parse_sender(from_header: str) -> tuple[str, str]:
    """Parse 'Name <email>' format into (name, email)."""
    match = re.match(r'^"?([^"<]*)"?\s*<([^>]+)>', from_header)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    email_match = re.search(r'[\w.+-]+@[\w.-]+', from_header)
    if email_match:
        return "", email_match.group(0)
    return "", from_header.strip()


def _decode_body_part(part: Dict) -> str:
    """Decode base64url-encoded body data."""
    data = part.get("body", {}).get("data", "")
    if not data:
        return ""
    try:
        decoded = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        return decoded
    except Exception:
        return ""


def _extract_body(payload: Dict) -> tuple[str, str]:
    """Recursively extract text and HTML body from message payload."""
    mime_type = payload.get("mimeType", "")
    parts = payload.get("parts", [])
    text_body = ""
    html_body = ""

    if mime_type == "text/plain":
        text_body = _decode_body_part(payload)
    elif mime_type == "text/html":
        html_body = _decode_body_part(payload)
    elif parts:
        for part in parts:
            t, h = _extract_body(part)
            if t:
                text_body += t
            if h:
                html_body += h

    return text_body, html_body


def _html_to_text(html_content: str) -> str:
    """Convert HTML email body to clean plain text."""
    if not html_content:
        return ""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0
    return converter.handle(html_content).strip()


def _extract_attachments(payload: Dict) -> List[EmailAttachment]:
    """Extract attachment metadata from message payload."""
    attachments = []
    parts = payload.get("parts", [])

    for part in parts:
        filename = part.get("filename", "")
        if not filename:
            continue
        mime_type = part.get("mimeType", "application/octet-stream")
        body = part.get("body", {})
        attachment_id = body.get("attachmentId", "")
        size = body.get("size", 0)
        if attachment_id:
            attachments.append(EmailAttachment(
                filename=filename,
                mime_type=mime_type,
                size=size,
                attachment_id=attachment_id,
            ))

    return attachments


def parse_gmail_message(raw_message: Dict) -> ParsedEmail:
    """Parse a raw Gmail API message into a clean ParsedEmail object."""
    payload = raw_message.get("payload", {})
    headers = payload.get("headers", [])
    label_ids = raw_message.get("labelIds", [])

    from_header = _get_header(headers, "From")
    sender_name, sender_email = _parse_sender(from_header)

    to_header = _get_header(headers, "To")
    recipients = [r.strip() for r in to_header.split(",") if r.strip()] if to_header else []

    cc_header = _get_header(headers, "Cc")
    cc = [r.strip() for r in cc_header.split(",") if r.strip()] if cc_header else []

    bcc_header = _get_header(headers, "Bcc")
    bcc = [r.strip() for r in bcc_header.split(",") if r.strip()] if bcc_header else []

    date_str = _get_header(headers, "Date")
    try:
        parsed_date = dateparser.parse(date_str) if date_str else None
    except Exception:
        parsed_date = None

    text_body, html_body = _extract_body(payload)
    if not text_body and html_body:
        text_body = _html_to_text(html_body)

    # Collect all headers for raw access
    raw_headers = {h["name"]: h["value"] for h in headers}

    return ParsedEmail(
        message_id=raw_message.get("id", ""),
        thread_id=raw_message.get("threadId", ""),
        subject=_get_header(headers, "Subject") or "(No Subject)",
        sender=sender_name,
        sender_email=sender_email,
        recipients=recipients,
        cc=cc,
        bcc=bcc,
        date=parsed_date,
        body_text=text_body.strip(),
        body_html=html_body,
        snippet=raw_message.get("snippet", ""),
        labels=label_ids,
        is_read="UNREAD" not in label_ids,
        is_starred="STARRED" in label_ids,
        is_important="IMPORTANT" in label_ids,
        attachments=_extract_attachments(payload),
        raw_headers=raw_headers,
    )
