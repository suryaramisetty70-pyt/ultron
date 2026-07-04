import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import pyttsx3
import time

from command_normalizer import CommandNormalizer
from agent_manager import handle_command


# ==========================================
# LOAD WHISPER MODEL
# ==========================================

model = WhisperModel(
    "small",
    compute_type="int8"
)

# ==========================================
# TTS ENGINE
# ==========================================

engine = pyttsx3.init()

engine.setProperty("rate", 170)

# ==========================================
# NORMALIZER
# ==========================================

normalizer = CommandNormalizer(
    fuzzy_threshold=70
)

# ==========================================
# SPEAK
# ==========================================

def speak(text):

    print(f"\nBuddy: {text}")

    engine.say(text)

    engine.runAndWait()

# ==========================================
# RECORD AUDIO
# ==========================================

def record_audio():

    duration = 4
    sample_rate = 16000

    print("\nListening...\n")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    audio = np.squeeze(audio)

    volume = np.linalg.norm(audio)

    print(f"\nVolume Level: {volume}\n")

    if volume < 0.03:

        print("\nToo silent.\n")

        return None

    return audio

# ==========================================
# TRANSCRIBE
# ==========================================

def transcribe(audio):

    print("\nTranscribing...\n")

    segments, info = model.transcribe(

        audio,

        language="en",

        vad_filter=True,

        beam_size=5
    )

    text = ""

    for segment in segments:

        text += segment.text + " "

    return text.strip().lower()

# ==========================================
# PROCESS COMMAND
# ==========================================

def process_command(raw_text):

    if not raw_text:
        return

    print(f"\nYou Said: {raw_text}\n")

    result = normalizer.normalize(raw_text)

    print("\n[Normalizer Result]")

    print(result)

    if result["intent"] is None:

        speak("Command not understood.")

        return

    cleaned_command = result["cleaned"]

    response = handle_command(cleaned_command)

    if response == "exit":

        speak("Goodbye sir.")

        exit()

    speak(response)

# ==========================================
# MAIN
# ==========================================

print("\nLoading Buddy Voice Engine...\n")

time.sleep(2)

print("\nBuddy Voice Engine Ready!\n")

speak("Buddy professional system activated.")

while True:

    try:

        audio = record_audio()

        if audio is None:
            continue

        text = transcribe(audio)

        process_command(text)

    except KeyboardInterrupt:

        print("\nExiting Buddy...\n")

        break

    except Exception as e:

        print(f"\nERROR: {e}\n")