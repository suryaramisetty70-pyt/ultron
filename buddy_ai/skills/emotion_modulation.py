# emotion_modulation.py
"""Emotion Modulation Skill

Wraps Edge‑TTS to adjust pitch and rate based on a simple emotion enum.
Supports: neutral, happy, sad, angry, excited.
Uses PyDub for optional post‑processing.
"""
import edge_tts
from enum import Enum
import asyncio
import os
import pygame

class Emotion(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"

# Mapping from emotion to TTS parameters
EMOTION_PARAMS = {
    Emotion.NEUTRAL: {"rate": "+0%", "pitch": "+0Hz"},
    Emotion.HAPPY: {"rate": "+10%", "pitch": "+5Hz"},
    Emotion.SAD: {"rate": "-10%", "pitch": "-5Hz"},
    Emotion.ANGRY: {"rate": "+5%", "pitch": "+10Hz"},
    Emotion.EXCITED: {"rate": "+15%", "pitch": "+10Hz"},
}

async def _generate_speech(text: str, emotion: Emotion, voice: str = "en-US-ChristopherNeural") -> str:
    params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS[Emotion.NEUTRAL])
    communicate = edge_tts.Communicate(text, voice, rate=params["rate"], pitch=params["pitch"])
    out_path = "emotion_output.mp3"
    await communicate.save(out_path)
    return out_path

def speak_with_emotion(text: str, emotion: Emotion = Emotion.NEUTRAL):
    """Synchronously generate speech with the requested emotion and play it.
    Mirrors the original `speak` function but adds emotion control.
    """
    loop = asyncio.new_event_loop()
    mp3_path = loop.run_until_complete(_generate_speech(text, emotion))
    pygame.mixer.init()
    pygame.mixer.music.load(mp3_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    if os.path.exists(mp3_path):
        os.remove(mp3_path)
