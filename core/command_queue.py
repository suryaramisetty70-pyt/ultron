import asyncio

# ==========================================
# COMMAND QUEUE
# ==========================================

class CommandQueue:

    def __init__(self):

        self.queue = asyncio.Queue()

    async def put(

        self,

        command
    ):

        await self.queue.put(command)

    async def get(self):

        return await self.queue.get()