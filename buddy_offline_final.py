# ======================================================
# BUDDY OFFLINE – AUTO MODEL DETECTION VERSION
# No hardcoded folder name
# ======================================================

import os
import json
import pyaudio
from vosk import Model, KaldiRecognizer
import pyttsx3
from datetime import datetime

# ==============================
# TEXT TO SPEECH
# ==============================
def speak(text):
    print("Buddy:", text)
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ==============================
# FIND VOSK MODEL AUTOMATICALLY
# ==============================
def find_vosk_model():
    current_dir = os.getcwd()

    for folder in os.listdir(current_dir):
        if "vosk" in folder.lower() and os.path.isdir(folder):
            return folder

    return None

model_path = find_vosk_model()

if not model_path:
    print("\nERROR: No Vosk model folder found!")
    print("Make sure the Vosk model folder is inside this directory:")
    print(os.getcwd())
    exit()

print("Using Vosk model folder:", model_path)

# ==============================
# LOAD MODEL
# ==============================
model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

# ==============================
# MICROPHONE SETUP
# ==============================
mic = pyaudio.PyAudio()

stream = mic.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=8000
)

stream.start_stream()

# ==============================
# COMMAND HANDLER
# ==============================
def handle_command(cmd):

    if "open calculator" in cmd:
        os.system("calc")
        return "Opening calculator"

    if "time" in cmd:
        return datetime.now().strftime("Current time is %I:%M %p")

    if "date" in cmd:
        return datetime.now().strftime("Today is %A, %d %B %Y")

    if "exit" in cmd:
        return "exit"

    return "Command not recognized"

# ==============================
# MAIN LOOP
# ==============================
print("Buddy Offline Mode Started")
speak("Buddy offline mode activated")

while True:
    try:
        data = stream.read(4000, exception_on_overflow=False)

        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            text = json.loads(result)["text"]

            if text:
                print("You:", text)
                response = handle_command(text)

                if response == "exit":
                    speak("Goodbye")
                    break

                speak(response)

    except Exception as e:
        print("Audio error:", e)

# ==============================
# CLEANUP
# ==============================
stream.stop_stream()
stream.close()
mic.terminate()







