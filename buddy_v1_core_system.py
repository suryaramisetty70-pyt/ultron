# ==================================================
# Buddy v1.1 – SUPER CLEAN FINAL CORE
# Voice + AI + Open Apps + Close Apps + Any Website
# ==================================================

import os
import webbrowser
import json
import pyttsx3
import speech_recognition as sr
import requests
from datetime import datetime

# ==================================================
# INSERT YOUR GROQ API KEY HERE
# ==================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ==================================================
# GLOBAL MODES
# ==================================================
VOICE_ENABLED = True
STOP_REQUESTED = False

# ==================================================
# SPEAK (WINDOWS SAFE)
# ==================================================
def speak(text):
    global STOP_REQUESTED
    if not VOICE_ENABLED:
        return

    print("Buddy:", text)
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)

    for sentence in text.split(". "):
        if STOP_REQUESTED:
            engine.stop()
            STOP_REQUESTED = False
            return
        engine.say(sentence)
        engine.runAndWait()

    engine.stop()

# ==================================================
# SPEECH TO TEXT
# ==================================================
recognizer = sr.Recognizer()
microphone = sr.Microphone()

with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)

def listen(timeout=6):
    with microphone as source:
        try:
            audio = recognizer.listen(source, timeout=timeout)
        except sr.WaitTimeoutError:
            return ""

    try:
        text = recognizer.recognize_google(audio)
        print("You:", text)
        return text.lower()
    except:
        return ""

# ==================================================
# MEMORY
# ==================================================
class Brain:
    def __init__(self, file="brain.json"):
        try:
            with open(file, "r") as f:
                self.data = json.load(f)
        except:
            self.data = []
        self.file = file

    def log(self, role, content):
        self.data.append({
            "time": datetime.now().isoformat(),
            "role": role,
            "content": content
        })
        with open(self.file, "w") as f:
            json.dump(self.data, f, indent=4)

# ==================================================
# GROQ AI
# ==================================================
def ask_ai(question):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=20
    )

    if r.status_code != 200:
        return "AI request failed."

    return r.json()["choices"][0]["message"]["content"]

# ==================================================
# OPEN APP
# ==================================================
def open_app(command):
    apps = {
        "calculator": "calc",
        "settings": "ms-settings:",
        "file explorer": "explorer",
        "recycle bin": "explorer shell:RecycleBinFolder",
        "powerpoint": "powerpnt",
        "vs code": "code",
        "python": "python",
        "tux paint": "tuxpaint",
        "dell optimizer": "delloptimizer"
    }

    for name, cmd in apps.items():
        if f"open {name}" in command:
            os.system(cmd)
            return f"Opened {name}"

    return None

# ==================================================
# CLOSE APP (SAFE)
# ==================================================
def close_app(command):
    processes = {
        "calculator": "Calculator.exe",
        "chrome": "chrome.exe",
        "browser": "chrome.exe",
        "powerpoint": "POWERPNT.EXE",
        "vs code": "Code.exe",
        "python": "python.exe"
    }

    for name, proc in processes.items():
        if f"close {name}" in command:
            os.system(f"taskkill /f /im {proc}")
            return f"Closed {name}"

    return None

# ==================================================
# WEB HANDLER
# ==================================================
def handle_web(command):
    # ANY WEBSITE
    if "open website" in command:
        site = command.replace("open website", "").strip()
        if not site.startswith("http"):
            site = "https://" + site
        webbrowser.open(site)
        return f"Opening website {site}"

    # WIKIPEDIA
    if "wikipedia" in command:
        query = command.replace("search wikipedia for", "").replace("open wikipedia", "").strip()
        url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
        webbrowser.open(url)
        return f"Searching Wikipedia for {query}"

    # WEB SEARCH
    if "search web for" in command:
        query = command.replace("search web for", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Searching web for {query}"

    return None

# ==================================================
# MAIN LOOP
# ==================================================
def main():
    global VOICE_ENABLED, STOP_REQUESTED
    brain = Brain()
    speak("Buddy version one point one is ready.")

    while True:
        query = listen()
        if not query:
            continue

        # CONTROL
        if "stop speaking" in query:
            STOP_REQUESTED = True
            continue

        if "mute voice" in query:
            VOICE_ENABLED = False
            print("[Voice muted]")
            continue

        if "resume voice" in query:
            VOICE_ENABLED = True
            speak("Voice resumed.")
            continue

        if "exit" in query or "shutdown" in query:
            speak("Goodbye.")
            break

        # OPEN APP
        result = open_app(query)
        if result:
            speak(result)
            continue

        # CLOSE APP
        result = close_app(query)
        if result:
            speak(result)
            continue

        # WEB
        result = handle_web(query)
        if result:
            speak(result)
            continue

        # AI
        brain.log("user", query)
        answer = ask_ai(query)
        brain.log("ai", answer)

        print("\nAI ANSWER:\n", answer, "\n")
        speak(answer)

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    main()

