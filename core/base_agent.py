from abc import ABC, abstractmethod

# ==========================================
# BASE AGENT
# ==========================================

class BaseAgent(ABC):

    def __init__(

        self,

        agent_id,

        event_bus,

        command_queue
    ):

        self.agent_id = agent_id

        self.event_bus = event_bus

        self.command_queue = command_queue

        self.intent_handlers = {}

    # ======================================
    # REGISTER INTENT
    # ======================================

    def register_intent(

        self,

        intent,

        handler
    ):

        self.intent_handlers[
            intent
        ] = handler

    # ======================================
    # START
    # ======================================

    async def start(self):

        await self.on_start()

    # ======================================
    # STOP
    # ======================================

    async def stop(self):

        await self.on_stop()

    # ======================================
    # ABSTRACTS
    # ======================================

    @abstractmethod
    async def on_start(self):

        pass

    @abstractmethod
    async def on_stop(self):

        pass

    @abstractmethod
    async def handle_command(

        self,

        command
    ):

        pass