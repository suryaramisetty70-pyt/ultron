# buddy_ai/email_agent/email_agent.py
# EmailAgent — Production-grade AI email executive assistant
# Extends BaseAgent, integrates with Buddy AI ecosystem
# Supports: Gmail API, OpenAI, async, voice, scheduling, classification

from __future__ import annotations
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent, AgentCommand, AgentResponse, AgentStatus

from .helpers.gmail_auth import build_gmail_service_async
from .helpers.gmail_operations import GmailOperations
from .helpers.ai_engine import AIEmailEngine
from .helpers.intent_mapper import normalize_command, route_intent
from .helpers.scheduler import EmailScheduler
from .helpers.email_parser import ParsedEmail
from .helpers.response_formatter import (
    format_email_list_text,
    format_email_list_voice,
    format_single_email_text,
    format_single_email_voice,
    format_classification_voice,
    format_send_confirmation,
    format_send_confirmation_voice,
    format_thread_text,
    format_attachment_list,
    build_inbox_stats,
)

logger = logging.getLogger("buddy.email_agent")


class EmailAgent(BaseAgent):
    """
    Buddy AI Email Agent
    ────────────────────
    A production-grade AI email executive assistant.
    Handles reading, sending, searching, summarizing, classifying,
    scheduling, and all automation workflows via Gmail API + OpenAI.
    """

    AGENT_ID = "email_agent"
    AGENT_NAME = "Buddy Email Agent"

    def __init__(self, openai_api_key: str, safe_mode: bool = True):
        super().__init__(agent_id=self.AGENT_ID, name=self.AGENT_NAME)
        self.openai_api_key = openai_api_key
        self.safe_mode = safe_mode          # Require voice confirmation before send/destructive actions
        self._gmail_ops: Optional[GmailOperations] = None
        self._ai: Optional[AIEmailEngine] = None
        self._scheduler = EmailScheduler()
        self._initialized = False
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}  # command_id -> pending action

    # ─────────────────────────────────────────────
    # INITIALIZATION
    # ─────────────────────────────────────────────

    async def initialize(self) -> None:
        """Initialize Gmail service and AI engine. Call once before use."""
        try:
            logger.info("Initializing Email Agent...")
            service = await build_gmail_service_async()
            self._gmail_ops = GmailOperations(service)
            self._ai = AIEmailEngine(api_key=self.openai_api_key)
            self._scheduler.set_send_callback(self._scheduled_send_callback)
            self._scheduler.start()
            self._initialized = True
            profile = await self._gmail_ops.get_profile()
            email_address = profile.get("emailAddress", "unknown")
            logger.info(f"Email Agent initialized — connected as: {email_address}")
            await self.event_bus.publish("email_agent.ready", {"email": email_address})
        except Exception as e:
            logger.error(f"Email Agent initialization failed: {e}", exc_info=True)
            self.status = AgentStatus.ERROR
            raise

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "EmailAgent not initialized. Call await agent.initialize() first."
            )

    # ─────────────────────────────────────────────
    # CORE COMMAND DISPATCHER
    # ─────────────────────────────────────────────

    async def handle_command(self, command: AgentCommand) -> AgentResponse:
        """
        Main entry point for all email commands.
        Supports both structured intent (command.intent) and
        raw natural language (command.raw_text) via AI intent extraction.
        """
        self._ensure_initialized()

        try:
            # 1. Handle pending confirmation responses
            if command.intent in ("confirm", "yes") and command.reply_to in self._pending_confirmations:
                return await self._execute_confirmed_action(command.reply_to)
            if command.intent in ("cancel", "no") and command.reply_to in self._pending_confirmations:
                self._pending_confirmations.pop(command.reply_to, None)
                return AgentResponse(
                    command_id=command.command_id,
                    success=True,
                    message="Action cancelled.",
                    voice_text="Got it, action cancelled.",
                )

            # 2. Resolve intent from command
            intent_action = command.intent
            params = command.parameters or {}

            # 3. If no structured intent, run rule-based normalization
            if not intent_action and command.raw_text:
                email_intent = normalize_command(command.raw_text)
                intent_action = email_intent.action
                params = {**email_intent.parameters, **params}

            # 4. If still unknown, use AI to extract intent
            if not intent_action or intent_action == "unknown":
                if command.raw_text and self._ai:
                    ai_intent = await self._ai.extract_intent(command.raw_text)
                    intent_action = ai_intent.get("action", "read_inbox")
                    ai_params = ai_intent.get("parameters", {})
                    params = {**ai_params, **params}
                else:
                    intent_action = "read_inbox"

            # 5. Route to handler
            handler_name = route_intent(intent_action)
            if handler_name and hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                return await handler(command, params)
            else:
                logger.warning(f"No handler for intent: '{intent_action}'")
                return AgentResponse(
                    command_id=command.command_id,
                    success=False,
                    message=f"I don't know how to handle '{intent_action}' yet.",
                    voice_text=f"I'm not sure how to handle that email command.",
                )

        except Exception as e:
            logger.error(f"Error handling command '{command.intent}': {e}", exc_info=True)
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message=f"An error occurred: {str(e)}",
                error=str(e),
                voice_text="Sorry, I ran into an error processing that email command.",
            )

    # ─────────────────────────────────────────────
    # READ HANDLERS
    # ─────────────────────────────────────────────

    async def _handle_read_inbox(self, command: AgentCommand, params: Dict) -> AgentResponse:
        count = int(params.get("count", 20))
        emails = await self._gmail_ops.get_inbox(max_results=count)
        stats = build_inbox_stats(emails)
        text = format_email_list_text(emails, "Inbox")
        voice = format_email_list_voice(emails, "inbox emails")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails], "stats": stats},
            voice_text=voice,
        )

    async def _handle_read_unread(self, command: AgentCommand, params: Dict) -> AgentResponse:
        count = int(params.get("count", 20))
        emails = await self._gmail_ops.get_unread(max_results=count)
        text = format_email_list_text(emails, "Unread Emails")
        voice = format_email_list_voice(emails, "unread emails")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=voice,
        )

    async def _handle_read_important(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.get_important(max_results=20)
        text = format_email_list_text(emails, "Important Emails")
        voice = format_email_list_voice(emails, "important emails")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=voice,
        )

    async def _handle_read_today(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.get_today(max_results=30)
        text = format_email_list_text(emails, "Today's Emails")
        voice = format_email_list_voice(emails, "today's emails")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=voice,
        )

    async def _handle_read_by_sender(self, command: AgentCommand, params: Dict) -> AgentResponse:
        sender = params.get("sender", "")
        if not sender:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Please specify a sender name or email address.",
                voice_text="Who should I look for? Please tell me the sender's name or email.",
            )
        emails = await self._gmail_ops.get_by_sender(sender, max_results=20)
        text = format_email_list_text(emails, f"Emails from {sender}")
        voice = format_email_list_voice(emails, f"emails from {sender}")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails], "sender": sender},
            voice_text=voice,
        )

    async def _handle_read_by_subject(self, command: AgentCommand, params: Dict) -> AgentResponse:
        subject = params.get("subject", "")
        if not subject:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Please specify a subject keyword.",
                voice_text="What subject should I search for?",
            )
        emails = await self._gmail_ops.get_by_subject(subject, max_results=20)
        text = format_email_list_text(emails, f"Emails about '{subject}'")
        voice = format_email_list_voice(emails, f"emails about {subject}")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=voice,
        )

    async def _handle_read_with_attachments(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.get_with_attachments(max_results=20)
        text = format_attachment_list(emails)
        voice = f"Found {len(emails)} emails with attachments."
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=voice,
        )

    async def _handle_read_thread(self, command: AgentCommand, params: Dict) -> AgentResponse:
        thread_id = params.get("thread_id", "")
        message_id = params.get("message_id", "")

        if not thread_id and message_id:
            email = await self._gmail_ops.get_message(message_id)
            thread_id = email.thread_id

        if not thread_id:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Please provide a thread ID or message ID.",
                voice_text="I need a thread or message reference to read the conversation.",
            )

        thread_emails = await self._gmail_ops.get_thread(thread_id)
        subject = thread_emails[0].subject if thread_emails else "Unknown Thread"
        text = format_thread_text(thread_emails, subject)
        voice = f"Thread '{subject}' has {len(thread_emails)} messages."
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"thread": [e.to_dict() for e in thread_emails]},
            voice_text=voice,
        )

    # ─────────────────────────────────────────────
    # SEARCH HANDLER
    # ─────────────────────────────────────────────

    async def _handle_search(self, command: AgentCommand, params: Dict) -> AgentResponse:
        query = params.get("query", command.raw_text or "")
        if not query:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Please provide a search query.",
                voice_text="What would you like me to search for?",
            )
        emails = await self._gmail_ops.search_emails(query, max_results=20)

        # Semantic AI search if result needs ranking
        if self._ai and len(emails) > 3:
            ai_result = await self._ai.smart_search(
                [e.to_dict() for e in emails], query
            )
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message=ai_result,
                data={"emails": [e.to_dict() for e in emails], "query": query},
                voice_text=f"Found {len(emails)} emails matching '{query}'.",
            )

        text = format_email_list_text(emails, f"Search: {query}")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails], "query": query},
            voice_text=f"Found {len(emails)} emails matching '{query}'.",
        )

    # ─────────────────────────────────────────────
    # SUMMARIZE HANDLERS
    # ─────────────────────────────────────────────

    async def _handle_summarize_inbox(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.get_inbox(max_results=20)
        if not emails:
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message="Your inbox is empty.",
                voice_text="Your inbox is empty. Nothing to report.",
            )
        summary = await self._ai.summarize_inbox([e.to_dict() for e in emails])
        stats = build_inbox_stats(emails)
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=summary,
            data={"stats": stats, "email_count": len(emails)},
            voice_text=summary,
        )

    async def _handle_summarize_thread(self, command: AgentCommand, params: Dict) -> AgentResponse:
        thread_id = params.get("thread_id", "")
        message_id = params.get("message_id", "")

        if not thread_id and message_id:
            email = await self._gmail_ops.get_message(message_id)
            thread_id = email.thread_id

        if not thread_id:
            # Summarize latest thread from inbox
            emails = await self._gmail_ops.get_inbox(max_results=1)
            if emails:
                thread_id = emails[0].thread_id
            else:
                return AgentResponse(
                    command_id=command.command_id,
                    success=False,
                    message="No thread found to summarize.",
                    voice_text="I couldn't find a thread to summarize.",
                )

        thread_emails = await self._gmail_ops.get_thread(thread_id)
        thread_data = [
            {
                "sender": e.sender_display,
                "date": e.date.isoformat() if e.date else "",
                "body": e.body_text or e.snippet,
            }
            for e in thread_emails
        ]
        summary = await self._ai.summarize_thread(thread_data)
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=summary,
            data={"thread_id": thread_id, "message_count": len(thread_emails)},
            voice_text=summary,
        )

    async def _handle_voice_summary(self, command: AgentCommand, params: Dict) -> AgentResponse:
        """Comprehensive voice-optimized morning briefing."""
        unread = await self._gmail_ops.get_unread(max_results=10)
        important = await self._gmail_ops.get_important(max_results=5)
        today = await self._gmail_ops.get_today(max_results=20)

        all_emails = {e.message_id: e for e in unread + important + today}
        combined = list(all_emails.values())

        summary = await self._ai.summarize_inbox([e.to_dict() for e in combined])
        urgent = [e for e in combined if e.is_important]

        voice_parts = [f"Good morning. Here's your email briefing. {summary}"]
        if urgent:
            voice_parts.append(
                f"You have {len(urgent)} important emails that may need attention."
            )

        voice_text = " ".join(voice_parts)
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=voice_text,
            data={"unread_count": len(unread), "today_count": len(today)},
            voice_text=voice_text,
        )

    # ─────────────────────────────────────────────
    # URGENT / SECURITY HANDLERS
    # ─────────────────────────────────────────────

    async def _handle_check_urgent(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.get_inbox(max_results=30)
        urgent_report = await self._ai.detect_urgent_items([e.to_dict() for e in emails])
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=urgent_report,
            data={"scanned": len(emails)},
            voice_text=urgent_report,
        )

    async def _handle_check_spam(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.search_emails("in:spam", max_results=20)
        text = format_email_list_text(emails, "Spam / Junk")
        voice = f"You have {len(emails)} emails in your spam folder."
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=voice,
        )

    # ─────────────────────────────────────────────
    # SEND HANDLERS
    # ─────────────────────────────────────────────

    async def _handle_send(self, command: AgentCommand, params: Dict) -> AgentResponse:
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        purpose = params.get("purpose", "")
        tone = params.get("tone", "professional")

        if not to:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Who should I send the email to?",
                voice_text="Who should I send the email to? Please provide a recipient.",
            )

        # Generate email if body not provided
        if not body and (purpose or command.raw_text):
            draft = await self._ai.generate_draft(
                to=to,
                purpose=purpose or command.raw_text,
                tone=tone,
            )
            subject = subject or draft.subject
            body = draft.body

        if not body:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Please provide content or purpose for the email.",
                voice_text="What should the email say? Please give me some content or purpose.",
            )

        # Safe mode: ask for confirmation before sending
        if self.safe_mode:
            self._pending_confirmations[command.command_id] = {
                "action": "send",
                "to": to,
                "subject": subject,
                "body": body,
            }
            confirm_text = format_send_confirmation(to, subject, body, tone)
            voice_confirm = format_send_confirmation_voice(to, subject)
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message=confirm_text,
                data={"awaiting_confirmation": True, "confirmation_id": command.command_id},
                voice_text=voice_confirm,
            )

        msg_id = await self._gmail_ops.send_email(to=to, subject=subject, body=body)
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Email sent to {to}.\nSubject: {subject}",
            data={"message_id": msg_id, "to": to, "subject": subject},
            voice_text=f"Done! Email sent to {to} with subject: {subject}.",
        )

    async def _handle_reply(self, command: AgentCommand, params: Dict) -> AgentResponse:
        message_id = params.get("message_id", "")
        tone = params.get("tone", "professional")
        instructions = params.get("instructions", command.raw_text or "")

        if not message_id:
            # Default to latest unread
            unread = await self._gmail_ops.get_unread(max_results=1)
            if unread:
                message_id = unread[0].message_id
            else:
                return AgentResponse(
                    command_id=command.command_id,
                    success=False,
                    message="No message found to reply to. Please provide a message ID.",
                    voice_text="Which email should I reply to?",
                )

        original = await self._gmail_ops.get_message(message_id)
        generated = await self._ai.generate_reply(
            original_subject=original.subject,
            original_sender=original.sender_display,
            original_body=original.body_text or original.snippet,
            tone=tone,
            user_instructions=instructions,
        )

        if self.safe_mode:
            self._pending_confirmations[command.command_id] = {
                "action": "reply",
                "original": original,
                "body": generated.body,
                "reply_all": False,
            }
            confirm_text = format_send_confirmation(
                original.sender_email, generated.subject, generated.body, tone
            )
            voice_confirm = format_send_confirmation_voice(original.sender_email, generated.subject)
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message=f"Generated {tone} reply:\n\n{generated.body}\n\n{confirm_text}",
                data={"awaiting_confirmation": True, "confirmation_id": command.command_id},
                voice_text=voice_confirm,
            )

        sent_id = await self._gmail_ops.reply_to_email(original, generated.body)
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Reply sent to {original.sender_display}.",
            data={"message_id": sent_id},
            voice_text=f"Reply sent to {original.sender_display}.",
        )

    async def _handle_reply_all(self, command: AgentCommand, params: Dict) -> AgentResponse:
        params["reply_all"] = True
        message_id = params.get("message_id", "")
        tone = params.get("tone", "professional")

        if not message_id:
            unread = await self._gmail_ops.get_unread(max_results=1)
            if unread:
                message_id = unread[0].message_id
            else:
                return AgentResponse(
                    command_id=command.command_id,
                    success=False,
                    message="No message found for reply-all.",
                    voice_text="Which email should I reply to all on?",
                )

        original = await self._gmail_ops.get_message(message_id)
        generated = await self._ai.generate_reply(
            original_subject=original.subject,
            original_sender=original.sender_display,
            original_body=original.body_text or original.snippet,
            tone=tone,
        )

        if self.safe_mode:
            all_recipients = ", ".join(set(original.recipients + original.cc) - {original.sender_email})
            self._pending_confirmations[command.command_id] = {
                "action": "reply",
                "original": original,
                "body": generated.body,
                "reply_all": True,
            }
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message=f"Reply-all to: {all_recipients}\n\n{generated.body}\n\nSay 'confirm' to send.",
                data={"awaiting_confirmation": True},
                voice_text=f"Ready to reply to all {len(original.recipients + original.cc)} recipients. Say confirm to send.",
            )

        sent_id = await self._gmail_ops.reply_to_email(original, generated.body, reply_all=True)
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message="✅ Reply-all sent.",
            data={"message_id": sent_id},
            voice_text="Reply-all sent successfully.",
        )

    async def _handle_forward(self, command: AgentCommand, params: Dict) -> AgentResponse:
        message_id = params.get("message_id", "")
        to = params.get("to", "")
        note = params.get("note", "")

        if not message_id or not to:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Please provide both a message ID and a recipient to forward to.",
                voice_text="Who should I forward the email to?",
            )

        original = await self._gmail_ops.get_message(message_id)
        if self.safe_mode:
            self._pending_confirmations[command.command_id] = {
                "action": "forward",
                "original": original,
                "to": to,
                "note": note,
            }
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message=f"Forward email '{original.subject}' to {to}?\nSay 'confirm' to proceed.",
                data={"awaiting_confirmation": True},
                voice_text=f"Should I forward '{original.subject}' to {to}? Say confirm to proceed.",
            )

        sent_id = await self._gmail_ops.forward_email(original, to, note)
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Email forwarded to {to}.",
            data={"message_id": sent_id},
            voice_text=f"Email forwarded to {to} successfully.",
        )

    async def _handle_draft(self, command: AgentCommand, params: Dict) -> AgentResponse:
        to = params.get("to", "")
        purpose = params.get("purpose", command.raw_text or "")
        tone = params.get("tone", "professional")
        subject = params.get("subject", "")

        if not purpose:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="What should the draft be about?",
                voice_text="What should I draft the email about?",
            )

        draft = await self._ai.generate_draft(to=to or "recipient@example.com", purpose=purpose, tone=tone)
        subject = subject or draft.subject

        if to:
            draft_id = await self._gmail_ops.create_draft(to=to, subject=subject, body=draft.body)
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message=f"✅ Draft saved.\n\nSubject: {subject}\n\n{draft.body}",
                data={"draft_id": draft_id, "subject": subject, "body": draft.body},
                voice_text=f"Draft saved with subject: {subject}. You can review and send it from Gmail.",
            )

        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"📝 Draft generated:\n\nSubject: {subject}\n\n{draft.body}",
            data={"subject": subject, "body": draft.body},
            voice_text=f"Here's your draft with subject: {subject}. Would you like me to save it or send it?",
        )

    # ─────────────────────────────────────────────
    # CATEGORY HANDLERS
    # ─────────────────────────────────────────────

    async def _handle_check_job_emails(self, command: AgentCommand, params: Dict) -> AgentResponse:
        queries = ["job", "career", "recruitment", "interview", "hiring", "position", "opportunity"]
        all_emails = []
        for q in queries[:3]:
            results = await self._gmail_ops.search_emails(q, max_results=10)
            all_emails.extend(results)
        seen = {}
        unique = [seen.setdefault(e.message_id, e) for e in all_emails if e.message_id not in seen]
        text = format_email_list_text(unique, "Job-Related Emails")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in unique]},
            voice_text=f"Found {len(unique)} job-related emails.",
        )

    async def _handle_check_bank_alerts(self, command: AgentCommand, params: Dict) -> AgentResponse:
        queries = ["bank alert", "transaction", "account statement", "security alert", "suspicious activity"]
        all_emails = []
        for q in queries[:3]:
            results = await self._gmail_ops.search_emails(q, max_results=10)
            all_emails.extend(results)
        seen = {}
        unique = [seen.setdefault(e.message_id, e) for e in all_emails if e.message_id not in seen]
        text = format_email_list_text(unique, "Bank & Security Alerts")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in unique]},
            voice_text=f"Found {len(unique)} bank and security emails.",
        )

    async def _handle_check_otp(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.search_emails("OTP OR verification code OR one-time password", max_results=10)
        text = format_email_list_text(emails, "OTP / Verification Codes")
        if emails:
            latest = emails[0]
            voice = f"Latest OTP email: from {latest.sender_display}, subject: {latest.subject}."
        else:
            voice = "No OTP or verification code emails found."
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=voice,
        )

    async def _handle_check_college(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.search_emails(
            "college OR university OR exam result OR admission OR scholarship", max_results=20
        )
        text = format_email_list_text(emails, "College / Exam Emails")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=f"Found {len(emails)} college or exam-related emails.",
        )

    async def _handle_check_promotions(self, command: AgentCommand, params: Dict) -> AgentResponse:
        emails = await self._gmail_ops.get_promotions(max_results=20)
        text = format_email_list_text(emails, "Promotions & Newsletters")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=text,
            data={"emails": [e.to_dict() for e in emails]},
            voice_text=f"You have {len(emails)} promotional emails.",
        )

    # ─────────────────────────────────────────────
    # AUTOMATION HANDLERS
    # ─────────────────────────────────────────────

    async def _handle_archive_promotions(self, command: AgentCommand, params: Dict) -> AgentResponse:
        if self.safe_mode:
            promos = await self._gmail_ops.get_promotions(max_results=50)
            self._pending_confirmations[command.command_id] = {
                "action": "archive_promotions",
                "count": len(promos),
            }
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message=f"Found {len(promos)} promotional emails. Say 'confirm' to archive them all.",
                data={"awaiting_confirmation": True, "count": len(promos)},
                voice_text=f"I found {len(promos)} promotional emails. Should I archive them? Say confirm.",
            )
        count = await self._gmail_ops.archive_all_promotions()
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Archived {count} promotional emails.",
            data={"archived_count": count},
            voice_text=f"Done! Archived {count} promotional emails.",
        )

    async def _handle_vacation_mode(self, command: AgentCommand, params: Dict) -> AgentResponse:
        enabled = params.get("enabled", True)
        subject = params.get("subject", "Out of Office — Auto Reply")
        body = params.get("body", "Thank you for your email. I am currently out of office and will respond upon my return.")
        start_str = params.get("start")
        end_str = params.get("end")

        start_time = datetime.fromisoformat(start_str) if start_str else datetime.now()
        end_time = datetime.fromisoformat(end_str) if end_str else datetime.now() + timedelta(days=7)

        if not enabled:
            await self._gmail_ops.set_vacation_responder(enabled=False)
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message="✅ Vacation auto-reply disabled.",
                voice_text="Vacation mode turned off.",
            )

        if self.safe_mode:
            self._pending_confirmations[command.command_id] = {
                "action": "vacation_mode",
                "enabled": True,
                "subject": subject,
                "body": body,
                "start_time": start_time,
                "end_time": end_time,
            }
            return AgentResponse(
                command_id=command.command_id,
                success=True,
                message=f"Vacation responder:\nSubject: {subject}\n\n{body}\n\nSay 'confirm' to enable.",
                data={"awaiting_confirmation": True},
                voice_text="I've prepared your vacation auto-reply. Say confirm to enable it.",
            )

        await self._gmail_ops.set_vacation_responder(
            enabled=True, subject=subject, body=body,
            start_time=start_time, end_time=end_time,
        )
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Vacation auto-reply enabled until {end_time.strftime('%B %d')}.",
            voice_text=f"Vacation mode enabled until {end_time.strftime('%B %d')}.",
        )

    async def _handle_schedule_send(self, command: AgentCommand, params: Dict) -> AgentResponse:
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        send_at_str = params.get("send_at", "")

        if not all([to, subject, body, send_at_str]):
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Please provide: recipient, subject, body, and send time (ISO format).",
                voice_text="I need the recipient, subject, content, and when to send it.",
            )

        try:
            send_at = datetime.fromisoformat(send_at_str)
        except ValueError:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message=f"Invalid datetime format: {send_at_str}. Use ISO 8601.",
                voice_text="That time format doesn't look right. Please use a standard date and time.",
            )

        job_id = await self._scheduler.schedule_email(
            to=to, subject=subject, body=body, send_at=send_at
        )
        time_str = send_at.strftime("%B %d at %I:%M %p")
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Email scheduled for {time_str}.\nJob ID: {job_id}",
            data={"job_id": job_id, "send_at": send_at.isoformat()},
            voice_text=f"Email to {to} scheduled for {time_str}.",
        )

    async def _handle_follow_up(self, command: AgentCommand, params: Dict) -> AgentResponse:
        message_id = params.get("message_id", "")
        hours = float(params.get("hours", 24))

        if not message_id:
            unread = await self._gmail_ops.get_unread(max_results=1)
            if unread:
                message_id = unread[0].message_id
            else:
                return AgentResponse(
                    command_id=command.command_id,
                    success=False,
                    message="No message found. Please provide a message ID.",
                    voice_text="Which email should I set a follow-up for?",
                )

        email = await self._gmail_ops.get_message(message_id)
        job_id = await self._scheduler.set_follow_up(
            message_id=email.message_id,
            thread_id=email.thread_id,
            subject=email.subject,
            recipient=email.sender_email,
            remind_in_hours=hours,
        )
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Follow-up reminder set for '{email.subject}' in {hours} hours.",
            data={"job_id": job_id, "message_id": message_id},
            voice_text=f"Follow-up reminder set for {email.subject} in {int(hours)} hours.",
        )

    async def _handle_auto_label(self, command: AgentCommand, params: Dict) -> AgentResponse:
        """AI-powered auto-labeling of inbox emails."""
        emails = await self._gmail_ops.get_inbox(max_results=20)
        labelled_count = 0

        label_map = {
            "is_job_related": "Buddy/Jobs",
            "is_bank_alert": "Buddy/Finance",
            "is_otp": "Buddy/OTP",
            "is_college_exam": "Buddy/College",
            "is_urgent": "Buddy/Urgent",
            "is_spam": "Buddy/Suspected-Spam",
        }

        for email in emails[:10]:  # Cap at 10 to avoid rate limits
            try:
                classification = await self._ai.classify_email(
                    subject=email.subject,
                    sender=email.sender_display,
                    body=email.body_text or email.snippet,
                )
                for field_name, label_name in label_map.items():
                    if getattr(classification, field_name, False):
                        await self._gmail_ops.apply_label(email.message_id, label_name)
                        labelled_count += 1
                        break
            except Exception as e:
                logger.warning(f"Failed to label {email.message_id}: {e}")

        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Auto-labelled {labelled_count} emails across {len(emails)} scanned.",
            data={"labelled": labelled_count, "scanned": len(emails)},
            voice_text=f"Done! Auto-labelled {labelled_count} emails.",
        )

    async def _handle_download_attachments(self, command: AgentCommand, params: Dict) -> AgentResponse:
        message_id = params.get("message_id", "")
        save_dir = params.get("save_dir")

        if not message_id:
            emails = await self._gmail_ops.get_with_attachments(max_results=1)
            if emails:
                message_id = emails[0].message_id
            else:
                return AgentResponse(
                    command_id=command.command_id,
                    success=False,
                    message="No emails with attachments found.",
                    voice_text="I couldn't find any emails with attachments.",
                )

        email = await self._gmail_ops.get_message(message_id)
        if not email.has_attachments:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="This email has no attachments.",
                voice_text="This email doesn't have any attachments.",
            )

        saved_paths = await self._gmail_ops.download_all_attachments(email, save_dir)
        paths_text = "\n".join(saved_paths)
        return AgentResponse(
            command_id=command.command_id,
            success=True,
            message=f"✅ Downloaded {len(saved_paths)} attachment(s):\n{paths_text}",
            data={"saved_paths": saved_paths, "count": len(saved_paths)},
            voice_text=f"Downloaded {len(saved_paths)} attachments to your Downloads folder.",
        )

    # ─────────────────────────────────────────────
    # CONFIRMATION EXECUTION
    # ─────────────────────────────────────────────

    async def _execute_confirmed_action(self, confirmation_id: str) -> AgentResponse:
        """Execute a previously queued action after user confirms."""
        pending = self._pending_confirmations.pop(confirmation_id, None)
        if not pending:
            return AgentResponse(
                command_id=confirmation_id,
                success=False,
                message="No pending action found to confirm.",
                voice_text="I don't have a pending action to confirm.",
            )

        action = pending.get("action")

        try:
            if action == "send":
                msg_id = await self._gmail_ops.send_email(
                    to=pending["to"],
                    subject=pending["subject"],
                    body=pending["body"],
                )
                return AgentResponse(
                    command_id=confirmation_id,
                    success=True,
                    message=f"✅ Email sent to {pending['to']}.",
                    data={"message_id": msg_id},
                    voice_text=f"Email sent to {pending['to']} successfully.",
                )

            elif action == "reply":
                msg_id = await self._gmail_ops.reply_to_email(
                    original=pending["original"],
                    body=pending["body"],
                    reply_all=pending.get("reply_all", False),
                )
                return AgentResponse(
                    command_id=confirmation_id,
                    success=True,
                    message="✅ Reply sent.",
                    data={"message_id": msg_id},
                    voice_text="Reply sent successfully.",
                )

            elif action == "forward":
                msg_id = await self._gmail_ops.forward_email(
                    original=pending["original"],
                    to=pending["to"],
                    note=pending.get("note", ""),
                )
                return AgentResponse(
                    command_id=confirmation_id,
                    success=True,
                    message=f"✅ Email forwarded to {pending['to']}.",
                    data={"message_id": msg_id},
                    voice_text=f"Email forwarded to {pending['to']}.",
                )

            elif action == "archive_promotions":
                count = await self._gmail_ops.archive_all_promotions()
                return AgentResponse(
                    command_id=confirmation_id,
                    success=True,
                    message=f"✅ Archived {count} promotional emails.",
                    voice_text=f"Done! Archived {count} promotional emails.",
                )

            elif action == "vacation_mode":
                await self._gmail_ops.set_vacation_responder(
                    enabled=pending["enabled"],
                    subject=pending["subject"],
                    body=pending["body"],
                    start_time=pending.get("start_time"),
                    end_time=pending.get("end_time"),
                )
                return AgentResponse(
                    command_id=confirmation_id,
                    success=True,
                    message="✅ Vacation mode enabled.",
                    voice_text="Vacation auto-reply is now active.",
                )

        except Exception as e:
            logger.error(f"Failed to execute confirmed action '{action}': {e}", exc_info=True)
            return AgentResponse(
                command_id=confirmation_id,
                success=False,
                message=f"Failed to execute action: {e}",
                voice_text="Sorry, something went wrong executing that action.",
                error=str(e),
            )

        return AgentResponse(
            command_id=confirmation_id,
            success=False,
            message=f"Unknown confirmed action: {action}",
        )

    # ─────────────────────────────────────────────
    # SCHEDULER CALLBACK
    # ─────────────────────────────────────────────

    async def _scheduled_send_callback(self, to: str, subject: str, body: str, cc: str = "") -> None:
        await self._gmail_ops.send_email(to=to, subject=subject, body=body, cc=cc)

    # ─────────────────────────────────────────────
    # LIFECYCLE
    # ─────────────────────────────────────────────

    async def start(self) -> None:
        await self.initialize()
        await super().start()

    async def stop(self) -> None:
        self._scheduler.stop()
        await super().stop()
