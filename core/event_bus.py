import asyncio
from collections import defaultdict

# ==========================================
# EVENT BUS
# ==========================================

class EventBus:

    def __init__(self):

        self.subscribers = defaultdict(list)

    # ======================================
    # SUBSCRIBE
    # ======================================

    def subscribe(

        self,

        event_name,

        callback
    ):

        self.subscribers[
            event_name
        ].append(callback)

    # ======================================
    # PUBLISH
    # ======================================

    async def publish(

        self,

        event_name,

        data=None
    ):

        if event_name not in self.subscribers:

            return

        tasks = []

        for callback in self.subscribers[
            event_name
        ]:

            tasks.append(

                callback(data)
            )

        await asyncio.gather(*tasks)