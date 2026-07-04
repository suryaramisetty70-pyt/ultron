# buddy_ai/email_agent/demo.py
# Quick-start demo for Buddy AI Email Agent
# Tests real Gmail API + OpenAI integration
# Run: python demo.py

from __future__ import annotations
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from buddy_ai.agent_manager import AgentManager


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

TEST_COMMANDS = [
    "buddy check my emails",
    "buddy show unread emails",
    "buddy read important emails",
    "buddy summarize today's emails",
    "buddy what needs urgent attention",
    "buddy check job emails",
    "buddy check bank alerts",
    "buddy check OTP emails",
    "buddy show promotions",
    "buddy voice summary",
    "buddy search emails from amazon",
    "buddy show emails with attachments",
]


async def main():
    if not OPENAI_API_KEY:
        print("ERROR: Set OPENAI_API_KEY environment variable first.")
        print("  Windows: set OPENAI_API_KEY=your-key-here")
        print("  Linux/Mac: export OPENAI_API_KEY=your-key-here")
        sys.exit(1)

    print("=" * 60)
    print("Buddy AI Email Agent — Live Demo")
    print("=" * 60)
    print()

    manager = AgentManager()
    try:
        await manager.initialize(openai_api_key=OPENAI_API_KEY, safe_mode=True)
        print("✅ Agent Manager initialized\n")

        for command in TEST_COMMANDS:
            print(f"🎤 Command: {command}")
            print("-" * 40)
            response = await manager.execute(command)
            if response.success:
                print(f"✅ Success")
                if response.voice_text:
                    print(f"🔊 Voice: {response.voice_text[:200]}")
                print(f"📄 Message: {response.message[:300]}")
            else:
                print(f"❌ Failed: {response.message}")
            print()
            await asyncio.sleep(1)  # Be kind to API rate limits

    finally:
        await manager.shutdown()
        print("Agent Manager shut down.")


if __name__ == "__main__":
    asyncio.run(main())
