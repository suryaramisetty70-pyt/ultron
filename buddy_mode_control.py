# ==================================================
# Buddy OPIS – MODE BASED VOICE CONTROL (STABLE)
# No keyboard hacks | No mic conflicts
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
# GLOBAL MODES
# ==================================================
VOICE_ENABLED = True
STOP_REQUESTED = False

# ==================================================
# SPEAK (SAFE)
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
    global VOICE_ENABLED, STOP_REQUESTED

    brain = Brain()
    speak("Buddy is online. You can talk to me.")

    while True:
        query = listen()
        if not query:
            continue

        # -------- CONTROL COMMANDS --------
        if "stop speaking" in query:
            STOP_REQUESTED = True
            print("[Speech stopped]")
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

        # -------- NORMAL QUESTION --------
        brain.log("user", query)
        print("Thinking...")

        answer = ask_ai(query)
        brain.log("ai", answer)

        # DISPLAY ALWAYS
        print("\nAI ANSWER:\n", answer, "\n")

        # SPEAK ONLY IF ENABLED
        speak(answer)

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    main()
