"""
Local Wake-Word Engine
Runs a highly optimized, offline listening loop using Vosk.
Listens for the wake word 'Ultron' using minimal CPU resources.
"""
import os
import json
import queue
import sys
import threading
import sounddevice as sd

q = queue.Queue()

def _audio_callback(indata, frames, time, status):
    if status:
        pass
    q.put(bytes(indata))

def _run_wake_word():
    print("\n[Wake Word] Initializing offline auditory receptors...")
    try:
        from vosk import Model, KaldiRecognizer
        
        # Initialize Vosk Model (Download small English model if needed, or use default)
        model = Model(lang="en-us")
        # Optimization: Restrict vocabulary to exactly what we need to minimize CPU usage
        rec = KaldiRecognizer(model, 16000, '["ultron", "wake up", "[unk]"]')
        
        print("[Wake Word] Engine online. Say 'Ultron' to wake the system.")
        
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=_audio_callback):
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    text = res.get('text', '')
                    if 'ultron' in text.lower():
                        print("\n[Wake Word] Detected 'Ultron'. System Waking...")
                        # In full implementation, this triggers the main LLM loop
                        import pyttsx3
                        engine = pyttsx3.init()
                        engine.say("Yes, sir?")
                        engine.runAndWait()
                        
    except Exception as e:
        print(f"[Wake Word] Warning: Vosk model not found or audio error. {e}")
        print("Please download the 'vosk-model-small-en-us' and place it in the models directory.")

def start_wake_word_engine():
    """Starts the wake word engine in a background thread."""
    t = threading.Thread(target=_run_wake_word, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    _run_wake_word()
