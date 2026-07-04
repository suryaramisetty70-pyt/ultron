import threading
import queue

# ==========================================
# BACKGROUND LISTENER
# ==========================================

class BackgroundListener:

    def __init__(

        self,

        listen_function
    ):

        self.listen_function = (
            listen_function
        )

        self.command_queue = queue.Queue()

        self.running = False

    # ======================================
    # LISTEN LOOP
    # ======================================

    def _listen_loop(self):

        while self.running:

            command = self.listen_function()

            if command:

                self.command_queue.put(
                    command
                )

    # ======================================
    # START
    # ======================================

    def start(self):

        self.running = True

        listener_thread = threading.Thread(

            target=self._listen_loop,

            daemon=True
        )

        listener_thread.start()

    # ======================================
    # STOP
    # ======================================

    def stop(self):

        self.running = False

    # ======================================
    # GET COMMAND
    # ======================================

    def get_command(self):

        if not self.command_queue.empty():

            return self.command_queue.get()

        return None