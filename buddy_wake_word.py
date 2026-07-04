# ==================================================
# Buddy OPIS – WAKE WORD (FIXED & STABLE)
# Wake Word: "hey buddy"
# ==================================================

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
# SPEAK (RE-INIT EVERY TIME — WINDOWS SAFE)
# ==================================================
def speak(text):
    print("Buddy:", text)
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ==================================================
# SPEECH RECOGNIZER (SETUP ONCE)
# ==================================================
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Calibrate mic ONCE
with microphone as source:
    print("Calibrating microphone...")
    recognizer.adjust_for_ambient_noise(source, duration=1)

def listen(timeout=5):
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
        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Answer clearly."},
            {"role": "user", "content": question}
        ]
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=20
    )

    if response.status_code != 200:
        return "AI request failed."

    return response.json()["choices"][0]["message"]["content"]

# ==================================================
# MAIN LOOP — WAKE WORD SYSTEM
# ==================================================
def main():
    brain = Brain()
    speak("Buddy is sleeping. Say hey buddy to wake me.")

    while True:
        # 💤 Sleep mode
        heard = listen(timeout=3)
        if not heard:
            continue

        if "hey buddy" not in heard:
            continue

        # 👂 Active mode
        speak("Yes. I am listening.")
        question = listen(timeout=8)

        if not question:
            speak("I did not hear the question.")
            continue

        if "exit" in question or "shutdown" in question:
            speak("Goodbye.")
            break

        brain.log("user", question)
        print("Thinking...")

        answer = ask_ai(question)
        brain.log("ai", answer)

        # DISPLAY
        print("\nAI ANSWER:\n", answer, "\n")

        # SPEAK
        speak(answer)

        speak("Going back to sleep.")

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    main()
