"""
Global Voice Dictation Engine
Press Ctrl+Alt+V anywhere in Windows to speak into your mic, and Ultron types it out.
"""
import keyboard
import pyautogui
import threading
import time

def _run_dictation():
    print("[Voice Dictation] Listening to microphone...")
    # In full implementation, this opens a PyAudio stream, feeds it to the local Vosk model, 
    # and returns the transcribed text.
    # We will simulate the transcription delay here.
    time.sleep(2)
    transcription = "This is a globally dictated sentence, transcribed locally and typed by Ultron."
    
    print(f"[Voice Dictation] Heard: '{transcription}'")
    print("[Voice Dictation] Typing...")
    
    # We release the hotkeys first to avoid getting stuck
    keyboard.release('ctrl')
    keyboard.release('alt')
    keyboard.release('v')
    
    pyautogui.write(transcription, interval=0.02)
    print("[Voice Dictation] Typing complete.")

def on_trigger():
    # Run dictation in a separate thread to not block the keyboard listener
    threading.Thread(target=_run_dictation, daemon=True).start()

def start_dictation_listener():
    print("\n[Voice Dictation] Global Listener Active. Press Ctrl+Alt+V anywhere to dictate text.")
    keyboard.add_hotkey('ctrl+alt+v', on_trigger)

if __name__ == "__main__":
    start_dictation_listener()
    keyboard.wait()
