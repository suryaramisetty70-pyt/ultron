# buddy_ai/base_agent.py
# BaseAgent - Core abstract class for all Buddy AI agents
# All agents in the ecosystem extend this class

from __future__ import annotations
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class CommandPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class AgentCommand:
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    intent: str = ""
    raw_text: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: CommandPriority = CommandPriority.NORMAL
    source: str = "user"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reply_to: Optional[str] = None


@dataclass
class AgentResponse:
    command_id: str
    success: bool
    message: str
    data: Any = None
    voice_text: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EventBus:
    """Simple pub/sub event bus for inter-agent communication."""
    _instance: Optional["EventBus"] = None
    _listeners: Dict[str, List[Callable]] = {}

    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event: str, callback: Callable) -> None:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable) -> None:
        if event in self._listeners:
            self._listeners[event] = [c for c in self._listeners[event] if c != callback]

    async def publish(self, event: str, data: Any = None) -> None:
        if event in self._listeners:
            for callback in self._listeners[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logging.error(f"EventBus error on '{event}': {e}")


class CommandQueue:
    """Priority-based async command queue."""

    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

    async def push(self, command: AgentCommand) -> None:
        priority_val = -command.priority.value
        await self._queue.put((priority_val, command.timestamp.timestamp(), command))

    async def pop(self) -> AgentCommand:
        _, _, command = await self._queue.get()
        return command

    def empty(self) -> bool:
        return self._queue.empty()


class AgentRegistry:
    """Central registry for all active agents."""
    _agents: Dict[str, "BaseAgent"] = {}

    @classmethod
    def register(cls, agent: "BaseAgent") -> None:
        cls._agents[agent.agent_id] = agent

    @classmethod
    def unregister(cls, agent_id: str) -> None:
        cls._agents.pop(agent_id, None)

    @classmethod
    def get(cls, agent_id: str) -> Optional["BaseAgent"]:
        return cls._agents.get(agent_id)

    @classmethod
    def get_all(cls) -> Dict[str, "BaseAgent"]:
        return dict(cls._agents)


class BaseAgent(ABC):
    """Abstract base class for all Buddy AI agents."""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"buddy.{agent_id}")
        self.event_bus = EventBus.get_instance()
        self.command_queue = CommandQueue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        AgentRegistry.register(self)

    @abstractmethod
    async def handle_command(self, command: AgentCommand) -> AgentResponse:
        """Process a command and return a response."""
        ...

    async def start(self) -> None:
        self._running = True
        self.status = AgentStatus.IDLE
        self._task = asyncio.create_task(self._run_loop())
        self.logger.info(f"{self.name} started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        self.status = AgentStatus.OFFLINE
        AgentRegistry.unregister(self.agent_id)
        self.logger.info(f"{self.name} stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                command = await asyncio.wait_for(self.command_queue.pop(), timeout=1.0)
                self.status = AgentStatus.BUSY
                response = await self.handle_command(command)
                await self.event_bus.publish(f"response.{command.command_id}", response)
                self.status = AgentStatus.IDLE
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in run loop: {e}", exc_info=True)
                self.status = AgentStatus.ERROR
                await asyncio.sleep(1)
                self.status = AgentStatus.IDLE

    async def submit_command(self, command: AgentCommand) -> AgentResponse:
        """Submit a command and wait for response."""
        future: asyncio.Future = asyncio.get_event_loop().create_future()

        async def on_response(response: AgentResponse):
            if not future.done():
                future.set_result(response)

        self.event_bus.subscribe(f"response.{command.command_id}", on_response)
        await self.command_queue.push(command)
        try:
            return await asyncio.wait_for(future, timeout=60.0)
        except asyncio.TimeoutError:
            return AgentResponse(
                command_id=command.command_id,
                success=False,
                message="Command timed out",
                error="timeout"
            )
        finally:
            self.event_bus.unsubscribe(f"response.{command.command_id}", on_response)
