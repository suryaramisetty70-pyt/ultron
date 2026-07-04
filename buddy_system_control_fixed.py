# ==========================================================
# BUDDY v4.1 – STABLE LISTENING + SMART AI ROUTING
# ==========================================================

import webbrowser
import pyttsx3
import speech_recognition as sr
import requests
from datetime import datetime
import time

# ==============================
# INSERT YOUR GROQ API KEY HERE
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
    time.sleep(0.8)   # Prevent mic catching its own voice


# ==============================
# STABLE LISTENER (NO CUTTING)
# ==============================
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.3
recognizer.non_speaking_duration = 0.8
recognizer.phrase_threshold = 0.1

mic = sr.Microphone()

def listen():

    for attempt in range(2):

        with mic as source:
            print("\nCalibrating...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            print("Listening clearly...")
            try:
                audio = recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=20
                )
            except sr.WaitTimeoutError:
                return ""

        try:
            result = recognizer.recognize_google(
                audio,
                language="en-IN",
                show_all=True
            )

            if result and "alternative" in result:
                text = result["alternative"][0]["transcript"]
                print("You:", text)
                return text.lower()

        except sr.UnknownValueError:
            print("Didn't catch that. Retrying...")
            continue
        except sr.RequestError:
            print("Network error.")
            return ""

    return ""


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

        response = r.json()
        return response["choices"][0]["message"]["content"]

    except:
        return "AI service is not available."


# ==============================
# WEBSITE HANDLER
# ==============================
def open_direct_website(name):

    name_clean = name.replace(" ", "")

    domains = [
        f"https://www.{name_clean}.com",
        f"https://{name_clean}.com",
        f"https://www.{name_clean}.in",
        f"https://{name_clean}.in",
        f"https://www.{name_clean}.org",
        f"https://{name_clean}.org"
    ]

    for url in domains:
        webbrowser.open(url)
        return f"Opening {name}"

    search_url = f"https://www.google.com/search?q={name}"
    webbrowser.open(search_url)
    return f"Searching {name} on Google"


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

    speak("Buddy version 4 point 1 is ready.")

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
