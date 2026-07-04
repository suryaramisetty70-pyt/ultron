# buddy_ai/email_agent/helpers/gmail_operations.py
# All Gmail API operations — read, search, send, label, archive, download
# All methods are async (run in executor to avoid blocking event loop)

from __future__ import annotations
import asyncio
import base64
import email as email_lib
import logging
import mimetypes
import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from googleapiclient.errors import HttpError

from .email_parser import ParsedEmail, parse_gmail_message

logger = logging.getLogger("buddy.email.ops")

# Max retries for API calls
MAX_RETRIES = 3
RETRY_DELAY = 2.0


class GmailOperations:
    """Wraps Gmail API with retry logic, error handling, and async support."""

    def __init__(self, service):
        self.service = service
        self._user = "me"

    def _sync_call(self, func, *args, **kwargs) -> Any:
        """Execute API call with retry logic."""
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                if e.resp.status in (429, 500, 503):
                    import time
                    wait = RETRY_DELAY * (attempt + 1)
                    logger.warning(f"API rate limit/error — retrying in {wait}s (attempt {attempt+1})")
                    import time; time.sleep(wait)
                    last_error = e
                else:
                    raise
        raise last_error

    async def _async(self, func, *args, **kwargs) -> Any:
        """Run sync API call in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._sync_call(func, *args, **kwargs))

    # ─────────────────────────────────────────────
    # READING
    # ─────────────────────────────────────────────

    async def list_messages(
        self,
        query: str = "",
        max_results: int = 20,
        label_ids: Optional[List[str]] = None,
        page_token: Optional[str] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """Return list of message IDs matching query."""
        kwargs: Dict[str, Any] = {"userId": self._user, "maxResults": max_results}
        if query:
            kwargs["q"] = query
        if label_ids:
            kwargs["labelIds"] = label_ids
        if page_token:
            kwargs["pageToken"] = page_token

        result = await self._async(
            self.service.users().messages().list(**kwargs).execute
        )
        messages = result.get("messages", [])
        next_page = result.get("nextPageToken")
        return [m["id"] for m in messages], next_page

    async def get_message(self, message_id: str, format: str = "full") -> ParsedEmail:
        """Fetch and parse a full email message."""
        raw = await self._async(
            self.service.users().messages().get(
                userId=self._user, id=message_id, format=format
            ).execute
        )
        return parse_gmail_message(raw)

    async def get_messages_batch(self, message_ids: List[str]) -> List[ParsedEmail]:
        """Fetch multiple messages concurrently."""
        tasks = [self.get_message(mid) for mid in message_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        emails = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Failed to fetch message: {r}")
            else:
                emails.append(r)
        return emails

    async def get_inbox(self, max_results: int = 20) -> List[ParsedEmail]:
        """Get inbox emails."""
        ids, _ = await self.list_messages(label_ids=["INBOX"], max_results=max_results)
        return await self.get_messages_batch(ids)

    async def get_unread(self, max_results: int = 20) -> List[ParsedEmail]:
        """Get unread emails."""
        ids, _ = await self.list_messages(label_ids=["UNREAD", "INBOX"], max_results=max_results)
        return await self.get_messages_batch(ids)

    async def get_important(self, max_results: int = 20) -> List[ParsedEmail]:
        """Get important/starred emails."""
        ids, _ = await self.list_messages(label_ids=["IMPORTANT"], max_results=max_results)
        return await self.get_messages_batch(ids)

    async def search_emails(self, query: str, max_results: int = 20) -> List[ParsedEmail]:
        """Search emails using Gmail search syntax."""
        ids, _ = await self.list_messages(query=query, max_results=max_results)
        return await self.get_messages_batch(ids)

    async def get_by_sender(self, sender: str, max_results: int = 20) -> List[ParsedEmail]:
        return await self.search_emails(f"from:{sender}", max_results)

    async def get_by_subject(self, subject: str, max_results: int = 20) -> List[ParsedEmail]:
        return await self.search_emails(f"subject:{subject}", max_results)

    async def get_by_date(self, after: datetime, before: Optional[datetime] = None, max_results: int = 20) -> List[ParsedEmail]:
        query = f"after:{after.strftime('%Y/%m/%d')}"
        if before:
            query += f" before:{before.strftime('%Y/%m/%d')}"
        return await self.search_emails(query, max_results)

    async def get_today(self, max_results: int = 30) -> List[ParsedEmail]:
        today = datetime.now().replace(hour=0, minute=0, second=0)
        return await self.get_by_date(today, max_results=max_results)

    async def get_with_attachments(self, max_results: int = 20) -> List[ParsedEmail]:
        return await self.search_emails("has:attachment", max_results)

    async def get_thread(self, thread_id: str) -> List[ParsedEmail]:
        """Get all messages in a thread, ordered by date."""
        raw = await self._async(
            self.service.users().threads().get(
                userId=self._user, id=thread_id, format="full"
            ).execute
        )
        messages = raw.get("messages", [])
        parsed = [parse_gmail_message(m) for m in messages]
        parsed.sort(key=lambda e: e.date or datetime.min)
        return parsed

    async def get_promotions(self, max_results: int = 30) -> List[ParsedEmail]:
        ids, _ = await self.list_messages(label_ids=["CATEGORY_PROMOTIONS"], max_results=max_results)
        return await self.get_messages_batch(ids)

    async def get_social(self, max_results: int = 20) -> List[ParsedEmail]:
        ids, _ = await self.list_messages(label_ids=["CATEGORY_SOCIAL"], max_results=max_results)
        return await self.get_messages_batch(ids)

    # ─────────────────────────────────────────────
    # SENDING
    # ─────────────────────────────────────────────

    def _build_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        reply_to_message: Optional[ParsedEmail] = None,
        attachments: Optional[List[str]] = None,
    ) -> str:
        """Build a RFC2822 message and return base64url-encoded string."""
        if attachments:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body, "plain", "utf-8"))
            for filepath in attachments:
                path = Path(filepath)
                if not path.exists():
                    logger.warning(f"Attachment not found: {filepath}")
                    continue
                mime_type, _ = mimetypes.guess_type(str(path))
                main_type, sub_type = (mime_type or "application/octet-stream").split("/", 1)
                with open(path, "rb") as f:
                    attachment_data = f.read()
                part = MIMEBase(main_type, sub_type)
                part.set_payload(attachment_data)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
                msg.attach(part)
        else:
            msg = MIMEText(body, "plain", "utf-8")

        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc

        if reply_to_message:
            original_msg_id = reply_to_message.raw_headers.get("Message-ID", "")
            if original_msg_id:
                msg["In-Reply-To"] = original_msg_id
                msg["References"] = original_msg_id

        raw_bytes = msg.as_bytes()
        return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        attachments: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        """Send a new email. Returns sent message ID."""
        raw = self._build_message(to=to, subject=subject, body=body, cc=cc, bcc=bcc, attachments=attachments)
        message_body: Dict[str, Any] = {"raw": raw}
        if thread_id:
            message_body["threadId"] = thread_id

        result = await self._async(
            self.service.users().messages().send(
                userId=self._user, body=message_body
            ).execute
        )
        msg_id = result.get("id", "")
        logger.info(f"Email sent — ID: {msg_id}")
        return msg_id

    async def reply_to_email(
        self,
        original: ParsedEmail,
        body: str,
        reply_all: bool = False,
        extra_cc: str = "",
    ) -> str:
        """Reply to an email (optionally reply-all)."""
        to = original.sender_email
        subject = original.subject if original.subject.lower().startswith("re:") else f"Re: {original.subject}"
        cc = ""
        if reply_all:
            all_recipients = set(original.recipients + original.cc)
            all_recipients.discard(original.sender_email)
            cc_parts = list(all_recipients)
            if extra_cc:
                cc_parts.append(extra_cc)
            cc = ", ".join(cc_parts)
        elif extra_cc:
            cc = extra_cc

        raw = self._build_message(
            to=to, subject=subject, body=body, cc=cc,
            reply_to_message=original,
        )
        message_body: Dict[str, Any] = {"raw": raw, "threadId": original.thread_id}
        result = await self._async(
            self.service.users().messages().send(
                userId=self._user, body=message_body
            ).execute
        )
        msg_id = result.get("id", "")
        logger.info(f"Reply sent — ID: {msg_id}")
        return msg_id

    async def forward_email(
        self,
        original: ParsedEmail,
        to: str,
        note: str = "",
    ) -> str:
        """Forward an email to another address."""
        fwd_body = (
            f"{note}\n\n"
            f"---------- Forwarded message ----------\n"
            f"From: {original.sender_display} <{original.sender_email}>\n"
            f"Date: {original.date.strftime('%a, %b %d, %Y at %I:%M %p') if original.date else ''}\n"
            f"Subject: {original.subject}\n\n"
            f"{original.body_text}"
        )
        subject = f"Fwd: {original.subject}"
        return await self.send_email(to=to, subject=subject, body=fwd_body)

    async def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
    ) -> str:
        """Save a draft email."""
        raw = self._build_message(to=to, subject=subject, body=body, cc=cc)
        result = await self._async(
            self.service.users().drafts().create(
                userId=self._user, body={"message": {"raw": raw}}
            ).execute
        )
        draft_id = result.get("id", "")
        logger.info(f"Draft created — ID: {draft_id}")
        return draft_id

    # ─────────────────────────────────────────────
    # LABELS & ORGANIZATION
    # ─────────────────────────────────────────────

    async def list_labels(self) -> List[Dict[str, str]]:
        """Return all Gmail labels."""
        result = await self._async(
            self.service.users().labels().list(userId=self._user).execute
        )
        return result.get("labels", [])

    async def get_or_create_label(self, name: str) -> str:
        """Get label ID by name, creating it if it doesn't exist."""
        labels = await self.list_labels()
        for label in labels:
            if label.get("name", "").lower() == name.lower():
                return label["id"]
        result = await self._async(
            self.service.users().labels().create(
                userId=self._user,
                body={
                    "name": name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            ).execute
        )
        return result["id"]

    async def apply_label(self, message_id: str, label_name: str) -> None:
        """Apply a label to a message."""
        label_id = await self.get_or_create_label(label_name)
        await self._async(
            self.service.users().messages().modify(
                userId=self._user,
                id=message_id,
                body={"addLabelIds": [label_id]},
            ).execute
        )

    async def remove_label(self, message_id: str, label_id: str) -> None:
        await self._async(
            self.service.users().messages().modify(
                userId=self._user,
                id=message_id,
                body={"removeLabelIds": [label_id]},
            ).execute
        )

    async def mark_as_read(self, message_id: str) -> None:
        await self._async(
            self.service.users().messages().modify(
                userId=self._user,
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute
        )

    async def mark_as_unread(self, message_id: str) -> None:
        await self._async(
            self.service.users().messages().modify(
                userId=self._user,
                id=message_id,
                body={"addLabelIds": ["UNREAD"]},
            ).execute
        )

    async def star_message(self, message_id: str) -> None:
        await self._async(
            self.service.users().messages().modify(
                userId=self._user,
                id=message_id,
                body={"addLabelIds": ["STARRED"]},
            ).execute
        )

    async def archive_message(self, message_id: str) -> None:
        """Archive by removing INBOX label."""
        await self._async(
            self.service.users().messages().modify(
                userId=self._user,
                id=message_id,
                body={"removeLabelIds": ["INBOX"]},
            ).execute
        )

    async def trash_message(self, message_id: str) -> None:
        await self._async(
            self.service.users().messages().trash(
                userId=self._user, id=message_id
            ).execute
        )

    async def archive_all_promotions(self) -> int:
        """Archive all promotions. Returns count of archived messages."""
        emails = await self.get_promotions(max_results=50)
        count = 0
        for email in emails:
            try:
                await self.archive_message(email.message_id)
                count += 1
            except Exception as e:
                logger.error(f"Failed to archive {email.message_id}: {e}")
        logger.info(f"Archived {count} promotion emails")
        return count

    # ─────────────────────────────────────────────
    # ATTACHMENTS
    # ─────────────────────────────────────────────

    async def download_attachment(
        self,
        message_id: str,
        attachment_id: str,
        filename: str,
        save_dir: Optional[str] = None,
    ) -> str:
        """Download an attachment and save to disk. Returns saved file path."""
        result = await self._async(
            self.service.users().messages().attachments().get(
                userId=self._user, messageId=message_id, id=attachment_id
            ).execute
        )
        data = base64.urlsafe_b64decode(result.get("data", "") + "==")

        if save_dir is None:
            save_dir = str(Path.home() / "Downloads" / "BuddyAI_Attachments")
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        # Organize by type
        ext = Path(filename).suffix.lower()
        type_folders = {
            ".pdf": "PDFs", ".doc": "Documents", ".docx": "Documents",
            ".xls": "Spreadsheets", ".xlsx": "Spreadsheets",
            ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
            ".zip": "Archives", ".rar": "Archives",
        }
        subfolder = type_folders.get(ext, "Other")
        final_dir = Path(save_dir) / subfolder
        final_dir.mkdir(parents=True, exist_ok=True)

        filepath = final_dir / filename
        # Avoid overwriting
        counter = 1
        while filepath.exists():
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            filepath = final_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        with open(filepath, "wb") as f:
            f.write(data)

        logger.info(f"Attachment saved: {filepath}")
        return str(filepath)

    async def download_all_attachments(self, email: ParsedEmail, save_dir: Optional[str] = None) -> List[str]:
        """Download all attachments from a parsed email."""
        saved_paths = []
        for attachment in email.attachments:
            try:
                path = await self.download_attachment(
                    message_id=email.message_id,
                    attachment_id=attachment.attachment_id,
                    filename=attachment.filename,
                    save_dir=save_dir,
                )
                saved_paths.append(path)
            except Exception as e:
                logger.error(f"Failed to download attachment {attachment.filename}: {e}")
        return saved_paths

    # ─────────────────────────────────────────────
    # VACATION / SETTINGS
    # ─────────────────────────────────────────────

    async def set_vacation_responder(
        self,
        enabled: bool,
        subject: str = "",
        body: str = "",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> None:
        """Enable or disable Gmail vacation auto-responder."""
        settings: Dict[str, Any] = {"enableAutoReply": enabled}
        if enabled:
            settings["responseSubject"] = subject
            settings["responseBodyPlainText"] = body
            settings["restrictToContacts"] = False
            settings["restrictToDomain"] = False
        if start_time:
            settings["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            settings["endTime"] = int(end_time.timestamp() * 1000)

        await self._async(
            self.service.users().settings().updateVacation(
                userId=self._user, body=settings
            ).execute
        )
        action = "enabled" if enabled else "disabled"
        logger.info(f"Vacation responder {action}")

    async def get_profile(self) -> Dict[str, Any]:
        """Get Gmail account profile info."""
        return await self._async(
            self.service.users().getProfile(userId=self._user).execute
        )
