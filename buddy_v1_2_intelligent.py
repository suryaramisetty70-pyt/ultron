# ==================================================
# Buddy v1.2 – INTELLIGENT SEARCH & FIXED CLOSE
# AI + Wikipedia + Open Any Website + Proper Close
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
# MODES
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
            {"role": "system", "content": "Answer clearly and simply."},
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
# CLOSE APP (FIXED)
# ==================================================
def close_app(command):
    processes = {
        "calculator": "Calculator.exe",
        "chrome": "chrome.exe",
        "browser": "chrome.exe",
        "vs code": "Code.exe",
        "powerpoint": "POWERPNT.EXE",
        "python": "python.exe"
    }

    for name, exe in processes.items():
        if f"close {name}" in command:
            os.system(f'taskkill /f /im {exe} >nul 2>&1')
            return f"Closed {name}"

    return None

# ==================================================
# INTELLIGENT SEARCH & OPEN
# ==================================================
def intelligent_search(command):
    # SEARCH AND OPEN → WEBSITE
    if "search and open" in command:
        target = command.replace("search and open", "").strip()
        url = f"https://www.{target.replace(' ', '')}.com"
        webbrowser.open(url)
        return f"Opening website {target}"

    # SEARCH → WIKIPEDIA
    if "search" in command:
        topic = command.replace("search about", "").replace("search", "").strip()
        url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
        webbrowser.open(url)
        return f"Searching Wikipedia for {topic}"

    return None

# ==================================================
# MAIN LOOP
# ==================================================
def main():
    global VOICE_ENABLED, STOP_REQUESTED
    brain = Brain()
    speak("Buddy version one point two is ready.")

    while True:
        query = listen()
        if not query:
            continue

        # CONTROLS
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

        # CLOSE APP
        result = close_app(query)
        if result:
            speak(result)
            continue

        # SEARCH LOGIC
        result = intelligent_search(query)
        if result:
            speak(result)
            continue

        # NORMAL AI QUESTION
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
