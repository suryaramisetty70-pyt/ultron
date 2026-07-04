# buddy_ai/email_agent/tests/test_email_agent.py
# Test suite for Buddy AI Email Agent
# Run: python -m pytest tests/ -v
# Or:  python tests/test_email_agent.py (standalone)

from __future__ import annotations
import asyncio
import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from buddy_ai.base_agent import AgentCommand, CommandPriority
from buddy_ai.email_agent.helpers.intent_mapper import normalize_command, route_intent
from buddy_ai.email_agent.helpers.email_parser import ParsedEmail, parse_gmail_message
from buddy_ai.email_agent.helpers.response_formatter import (
    format_email_list_text,
    format_email_list_voice,
    format_single_email_text,
    build_inbox_stats,
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def make_parsed_email(**kwargs) -> ParsedEmail:
    defaults = dict(
        message_id="msg_001",
        thread_id="thread_001",
        subject="Test Subject",
        sender="John Doe",
        sender_email="john@example.com",
        recipients=["me@example.com"],
        cc=[],
        bcc=[],
        date=datetime(2024, 5, 15, 10, 30),
        body_text="This is the email body.",
        body_html="<p>This is the email body.</p>",
        snippet="This is the email body.",
        labels=["INBOX", "UNREAD"],
        is_read=False,
        is_starred=False,
        is_important=False,
        attachments=[],
        raw_headers={},
    )
    defaults.update(kwargs)
    return ParsedEmail(**defaults)


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ─────────────────────────────────────────────
# INTENT MAPPER TESTS
# ─────────────────────────────────────────────

class TestIntentMapper(unittest.TestCase):

    def _assert_action(self, text: str, expected_action: str):
        result = normalize_command(text)
        self.assertEqual(
            result.action, expected_action,
            f"'{text}' → expected '{expected_action}', got '{result.action}'"
        )

    def test_read_inbox(self):
        self._assert_action("buddy check my emails", "read_inbox")
        self._assert_action("show inbox", "read_inbox")
        self._assert_action("open my mail", "read_inbox")

    def test_read_unread(self):
        self._assert_action("buddy show unread emails", "read_unread")
        self._assert_action("new messages", "read_unread")
        self._assert_action("show unread", "read_unread")

    def test_read_important(self):
        self._assert_action("read important emails", "read_important")
        self._assert_action("show starred messages", "read_important")

    def test_read_by_sender(self):
        result = normalize_command("emails from amazon")
        self.assertEqual(result.action, "read_by_sender")
        self.assertIn("sender", result.parameters)
        self.assertIn("amazon", result.parameters["sender"].lower())

    def test_search(self):
        result = normalize_command("search emails about invoice")
        self.assertEqual(result.action, "search")

    def test_summarize_inbox(self):
        self._assert_action("buddy summarize today's emails", "summarize_inbox")
        self._assert_action("give me a summary", "summarize_inbox")
        self._assert_action("morning brief", "summarize_inbox")

    def test_check_urgent(self):
        self._assert_action("what needs urgent attention", "check_urgent")
        self._assert_action("show urgent emails", "check_urgent")

    def test_send(self):
        self._assert_action("send email to john@example.com", "send")
        self._assert_action("compose email to Sarah", "send")

    def test_reply(self):
        self._assert_action("reply professionally", "reply")
        self._assert_action("reply to this email", "reply")

    def test_reply_all(self):
        self._assert_action("reply all", "reply_all")
        self._assert_action("respond to all", "reply_all")

    def test_draft(self):
        self._assert_action("draft an email", "draft")
        self._assert_action("prepare a leave request email", "draft")

    def test_check_job_emails(self):
        self._assert_action("check job emails", "check_job_emails")
        self._assert_action("show career emails", "check_job_emails")

    def test_check_bank_alerts(self):
        self._assert_action("check bank alerts", "check_bank_alerts")
        self._assert_action("show security alerts", "check_bank_alerts")

    def test_check_otp(self):
        self._assert_action("check OTP emails", "check_otp")
        self._assert_action("find verification codes", "check_otp")

    def test_archive_promotions(self):
        self._assert_action("archive promotions", "archive_promotions")
        self._assert_action("clean up newsletters", "archive_promotions")

    def test_vacation_mode(self):
        self._assert_action("enable vacation mode", "vacation_mode")
        self._assert_action("set out of office", "vacation_mode")

    def test_download_attachments(self):
        self._assert_action("download attachments", "download_attachments")
        self._assert_action("save files from email", "download_attachments")

    def test_unknown_falls_through(self):
        result = normalize_command("what is the weather today")
        self.assertEqual(result.action, "unknown")

    def test_buddy_prefix_stripped(self):
        r1 = normalize_command("buddy check my emails")
        r2 = normalize_command("check my emails")
        self.assertEqual(r1.action, r2.action)

    def test_route_intent_returns_handler(self):
        for action in [
            "read_inbox", "read_unread", "read_important", "search",
            "summarize_inbox", "send", "reply", "draft", "check_urgent",
        ]:
            handler = route_intent(action)
            self.assertIsNotNone(handler, f"No handler registered for: {action}")
            self.assertTrue(handler.startswith("_handle_"))


# ─────────────────────────────────────────────
# EMAIL PARSER TESTS
# ─────────────────────────────────────────────

class TestEmailParser(unittest.TestCase):

    def _make_raw_message(self, **overrides):
        msg = {
            "id": "msg123",
            "threadId": "thread123",
            "labelIds": ["INBOX", "UNREAD", "IMPORTANT"],
            "snippet": "Hello this is a test email snippet",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Jane Smith <jane@example.com>"},
                    {"name": "To", "value": "me@example.com"},
                    {"name": "Subject", "value": "Project Update"},
                    {"name": "Date", "value": "Thu, 15 May 2024 10:30:00 +0000"},
                    {"name": "Cc", "value": "boss@example.com"},
                ],
                "mimeType": "text/plain",
                "body": {"data": "SGVsbG8gdGhpcyBpcyBhIHRlc3QgZW1haWwgYm9keQ=="},
                "parts": [],
            },
        }
        msg.update(overrides)
        return msg

    def test_basic_parse(self):
        raw = self._make_raw_message()
        email = parse_gmail_message(raw)
        self.assertEqual(email.message_id, "msg123")
        self.assertEqual(email.thread_id, "thread123")
        self.assertEqual(email.subject, "Project Update")
        self.assertEqual(email.sender, "Jane Smith")
        self.assertEqual(email.sender_email, "jane@example.com")
        self.assertIn("me@example.com", email.recipients)
        self.assertIn("boss@example.com", email.cc)
        self.assertFalse(email.is_read)
        self.assertTrue(email.is_important)

    def test_unread_detection(self):
        raw = self._make_raw_message()
        raw["labelIds"] = ["INBOX", "UNREAD"]
        email = parse_gmail_message(raw)
        self.assertTrue(email.is_unread)

    def test_read_detection(self):
        raw = self._make_raw_message()
        raw["labelIds"] = ["INBOX"]
        email = parse_gmail_message(raw)
        self.assertTrue(email.is_read)
        self.assertFalse(email.is_unread)

    def test_starred_detection(self):
        raw = self._make_raw_message()
        raw["labelIds"] = ["INBOX", "STARRED"]
        email = parse_gmail_message(raw)
        self.assertTrue(email.is_starred)

    def test_no_subject_fallback(self):
        raw = self._make_raw_message()
        raw["payload"]["headers"] = [h for h in raw["payload"]["headers"] if h["name"] != "Subject"]
        email = parse_gmail_message(raw)
        self.assertEqual(email.subject, "(No Subject)")

    def test_sender_email_only(self):
        raw = self._make_raw_message()
        for h in raw["payload"]["headers"]:
            if h["name"] == "From":
                h["value"] = "noreply@company.com"
        email = parse_gmail_message(raw)
        self.assertEqual(email.sender_email, "noreply@company.com")
        self.assertEqual(email.sender_display, "noreply@company.com")

    def test_to_dict(self):
        raw = self._make_raw_message()
        email = parse_gmail_message(raw)
        d = email.to_dict()
        self.assertIn("message_id", d)
        self.assertIn("subject", d)
        self.assertIn("sender", d)
        self.assertIn("is_read", d)
        self.assertIn("has_attachments", d)


# ─────────────────────────────────────────────
# RESPONSE FORMATTER TESTS
# ─────────────────────────────────────────────

class TestResponseFormatter(unittest.TestCase):

    def _make_emails(self, count=3):
        emails = []
        for i in range(count):
            emails.append(make_parsed_email(
                message_id=f"msg_{i:03d}",
                subject=f"Test Email {i+1}",
                sender=f"Sender {i+1}",
                sender_email=f"sender{i+1}@example.com",
                is_read=(i % 2 == 0),
                is_important=(i == 0),
            ))
        return emails

    def test_format_email_list_text_empty(self):
        result = format_email_list_text([], "Inbox")
        self.assertTrue("no" in result.lower() or "empty" in result.lower() or "found" in result.lower())

    def test_format_email_list_text(self):
        emails = self._make_emails(3)
        result = format_email_list_text(emails, "Test Inbox")
        self.assertIn("Test Inbox", result)
        self.assertIn("Test Email 1", result)
        self.assertIn("Test Email 2", result)

    def test_format_email_list_voice_empty(self):
        result = format_email_list_voice([], "inbox emails")
        self.assertIn("no", result.lower())

    def test_format_email_list_voice(self):
        emails = self._make_emails(5)
        result = format_email_list_voice(emails, "inbox emails")
        self.assertIn("5", result)

    def test_format_single_email_text(self):
        email = make_parsed_email()
        result = format_single_email_text(email)
        self.assertIn("John Doe", result)
        self.assertIn("Test Subject", result)
        self.assertIn("This is the email body.", result)

    def test_build_inbox_stats(self):
        emails = self._make_emails(5)
        stats = build_inbox_stats(emails)
        self.assertEqual(stats["total"], 5)
        self.assertIn("unread", stats)
        self.assertIn("important", stats)
        self.assertIn("top_senders", stats)


# ─────────────────────────────────────────────
# EMAIL AGENT INTEGRATION TESTS (mocked)
# ─────────────────────────────────────────────

class TestEmailAgentIntegration(unittest.TestCase):
    """Integration tests using mocked Gmail service and AI engine."""

    def setUp(self):
        from buddy_ai.email_agent.email_agent import EmailAgent
        self.agent = EmailAgent(openai_api_key="test-key", safe_mode=False)

        # Mock internal components
        self.agent._initialized = True
        self.agent._gmail_ops = MagicMock()
        self.agent._ai = MagicMock()

        # Set up default return values
        self.mock_emails = [
            make_parsed_email(message_id=f"msg_{i}", subject=f"Email {i}", sender=f"User {i}")
            for i in range(3)
        ]

    def _make_command(self, intent="", raw_text="", **params) -> AgentCommand:
        return AgentCommand(intent=intent, raw_text=raw_text, parameters=params)

    def test_read_inbox_returns_emails(self):
        self.agent._gmail_ops.get_inbox = AsyncMock(return_value=self.mock_emails)
        cmd = self._make_command(intent="read_inbox")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)
        self.assertIsNotNone(response.data)
        self.assertEqual(len(response.data["emails"]), 3)

    def test_read_unread_returns_emails(self):
        self.agent._gmail_ops.get_unread = AsyncMock(return_value=self.mock_emails[:2])
        cmd = self._make_command(intent="read_unread")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)

    def test_search_returns_results(self):
        self.agent._gmail_ops.search_emails = AsyncMock(return_value=self.mock_emails)
        self.agent._ai.smart_search = AsyncMock(return_value="Smart search result")
        cmd = self._make_command(intent="search", query="invoice")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)

    def test_summarize_inbox(self):
        self.agent._gmail_ops.get_inbox = AsyncMock(return_value=self.mock_emails)
        self.agent._ai.summarize_inbox = AsyncMock(return_value="You have 3 emails. One from User 0.")
        cmd = self._make_command(intent="summarize_inbox")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)
        self.assertIn("3 emails", response.message)

    def test_send_requires_recipient(self):
        cmd = self._make_command(intent="send")  # No 'to' param
        response = run_async(self.agent.handle_command(cmd))
        self.assertFalse(response.success)

    def test_send_with_safe_mode_off(self):
        self.agent.safe_mode = False
        self.agent._gmail_ops.send_email = AsyncMock(return_value="sent_msg_id")
        self.agent._ai.generate_draft = AsyncMock(return_value=MagicMock(
            subject="Test Subject", body="Test body"
        ))
        cmd = self._make_command(intent="send", to="test@example.com", purpose="test")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)

    def test_send_with_safe_mode_requires_confirmation(self):
        self.agent.safe_mode = True
        self.agent._ai.generate_draft = AsyncMock(return_value=MagicMock(
            subject="Leave Request", body="Dear Manager, I would like to take leave."
        ))
        cmd = self._make_command(intent="send", to="manager@example.com", purpose="leave request")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)
        self.assertTrue(response.data.get("awaiting_confirmation"))

    def test_draft_generates_email(self):
        self.agent._ai.generate_draft = AsyncMock(return_value=MagicMock(
            subject="Leave Request", body="Dear team, I need a day off."
        ))
        cmd = self._make_command(intent="draft", purpose="draft a leave request email")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)
        self.assertIn("Leave Request", response.message)

    def test_archive_promotions_safe_mode(self):
        self.agent.safe_mode = True
        self.agent._gmail_ops.get_promotions = AsyncMock(return_value=self.mock_emails)
        cmd = self._make_command(intent="archive_promotions")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)
        self.assertTrue(response.data.get("awaiting_confirmation"))

    def test_confirmation_executes_send(self):
        self.agent._gmail_ops.send_email = AsyncMock(return_value="sent_id")
        # Pre-load a pending confirmation
        cmd_id = "test-cmd-001"
        self.agent._pending_confirmations[cmd_id] = {
            "action": "send",
            "to": "test@example.com",
            "subject": "Hello",
            "body": "Test body",
        }
        cmd = AgentCommand(command_id="confirm-cmd", intent="confirm", reply_to=cmd_id)
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)
        self.assertIn("sent", response.message.lower())

    def test_raw_text_routing_to_read_inbox(self):
        self.agent._gmail_ops.get_inbox = AsyncMock(return_value=self.mock_emails)
        cmd = self._make_command(raw_text="buddy check my emails")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)

    def test_unknown_intent_falls_through_gracefully(self):
        self.agent._ai.extract_intent = AsyncMock(return_value={
            "action": "read_inbox",
            "parameters": {}
        })
        self.agent._gmail_ops.get_inbox = AsyncMock(return_value=self.mock_emails)
        cmd = self._make_command(raw_text="xyzzy frobulate the qux")
        response = run_async(self.agent.handle_command(cmd))
        # Should not crash — fallback to read_inbox via AI
        self.assertIsNotNone(response)

    def test_check_job_emails(self):
        self.agent._gmail_ops.search_emails = AsyncMock(return_value=self.mock_emails[:2])
        cmd = self._make_command(intent="check_job_emails")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)

    def test_check_bank_alerts(self):
        self.agent._gmail_ops.search_emails = AsyncMock(return_value=self.mock_emails[:1])
        cmd = self._make_command(intent="check_bank_alerts")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)

    def test_voice_summary(self):
        self.agent._gmail_ops.get_unread = AsyncMock(return_value=self.mock_emails)
        self.agent._gmail_ops.get_important = AsyncMock(return_value=[])
        self.agent._gmail_ops.get_today = AsyncMock(return_value=self.mock_emails)
        self.agent._ai.summarize_inbox = AsyncMock(return_value="You have 3 emails to review.")
        cmd = self._make_command(intent="voice_summary")
        response = run_async(self.agent.handle_command(cmd))
        self.assertTrue(response.success)
        self.assertIsNotNone(response.voice_text)

    def test_response_always_has_voice_text(self):
        """Every successful response should have voice_text populated."""
        self.agent._gmail_ops.get_inbox = AsyncMock(return_value=self.mock_emails)
        cmd = self._make_command(intent="read_inbox")
        response = run_async(self.agent.handle_command(cmd))
        self.assertIsNotNone(response.voice_text)
        self.assertNotEqual(response.voice_text, "")


# ─────────────────────────────────────────────
# COMMAND NORMALIZER TESTS
# ─────────────────────────────────────────────

class TestCommandNormalizer(unittest.TestCase):

    def test_email_routing(self):
        from buddy_ai.command_normalizer import normalize_command as top_normalize
        result = top_normalize("buddy check my inbox")
        self.assertEqual(result.agent, "email")

    def test_coding_routing(self):
        from buddy_ai.command_normalizer import normalize_command as top_normalize
        result = top_normalize("fix this python function")
        self.assertEqual(result.agent, "coding")

    def test_pc_routing(self):
        from buddy_ai.command_normalizer import normalize_command as top_normalize
        result = top_normalize("open chrome browser")
        self.assertEqual(result.agent, "pc")


# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Buddy AI — Email Agent Test Suite")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestIntentMapper))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailParser))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailAgentIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandNormalizer))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
