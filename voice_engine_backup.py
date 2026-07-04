import os
import time
import tempfile
import asyncio

import pygame
import sounddevice as sd
import soundfile as sf
import numpy as np

from faster_whisper import WhisperModel
import edge_tts

from agent_manager import handle_command

# ==========================================
# SETTINGS
# ==========================================

SAMPLE_RATE = 16000

RECORD_SECONDS = 5

SILENCE_THRESHOLD = 0.002

# ==========================================
# FUZZY WAKE WORDS
# ==========================================

WAKE_WORDS = [

    "buddy",

    "buddy,",

    "but the",

    "by d",

    "but be",

    "body",

    "badi"
]

# ==========================================
# AUDIO
# ==========================================

pygame.mixer.init()

# ==========================================
# WHISPER MODEL
# ==========================================

print("\nLoading Buddy Voice Engine...\n")

model = WhisperModel(

    "base",

    device="cpu",

    compute_type="int8"
)

print("\nBuddy Voice Engine Ready!\n")

# ==========================================
# SPEAK
# ==========================================

def speak(text):

    try:

        print(f"\nBuddy: {text}\n")

        temp_file = tempfile.NamedTemporaryFile(

            delete=False,

            suffix=".mp3"
        )

        temp_path = temp_file.name

        temp_file.close()

        async def generate():

            communicate = edge_tts.Communicate(

                text=text,

                voice="en-US-GuyNeural",

                rate="+10%"
            )

            await communicate.save(
                temp_path
            )

        asyncio.run(generate())

        pygame.mixer.music.load(
            temp_path
        )

        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():

            time.sleep(0.1)

        pygame.mixer.music.unload()

        os.remove(temp_path)

    except Exception as e:

        print(f"\nVoice Error: {e}")

# ==========================================
# LISTEN
# ==========================================

def listen():

    try:

        print("\nListening...\n")

        audio = sd.rec(

            int(RECORD_SECONDS * SAMPLE_RATE),

            samplerate=SAMPLE_RATE,

            channels=1,

            dtype='float32'
        )

        sd.wait()

        volume = np.abs(audio).mean()

        print(f"\nVolume Level: {volume}\n")

        # ==================================
        # SILENCE FILTER
        # ==================================

        if volume < SILENCE_THRESHOLD:

            return ""

        sf.write(

            "input.wav",

            audio,

            SAMPLE_RATE
        )

        print("\nTranscribing...\n")

        segments, _ = model.transcribe(

            "input.wav",

            beam_size=5,

            language="en"
        )

        text = ""

        for segment in segments:

            text += segment.text

        text = text.strip().lower()

        print(f"\nYou Said: {text}\n")

        return text

    except Exception as e:

        print(f"\nListening Error: {e}")

        return ""

# ==========================================
# MAIN LOOP
# ==========================================

if __name__ == "__main__":

    speak(
        "Buddy professional system activated."
    )

    while True:

        command = listen()

        if not command:
            continue

        # ==================================
        # FUZZY WAKE WORD DETECTION
        # ==================================

        wake_detected = False

        for wake in WAKE_WORDS:

            if wake in command:

                command = command.replace(
                    wake,
                    ""
                ).strip()

                wake_detected = True

                break

        if not wake_detected:

            print("\nWake word not detected.\n")

            continue

        # ==================================
        # STOP SPEAKING
        # ==================================

        if (
            "stop" in command
        ):

            pygame.mixer.music.stop()

            continue

        # ==================================
        # HANDLE COMMAND
        # ==================================

        response = handle_command(
            command
        )

        # ==================================
        # EXIT
        # ==================================

        if response == "EXIT":

            speak("Goodbye sir.")

            break

        # ==================================
        # SPEAK RESPONSE
        # ==================================

        speak(response)