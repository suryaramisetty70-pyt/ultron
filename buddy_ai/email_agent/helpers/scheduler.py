# buddy_ai/email_agent/helpers/scheduler.py
# Handles scheduled email sending and follow-up reminders
# Uses APScheduler with asyncio support

from __future__ import annotations
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("buddy.email.scheduler")


@dataclass
class ScheduledEmail:
    job_id: str
    to: str
    subject: str
    body: str
    scheduled_time: datetime
    cc: str = ""
    status: str = "pending"   # pending | sent | cancelled | failed


@dataclass
class FollowUpReminder:
    job_id: str
    message_id: str
    thread_id: str
    subject: str
    recipient: str
    remind_at: datetime
    status: str = "active"


class EmailScheduler:
    """Manages scheduled sends and follow-up reminders."""

    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._scheduled_emails: Dict[str, ScheduledEmail] = {}
        self._follow_ups: Dict[str, FollowUpReminder] = {}
        self._send_callback: Optional[Callable[..., Coroutine]] = None

    def set_send_callback(self, callback: Callable[..., Coroutine]) -> None:
        """Register the async function to call when sending a scheduled email."""
        self._send_callback = callback

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Email scheduler started")

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Email scheduler stopped")

    async def schedule_email(
        self,
        to: str,
        subject: str,
        body: str,
        send_at: datetime,
        cc: str = "",
    ) -> str:
        """Schedule an email to be sent at a specific time. Returns job_id."""
        job_id = str(uuid.uuid4())[:8]
        scheduled = ScheduledEmail(
            job_id=job_id,
            to=to,
            subject=subject,
            body=body,
            scheduled_time=send_at,
            cc=cc,
        )
        self._scheduled_emails[job_id] = scheduled

        self._scheduler.add_job(
            func=self._execute_scheduled_send,
            trigger=DateTrigger(run_date=send_at),
            args=[job_id],
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Email scheduled — ID: {job_id} — at: {send_at}")
        return job_id

    async def _execute_scheduled_send(self, job_id: str) -> None:
        scheduled = self._scheduled_emails.get(job_id)
        if not scheduled:
            logger.warning(f"Scheduled email {job_id} not found")
            return
        if scheduled.status != "pending":
            return
        try:
            if self._send_callback:
                await self._send_callback(
                    to=scheduled.to,
                    subject=scheduled.subject,
                    body=scheduled.body,
                    cc=scheduled.cc,
                )
            scheduled.status = "sent"
            logger.info(f"Scheduled email {job_id} sent successfully")
        except Exception as e:
            scheduled.status = "failed"
            logger.error(f"Failed to send scheduled email {job_id}: {e}")

    def cancel_scheduled_email(self, job_id: str) -> bool:
        """Cancel a pending scheduled email. Returns True if cancelled."""
        scheduled = self._scheduled_emails.get(job_id)
        if not scheduled or scheduled.status != "pending":
            return False
        try:
            self._scheduler.remove_job(job_id)
            scheduled.status = "cancelled"
            logger.info(f"Scheduled email {job_id} cancelled")
            return True
        except Exception:
            return False

    async def set_follow_up(
        self,
        message_id: str,
        thread_id: str,
        subject: str,
        recipient: str,
        remind_in_hours: float = 24.0,
        callback: Optional[Callable[..., Coroutine]] = None,
    ) -> str:
        """Set a follow-up reminder for an email. Returns reminder_id."""
        job_id = str(uuid.uuid4())[:8]
        remind_at = datetime.utcnow() + timedelta(hours=remind_in_hours)
        reminder = FollowUpReminder(
            job_id=job_id,
            message_id=message_id,
            thread_id=thread_id,
            subject=subject,
            recipient=recipient,
            remind_at=remind_at,
        )
        self._follow_ups[job_id] = reminder

        async def _fire_reminder():
            logger.info(f"Follow-up reminder fired for: '{subject}' to {recipient}")
            if callback:
                await callback(reminder)
            reminder.status = "fired"

        self._scheduler.add_job(
            func=_fire_reminder,
            trigger=DateTrigger(run_date=remind_at),
            id=f"followup_{job_id}",
            replace_existing=True,
        )
        return job_id

    def cancel_follow_up(self, job_id: str) -> bool:
        reminder = self._follow_ups.get(job_id)
        if not reminder or reminder.status != "active":
            return False
        try:
            self._scheduler.remove_job(f"followup_{job_id}")
            reminder.status = "cancelled"
            return True
        except Exception:
            return False

    def list_scheduled(self) -> List[Dict[str, Any]]:
        return [
            {
                "job_id": s.job_id,
                "to": s.to,
                "subject": s.subject,
                "scheduled_time": s.scheduled_time.isoformat(),
                "status": s.status,
            }
            for s in self._scheduled_emails.values()
        ]

    def list_follow_ups(self) -> List[Dict[str, Any]]:
        return [
            {
                "job_id": f.job_id,
                "subject": f.subject,
                "recipient": f.recipient,
                "remind_at": f.remind_at.isoformat(),
                "status": f.status,
            }
            for f in self._follow_ups.values()
        ]
