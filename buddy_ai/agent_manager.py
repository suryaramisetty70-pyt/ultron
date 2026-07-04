# buddy_ai/agent_manager.py
# AgentManager — Central orchestrator for all Buddy AI agents
# Initializes, routes commands, and manages agent lifecycle

from __future__ import annotations
import asyncio
import logging
import os
from typing import Any, Dict, Optional

from .base_agent import AgentCommand, AgentResponse, AgentRegistry, CommandPriority
from .command_normalizer import normalize_command
from .email_agent import EmailAgent

logger = logging.getLogger("buddy.agent_manager")


class AgentManager:
    """
    Central command router for the Buddy AI ecosystem.
    Dispatches commands to the appropriate agent based on intent.
    """

    def __init__(self):
        self._email_agent: Optional[EmailAgent] = None
        self._ready = False

    async def initialize(
        self,
        openai_api_key: str,
        safe_mode: bool = True,
    ) -> None:
        """Initialize all registered agents."""
        logger.info("Initializing Buddy AI Agent Manager...")

        # Initialize Email Agent
        self._email_agent = EmailAgent(
            openai_api_key=openai_api_key,
            safe_mode=safe_mode,
        )
        await self._email_agent.start()

        # Future: initialize pc_agent, coding_agent here
        # self._pc_agent = PCAgent(...)
        # self._coding_agent = CodingAgent(...)

        self._ready = True
        logger.info("Agent Manager ready. All agents initialized.")

    async def shutdown(self) -> None:
        """Gracefully stop all agents."""
        if self._email_agent:
            await self._email_agent.stop()
        logger.info("Agent Manager shut down.")

    async def execute(self, raw_text: str, **extra_params) -> AgentResponse:
        """
        Route a raw voice or text command to the correct agent.
        Returns the agent's response.
        """
        if not self._ready:
            return AgentResponse(
                command_id="mgr",
                success=False,
                message="Agent Manager not initialized. Call initialize() first.",
            )

        # Route to correct agent
        routing = normalize_command(raw_text)
        logger.info(f"Command routed to agent='{routing.agent}' confidence={routing.confidence:.2f}: '{raw_text}'")

        command = AgentCommand(
            intent=routing.intent,
            raw_text=raw_text,
            parameters={**routing.parameters, **extra_params},
            priority=CommandPriority.NORMAL,
            source="voice",
        )

        if routing.agent == "email" and self._email_agent:
            return await self._email_agent.submit_command(command)

        # Fallback: try email agent for anything unrecognized
        if self._email_agent:
            return await self._email_agent.submit_command(command)

        return AgentResponse(
            command_id=command.command_id,
            success=False,
            message=f"No agent available for command: '{raw_text}'",
            voice_text="I'm not sure which assistant should handle that.",
        )

    async def execute_email(self, intent: str, **params) -> AgentResponse:
        """Directly execute an email command with a known intent."""
        if not self._email_agent:
            return AgentResponse(command_id="direct", success=False, message="Email agent not available.")
        command = AgentCommand(intent=intent, parameters=params, source="direct")
        return await self._email_agent.submit_command(command)

    @property
    def email_agent(self) -> Optional[EmailAgent]:
        return self._email_agent

    def status(self) -> Dict[str, Any]:
        agents = AgentRegistry.get_all()
        return {
            agent_id: {
                "name": agent.name,
                "status": agent.status.value,
            }
            for agent_id, agent in agents.items()
        }
