# ==================================================
# Buddy OPIS – AI Conversational Brain
# FINAL CLEAN VERSION (GUARANTEED)
# Voice Input + Voice Output + Groq AI
# ==================================================

import os
import json
import pyttsx3
import speech_recognition as sr
import requests
from datetime import datetime

# ==================================================
# 🔴 PASTE YOUR GROQ API KEY HERE
# ==================================================
GROQ_API_KEY = "PASTE_YOUR_GROQ_API_KEY_HERE"
# Example:
# GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxxx"

# ==================================================
# SPEAK FUNCTION
# ==================================================
def speak(text):
    print("Buddy:", text)
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ==================================================
# LISTEN FUNCTION
# ==================================================
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=6)
        except sr.WaitTimeoutError:
            return ""

    try:
        text = r.recognize_google(audio)
        print("You:", text)
        return text.lower()
    except:
        return ""

# ==================================================
# MEMORY BRAIN
# ==================================================
class Brain:
    def __init__(self, file="brain.json"):
        self.file = file
        self.data = []
        if os.path.exists(file):
            try:
                with open(file, "r") as f:
                    self.data = json.load(f)
            except:
                self.data = []

    def log(self, role, content):
        self.data.append({
            "time": datetime.now().isoformat(),
            "role": role,
            "content": content
        })
        with open(self.file, "w") as f:
            json.dump(self.data, f, indent=4)

# ==================================================
# GROQ AI FUNCTION
# ==================================================
def ask_ai(question):
    if not GROQ_API_KEY:
        return "Groq API key is not set. Please set GROQ_API_KEY environment variable."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Answer clearly and simply."},
            {"role": "user", "content": question}
        ]
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )

        if response.status_code != 200:
            return f"Groq API error: {response.status_code}"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Request failed: {e}"

# ==================================================
# MAIN PROGRAM
# ==================================================
def main():
    brain = Brain()
    speak("Buddy is now online. Ask me anything.")

    while True:
        question = listen()
        if not question:
            continue

        if "exit" in question or "shutdown" in question:
            speak("Goodbye.")
            break

        if "stop" in question:
            continue

        brain.log("user", question)

        print("Thinking...")
        answer = ask_ai(question)

        print("AI:", answer)
        brain.log("ai", answer)

        speak(answer)

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    main()



















