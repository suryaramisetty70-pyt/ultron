# ==================================================
# Buddy OPIS – FINAL STABLE VERSION (WINDOWS SAFE)
# Voice Input + Voice Output + Groq AI
# ==================================================

import json
import asyncio
import edge_tts
import pygame
import os
import speech_recognition as sr
import requests
from datetime import datetime

# ==================================================
# INSERT YOUR GROQ API KEY HERE
# ==================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ==================================================
# SPEAK (NEURAL VOICE - EDGE TTS)
# ==================================================
def speak(text):
    print("Buddy:", text)
    
    # Clean text to prevent edge-tts errors
    safe_text = text.replace('"', '').replace("'", "")
    
    # Choose a highly realistic voice (en-US-ChristopherNeural or en-US-AriaNeural)
    voice = "en-US-ChristopherNeural"
    
    async def generate_speech():
        communicate = edge_tts.Communicate(safe_text, voice)
        await communicate.save("response.mp3")
        
    # Generate MP3
    asyncio.run(generate_speech())
    
    # Play MP3 safely without locking
    pygame.mixer.init()
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
        
    pygame.mixer.quit()
    
    # Clean up the file
    try:
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")
    except Exception as e:
        pass

# ==================================================
# SPEECH TO TEXT (SINGLE MIC OWNER)
# ==================================================
recognizer = sr.Recognizer()
microphone = sr.Microphone()

def listen():
    with microphone as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=6)
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
    speak("Buddy is online. Ask me anything.")

    while True:
        query = listen()
        if not query:
            continue

        if "exit" in query or "shutdown" in query:
            speak("Goodbye.")
            break

        if "stop" in query:
            continue

        brain.log("user", query)
        print("Thinking...")

        answer = ask_ai(query)
        brain.log("ai", answer)

        # DISPLAY ANSWER
        print("\nAI ANSWER:\n", answer, "\n")

        # SPEAK ANSWER (ALWAYS WORKS NOW)
        speak(answer)

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    main()


