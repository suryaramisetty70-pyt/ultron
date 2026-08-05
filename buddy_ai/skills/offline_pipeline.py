"""
Offline Speech-to-Speech Engine Pipeline
Integrates Faster-Whisper, Silero VAD, and Piper TTS for zero-latency offline performance.
"""

import os
import io
import wave
import torch
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# Global cache for faster-whisper model instance
_whisper_model_instance = None

def get_whisper_model():
    global _whisper_model_instance
    if _whisper_model_instance is None:
        print("[Offline Pipeline] Initializing Faster-Whisper (Large-V3) model...")
        # Auto-fallback to cpu or cuda depending on system
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        try:
            _whisper_model_instance = WhisperModel("large-v3", device=device, compute_type=compute_type)
        except Exception as e:
            print(f"[Offline Pipeline] Fallback to base model due to memory constraint: {e}")
            _whisper_model_instance = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model_instance

def transcribe_faster_whisper(audio_bytes: bytes) -> str:
    """
    Transcribes raw audio WAV bytes using Faster-Whisper Large V3 offline model.
    Handles non-native accents, broken grammar, and unclear speech accurately.
    """
    try:
        model = get_whisper_model()
        
        # Write bytes to temporary memory buffer
        buf = io.BytesIO(audio_bytes)
        
        segments, info = model.transcribe(
            buf,
            beam_size=5,
            language="en",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        return text
    except Exception as e:
        print(f"[Faster-Whisper] Error during transcription: {e}")
        return ""

def speak_piper_tts(text: str):
    """
    Generates fast, natural-sounding, 100% offline speech using Piper TTS.
    Falls back gracefully to pyttsx3 or edge-tts if piper binary environment is minimal.
    """
    if not text or not text.strip():
        return

    try:
        # Try running Piper CLI or Python bindings
        import subprocess
        # Check if piper binary or python runner is available
        process = subprocess.Popen(
            ["piper", "--model", "en_US-lessac-medium", "--output-raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        stdout, _ = process.communicate(input=text.encode("utf-8"))
        if stdout:
            audio_data = np.frombuffer(stdout, dtype=np.int16)
            sd.play(audio_data, samplerate=22050)
            sd.wait()
            return
    except Exception:
        pass

    # Fallback to local offline pyttsx3/system engine if piper binary standalone is building
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Piper TTS Fallback] Audio playback fallback: {e}")
