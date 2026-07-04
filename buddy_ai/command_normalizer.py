# buddy_ai/command_normalizer.py
# Top-level command normalizer for Buddy AI ecosystem
# Routes raw voice/text commands to the correct agent

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class NormalizedCommand:
    agent: str          # "email" | "pc" | "coding" | "unknown"
    intent: str
    parameters: Dict[str, Any]
    raw_text: str
    confidence: float


# Agent routing keywords
_EMAIL_KEYWORDS = re.compile(
    r"\b(email|inbox|mail|unread|send|reply|forward|draft|attachment|"
    r"gmail|newsletter|spam|phishing|otp|vacation\s+mode|"
    r"message(s)?|compose|subscribe|thread|correspondence)\b",
    re.IGNORECASE,
)

_PC_KEYWORDS = re.compile(
    r"\b(open|close|launch|run|execute|file|folder|desktop|"
    r"screenshot|browser|chrome|firefox|app|application|"
    r"volume|screen|window|minimize|maximize|type|click|scroll)\b",
    re.IGNORECASE,
)

_CODING_KEYWORDS = re.compile(
    r"\b(code|script|function|debug|fix|error|python|javascript|"
    r"typescript|class|method|variable|import|module|test|unit test|"
    r"refactor|lint|compile|build|deploy|git|github|commit|push|pull)\b",
    re.IGNORECASE,
)


def normalize_command(raw_text: str) -> NormalizedCommand:
    """
    Route a raw user command to the correct Buddy AI agent.
    Returns a NormalizedCommand with agent name and basic intent.
    The target agent's own intent mapper handles fine-grained routing.
    """
    text = raw_text.strip()

    # Strip wake word prefix
    clean = re.sub(r"^(buddy\s+|hey\s+buddy\s+|ok\s+buddy\s+)", "", text, flags=re.IGNORECASE)

    email_score = len(_EMAIL_KEYWORDS.findall(clean))
    pc_score = len(_PC_KEYWORDS.findall(clean))
    coding_score = len(_CODING_KEYWORDS.findall(clean))

    if email_score >= pc_score and email_score >= coding_score:
        agent = "email"
        confidence = min(0.95, 0.6 + email_score * 0.1)
    elif pc_score > coding_score:
        agent = "pc"
        confidence = min(0.95, 0.6 + pc_score * 0.1)
    elif coding_score > 0:
        agent = "coding"
        confidence = min(0.95, 0.6 + coding_score * 0.1)
    else:
        agent = "unknown"
        confidence = 0.3

    return NormalizedCommand(
        agent=agent,
        intent="",          # Fine-grained intent resolved by each agent
        parameters={},
        raw_text=raw_text,
        confidence=confidence,
    )
