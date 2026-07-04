# ==========================================================
# BUDDY v5.0 – OFFLINE VOSK + SMART AI ROUTING
# ==========================================================

import os
import queue
import json
import webbrowser
import pyttsx3
import requests
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from datetime import datetime
import time

# ==============================
# INSERT YOUR GROQ API KEY
# ==============================
GROQ_API_KEY = "PASTE_YOUR_GROQ_API_KEY_HERE"

# ==============================
# TEXT TO SPEECH
# ==============================
def speak(text):
    print("\nBuddy:", text)
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    engine.say(text)
    engine.runAndWait()
    engine.stop()
    time.sleep(0.5)

# ==============================
# LOAD VOSK MODEL (OFFLINE)
# ==============================
MODEL_PATH = "vosk-model-small-en-us-0.15"

if not os.path.exists(MODEL_PATH):
    print("Vosk model not found!")
    exit()

model = Model(MODEL_PATH)

# Grammar mode for better short word detection
grammar = json.dumps([
    "search and open",
    "search",
    "time",
    "date",
    "exit",
    "stop",
    "ams",
    "veltech",
    "[unk]"   # Allow unknown words
])

recognizer = KaldiRecognizer(model, 16000, grammar)

q = queue.Queue()

def callback(indata, frames, time_info, status):
    if status:
        print(status)
    q.put(bytes(indata))

# ==============================
# OFFLINE LISTEN FUNCTION
# ==============================
def listen():

    print("\nListening (Offline)...")

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype='int16',
        channels=1,
        callback=callback
    ):

        while True:
            data = q.get()

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    print("You:", text)
                    return text.lower()

# ==============================
# AI BRAIN (GROQ)
# ==============================
def ask_ai(question):

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Answer clearly and briefly like a smart assistant."},
            {"role": "user", "content": question}
        ]
    }

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        return r.json()["choices"][0]["message"]["content"]

    except:
        return "AI service is not available."

# ==============================
# WEBSITE HANDLER
# ==============================
def open_direct_website(name):

    name_clean = name.replace(" ", "")

    url = f"https://www.{name_clean}.com"
    webbrowser.open(url)

    return f"Opening {name}"

# ==============================
# WIKIPEDIA SEARCH
# ==============================
def open_wikipedia(topic):
    wiki_url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
    webbrowser.open(wiki_url)

# ==============================
# COMMAND ROUTER
# ==============================
def handle_command(cmd):

    cmd = cmd.strip()

    if "exit" in cmd or "stop" in cmd:
        return "exit"

    if cmd.startswith("search and open"):
        target = cmd.replace("search and open", "").strip()
        return open_direct_website(target)

    if cmd.startswith("search"):
        topic = cmd.replace("search", "").strip()
        open_wikipedia(topic)
        return ask_ai(topic)

    if "time" in cmd:
        return datetime.now().strftime("Current time is %I:%M %p")

    if "date" in cmd:
        return datetime.now().strftime("Today is %A, %d %B %Y")

    return ask_ai(cmd)

# ==============================
# MAIN LOOP
# ==============================
def main():

    speak("Offline Buddy version 5 point 0 is ready.")

    while True:

        command = listen()

        if not command:
            continue

        response = handle_command(command)

        if response == "exit":
            speak("Goodbye Surya.")
            break

        speak(response)

if __name__ == "__main__":
    main()

