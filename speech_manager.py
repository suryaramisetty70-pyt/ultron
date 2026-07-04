import pyttsx3
import queue
import threading
import time

class SpeechManager:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 175)
        self.engine.setProperty("volume", 1.0)

        self.speech_queue = queue.Queue()
        self.speaking = False

        # Start speaker loop thread ONCE
        self.worker = threading.Thread(target=self._speaker_loop, daemon=True)
        self.worker.start()

    def speak(self, text: str):
        if text and isinstance(text, str):
            self.speech_queue.put(text)

    def stop(self):
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        self.engine.stop()

    def _speaker_loop(self):
        while True:
            text = self.speech_queue.get()
            try:
                self.speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print("🔴 TTS Error:", e)
            finally:
                self.speaking = False
                time.sleep(0.1)
