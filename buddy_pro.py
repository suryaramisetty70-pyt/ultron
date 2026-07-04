
import webbrowser
import pyttsx3
import speech_recognition as sr
import threading
import time

from groq import Groq
from coding_agent import run_coding_agent
from ui_server import run_server, set_state


# =========================
# CONFIG
# =========================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

AUTH_KEYWORD = "jarvis"
authenticated = False

client = Groq(api_key=GROQ_API_KEY)

stop_speaking = False


# =========================
# SPEAK (WITH STOP)
# =========================

def speak(text):

    global stop_speaking

    try:
        print("\nBuddy:", text)

        set_state("Speaking")

        engine = pyttsx3.init()
        engine.setProperty("rate", 165)

        stop_speaking = False

        for line in text.split("."):
            if stop_speaking:
                break

            engine.say(line)
            engine.runAndWait()

        engine.stop()

        set_state("Idle")

    except Exception as e:
        print("Voice Error:", e)


# =========================
# LISTEN
# =========================

def listen():

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        recognizer.adjust_for_ambient_noise(source, duration=1)

        print("\nListening...")
        set_state("Listening")

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=6)

            text = recognizer.recognize_google(audio)

            print("You:", text)

            set_state("Idle")

            return text.lower()

        except:
            set_state("Idle")
            return ""


# =========================
# AI
# =========================

def ask_ai(prompt):

    try:
        set_state("Thinking")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt}
            ]
        )

        set_state("Idle")

        return response.choices[0].message.content

    except Exception as e:
        print("AI Error:", e)
        set_state("Idle")
        return "Error"


# =========================
# STOP LISTENER THREAD
# =========================

def stop_listener():

    global stop_speaking

    while True:
        command = listen()

        if "stop" in command:
            print("Stopping speech...")
            stop_speaking = True


# =========================
# MAIN
# =========================

def main():

    global authenticated

    speak("Buddy is ready")

    while True:

        command = listen()

        if not command:
            continue

        # AUTH
        if not authenticated:
            if AUTH_KEYWORD in command:
                authenticated = True
                speak("Authentication successful")
            else:
                speak("Say jarvis to activate")
            continue

        # EXIT
        if "exit" in command:
            speak("Goodbye")
            break

        # STOP COMMAND
        if "stop" in command:
            global stop_speaking
            stop_speaking = True
            continue

        # CODING
        if "code" in command or "python" in command:
            speak("Starting coding agent")
            result = run_coding_agent(command)
            speak(result)

        # OPEN
        elif "youtube" in command:
            webbrowser.open("https://youtube.com")
            speak("Opening YouTube")

        elif "chrome" in command:
            webbrowser.open("https://google.com")
            speak("Opening Chrome")

        # NORMAL AI
        else:
            reply = ask_ai(command)
            speak(reply)


# =========================
# START
# =========================

if __name__ == "__main__":

    # START SERVER
    threading.Thread(target=run_server, daemon=True).start()

    # START STOP LISTENER
    threading.Thread(target=stop_listener, daemon=True).start()

    time.sleep(1)

    main()

