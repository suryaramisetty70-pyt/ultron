# voice_interruption.py
"""Voice Interruption Skill

Stops the AI's speech output mid‑sentence when the user starts speaking.
Implemented with Silero VAD to detect human speech on the microphone
while Edge‑TTS is playing audio.
"""
import threading
import queue
import sounddevice as sd
import numpy as np
import edge_tts
from silero_vad import VAD

# Global control objects
_stop_requested = threading.Event()
_audio_queue = queue.Queue()

def _audio_callback(indata, frames, time, status):
    """Callback for sounddevice input stream – pushes audio to queue."""
    if status:
        print(f"[VoiceInterruption] Input status: {status}")
    _audio_queue.put(indata.copy())

def _monitor_vad():
    """Runs VAD continuously; when speech is detected, signal stop."""
    vad = VAD()
    while not _stop_requested.is_set():
        try:
            block = _audio_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        # mono conversion and float32 to int16
        audio = (block[:, 0] * 32767).astype(np.int16)
        if vad(audio):
            # Detected speech – request stop of TTS playback
            print("[VoiceInterruption] User speech detected – stopping TTS")
            _stop_requested.set()
            break

def start_interruption_monitor():
    """Starts microphone stream and VAD monitor in background threads.
    Call this before any TTS playback.
    """
    global _stop_requested
    _stop_requested.clear()
    stream = sd.InputStream(callback=_audio_callback, channels=1, samplerate=16000)
    stream.start()
    threading.Thread(target=_monitor_vad, daemon=True).start()
    return stream

def stop_interruption_monitor(stream):
    """Stops the microphone stream and resets the event."""
    stream.stop()
    _stop_requested.set()

# Example helper to wrap Edge‑TTS playback with interruption support
async def speak_with_interruption(text: str, voice: str = "en-US-AriaNeural"):
    """Plays TTS while listening for interruption.
    Returns when playback finishes or user speech stops it.
    """
    import asyncio
    stream = start_interruption_monitor()
    communicate = edge_tts.Communicate(text, voice)
    try:
        async for chunk in communicate.stream():
            if _stop_requested.is_set():
                break
            # Placeholder for actual audio playback of chunk
            await asyncio.sleep(0)
    finally:
        stop_interruption_monitor(stream)
        _stop_requested.clear()
