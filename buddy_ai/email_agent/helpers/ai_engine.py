# buddy_ai/email_agent/helpers/ai_engine.py
# AI layer for email understanding, summarization, classification, and generation
# Uses OpenAI GPT-4o. Swap model string to use any compatible API.

from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

logger = logging.getLogger("buddy.email.ai")


@dataclass
class EmailClassification:
    category: str                   # e.g. work, personal, finance, promo, spam
    is_urgent: bool
    is_spam: bool
    is_phishing: bool
    is_promotion: bool
    is_newsletter: bool
    is_otp: bool
    is_job_related: bool
    is_bank_alert: bool
    is_college_exam: bool
    priority_score: int             # 1–10
    detected_intent: str            # what sender wants
    action_required: str            # what YOU need to do
    deadline: Optional[str]
    contacts_mentioned: List[str]
    meetings_detected: List[str]
    sentiment: str                  # positive, neutral, negative, alarming
    tags: List[str] = field(default_factory=list)


@dataclass
class GeneratedReply:
    subject: str
    body: str
    tone: str


class AIEmailEngine:
    """Wraps OpenAI calls for all email AI features."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def _chat(self, system: str, user: str, json_mode: bool = False) -> str:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def classify_email(self, subject: str, sender: str, body: str) -> EmailClassification:
        """Classify an email across all categories."""
        system = (
            "You are an expert email classification AI. Analyze the email and return ONLY a JSON object "
            "with these exact fields:\n"
            "category (string: work|personal|finance|promotion|spam|newsletter|security|college|job|other),\n"
            "is_urgent (bool), is_spam (bool), is_phishing (bool), is_promotion (bool),\n"
            "is_newsletter (bool), is_otp (bool), is_job_related (bool), is_bank_alert (bool),\n"
            "is_college_exam (bool), priority_score (int 1-10, 10=most urgent),\n"
            "detected_intent (string), action_required (string), deadline (string or null),\n"
            "contacts_mentioned (list of strings), meetings_detected (list of strings),\n"
            "sentiment (positive|neutral|negative|alarming), tags (list of strings)"
        )
        user = f"Subject: {subject}\nFrom: {sender}\n\nBody:\n{body[:3000]}"
        try:
            raw = await self._chat(system, user, json_mode=True)
            data = json.loads(raw)
            return EmailClassification(
                category=data.get("category", "other"),
                is_urgent=bool(data.get("is_urgent", False)),
                is_spam=bool(data.get("is_spam", False)),
                is_phishing=bool(data.get("is_phishing", False)),
                is_promotion=bool(data.get("is_promotion", False)),
                is_newsletter=bool(data.get("is_newsletter", False)),
                is_otp=bool(data.get("is_otp", False)),
                is_job_related=bool(data.get("is_job_related", False)),
                is_bank_alert=bool(data.get("is_bank_alert", False)),
                is_college_exam=bool(data.get("is_college_exam", False)),
                priority_score=int(data.get("priority_score", 5)),
                detected_intent=data.get("detected_intent", ""),
                action_required=data.get("action_required", ""),
                deadline=data.get("deadline"),
                contacts_mentioned=data.get("contacts_mentioned", []),
                meetings_detected=data.get("meetings_detected", []),
                sentiment=data.get("sentiment", "neutral"),
                tags=data.get("tags", []),
            )
        except Exception as e:
            logger.error(f"Email classification failed: {e}")
            return EmailClassification(
                category="other", is_urgent=False, is_spam=False, is_phishing=False,
                is_promotion=False, is_newsletter=False, is_otp=False, is_job_related=False,
                is_bank_alert=False, is_college_exam=False, priority_score=3,
                detected_intent="", action_required="", deadline=None,
                contacts_mentioned=[], meetings_detected=[], sentiment="neutral"
            )

    async def summarize_email(self, subject: str, sender: str, body: str) -> str:
        """Summarize a single email concisely."""
        system = (
            "You are an executive assistant summarizing emails for a busy professional. "
            "Be extremely concise. Summarize in 2-4 sentences. "
            "Include: who sent it, what they want, any deadlines or actions needed."
        )
        user = f"Subject: {subject}\nFrom: {sender}\n\nBody:\n{body[:4000]}"
        return await self._chat(system, user)

    async def summarize_thread(self, thread_emails: List[Dict[str, str]]) -> str:
        """Summarize an entire email thread."""
        system = (
            "You are an executive assistant summarizing an email conversation for a busy professional. "
            "Provide a clear thread summary: who's involved, what was discussed, current status, "
            "and what action (if any) is needed next. Be concise but complete."
        )
        thread_text = "\n\n---\n\n".join([
            f"From: {e.get('sender', '')}\nDate: {e.get('date', '')}\n{e.get('body', '')[:1500]}"
            for e in thread_emails
        ])
        user = f"Email thread ({len(thread_emails)} messages):\n\n{thread_text}"
        return await self._chat(system, user)

    async def summarize_inbox(self, emails: List[Dict[str, Any]]) -> str:
        """Summarize multiple emails as a morning briefing."""
        system = (
            "You are an AI executive assistant giving a morning email briefing. "
            "For each email, mention: sender, subject, and 1-line summary. "
            "At the end, call out any urgent items. Format it naturally for voice reading."
        )
        lines = []
        for i, e in enumerate(emails[:20], 1):
            lines.append(
                f"{i}. From {e.get('sender', 'Unknown')} — Subject: {e.get('subject', 'No subject')} — {e.get('snippet', '')}"
            )
        user = "Here are the emails:\n\n" + "\n".join(lines)
        return await self._chat(system, user)

    async def generate_reply(
        self,
        original_subject: str,
        original_sender: str,
        original_body: str,
        tone: str = "professional",
        user_instructions: str = "",
    ) -> GeneratedReply:
        """Generate a contextually appropriate email reply."""
        tone_guide = {
            "professional": "formal, polite, professional business tone",
            "friendly": "warm, friendly, conversational but still respectful",
            "formal": "very formal, traditional business letter style",
            "brief": "extremely short and to the point, 2-3 sentences max",
            "apologetic": "empathetic and apologetic",
            "assertive": "confident and direct",
        }.get(tone, "professional, polite tone")

        system = (
            f"You are an AI executive assistant writing an email reply. "
            f"Use a {tone_guide}. "
            "Return ONLY a JSON object with fields: 'subject' and 'body'. "
            "The subject should be a proper reply subject line. "
            "The body should be complete and ready to send — no placeholders."
        )
        instructions_text = f"\nAdditional instructions: {user_instructions}" if user_instructions else ""
        user = (
            f"Original email from {original_sender}:\n"
            f"Subject: {original_subject}\n\n"
            f"{original_body[:3000]}"
            f"{instructions_text}\n\n"
            "Write a complete reply."
        )
        try:
            raw = await self._chat(system, user, json_mode=True)
            data = json.loads(raw)
            return GeneratedReply(
                subject=data.get("subject", f"Re: {original_subject}"),
                body=data.get("body", ""),
                tone=tone,
            )
        except Exception as e:
            logger.error(f"Reply generation failed: {e}")
            return GeneratedReply(
                subject=f"Re: {original_subject}",
                body="Thank you for your email. I will get back to you shortly.",
                tone=tone,
            )

    async def generate_draft(
        self,
        to: str,
        purpose: str,
        tone: str = "professional",
        context: str = "",
    ) -> GeneratedReply:
        """Compose a new email from scratch based on user intent."""
        tone_guide = {
            "professional": "professional business tone",
            "friendly": "warm and friendly",
            "formal": "highly formal",
        }.get(tone, "professional")

        system = (
            f"You are an AI executive assistant composing a new email. "
            f"Use {tone_guide}. "
            "Return ONLY a JSON object with fields: 'subject' and 'body'. "
            "Both must be complete — no placeholders, no [brackets]."
        )
        user = (
            f"Write an email to: {to}\n"
            f"Purpose: {purpose}\n"
            f"Additional context: {context if context else 'None'}"
        )
        try:
            raw = await self._chat(system, user, json_mode=True)
            data = json.loads(raw)
            return GeneratedReply(
                subject=data.get("subject", ""),
                body=data.get("body", ""),
                tone=tone,
            )
        except Exception as e:
            logger.error(f"Draft generation failed: {e}")
            return GeneratedReply(subject="", body="", tone=tone)

    async def extract_intent(self, voice_command: str) -> Dict[str, Any]:
        """Extract structured intent from a natural language voice command."""
        system = (
            "You are an AI that extracts email agent intents from voice commands. "
            "Return ONLY a JSON object with these fields:\n"
            "action (string: read_inbox|read_unread|read_important|search|send|reply|forward|"
            "draft|summarize|summarize_thread|check_urgent|archive_promotions|read_by_sender|"
            "read_by_subject|download_attachments|schedule_send|vacation_mode|check_job_emails|"
            "check_bank_alerts|check_otp|check_college|voice_summary),\n"
            "parameters (object with relevant params like sender, subject, query, tone, to, purpose, count)"
        )
        user = f"Voice command: {voice_command}"
        try:
            raw = await self._chat(system, user, json_mode=True)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return {"action": "read_inbox", "parameters": {}}

    async def correct_grammar(self, text: str) -> str:
        """Fix grammar and improve clarity of email text."""
        system = (
            "You are an expert editor. Fix all grammar, spelling, and clarity issues in the text. "
            "Preserve the original tone and intent. Return ONLY the corrected text, nothing else."
        )
        return await self._chat(system, text)

    async def adjust_tone(self, text: str, target_tone: str) -> str:
        """Rewrite email body to match a target tone."""
        system = (
            f"Rewrite the following email to have a {target_tone} tone. "
            "Preserve all factual content and intent. Return ONLY the rewritten email body."
        )
        return await self._chat(system, text)

    async def detect_urgent_items(self, emails: List[Dict[str, Any]]) -> str:
        """Scan inbox and identify items needing immediate attention."""
        system = (
            "You are an executive assistant. Review these emails and identify which ones need "
            "URGENT attention. Explain briefly why each is urgent. Format for voice reading."
        )
        lines = [
            f"- From: {e.get('sender', '')} | Subject: {e.get('subject', '')} | {e.get('snippet', '')}"
            for e in emails[:30]
        ]
        user = "Emails to review:\n" + "\n".join(lines)
        return await self._chat(system, user)

    async def smart_search(self, emails: List[Dict[str, Any]], query: str) -> str:
        """Semantically search emails using AI understanding."""
        system = (
            "You are an intelligent email search assistant. "
            "From the list of emails, find and return those most relevant to the search query. "
            "Briefly explain why each matched. Format for easy reading."
        )
        lines = [
            f"{i+1}. From: {e.get('sender', '')} | Subject: {e.get('subject', '')} | {e.get('snippet', '')}"
            for i, e in enumerate(emails[:50])
        ]
        user = f"Search query: {query}\n\nEmails:\n" + "\n".join(lines)
        return await self._chat(system, user)
