# ==================================================
# Buddy OPIS – ADVANCED STEP
# TRUE STOP INTERRUPT (KEYBOARD BASED)
# Windows Safe | No Mic Crash
# ==================================================

import json
import pyttsx3
import speech_recognition as sr
import requests
import keyboard
from datetime import datetime

# ==================================================
# INSERT YOUR GROQ API KEY HERE
# ==================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ==================================================
# GLOBAL STOP FLAG
# ==================================================
STOP_SPEAKING = False

# ==================================================
# SPEAK (INTERRUPTIBLE)
# ==================================================
def speak(text):
    global STOP_SPEAKING
    print("Buddy:", text)

    engine = pyttsx3.init()
    engine.setProperty("rate", 165)

    for sentence in text.split(". "):
        if STOP_SPEAKING:
            engine.stop()
            STOP_SPEAKING = False
            print("[Speech stopped]")
            return
        engine.say(sentence)
        engine.runAndWait()

    engine.stop()

# ==================================================
# STOP KEY HANDLER
# ==================================================
def stop_key_handler(e):
    global STOP_SPEAKING
    STOP_SPEAKING = True

keyboard.on_press_key("s", stop_key_handler)

# ==================================================
# SPEECH TO TEXT (STABLE)
# ==================================================
recognizer = sr.Recognizer()
microphone = sr.Microphone()

with microphone as source:
    print("Calibrating microphone...")
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
# MAIN LOOP
# ==================================================
def main():
    brain = Brain()
    speak("Buddy is online. Press S anytime to stop my voice.")

    while True:
        query = listen()
        if not query:
            continue

        if "exit" in query or "shutdown" in query:
            speak("Goodbye.")
            break

        brain.log("user", query)
        print("Thinking...")

        answer = ask_ai(query)
        brain.log("ai", answer)

        # DISPLAY
        print("\nAI ANSWER:\n", answer, "\n")

        # SPEAK (STOP KEY WORKS HERE)
        speak(answer)

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    main()
