# mic_calibration.py
"""Microphone Calibration Skill

Analyzes ambient room noise to establish the optimal energy threshold
for high-fidelity listening, reducing false activations in noisy spaces.
"""
import speech_recognition as sr
from buddy_ai.ultron_memory import update_user_preference

def calibrate_microphone(duration: float = 3.0) -> str:
    """Measure background room noise and update optimal energy threshold."""
    recognizer = sr.Recognizer()
    try:
        # Use speech_recognition's built-in ambient noise measurement
        with sr.Microphone() as source:
            print(f"[SYSTEM] Calibrating microphone. Please remain silent for {duration} seconds...")
            recognizer.adjust_for_ambient_noise(source, duration=duration)
            threshold = int(recognizer.energy_threshold)
            
            # Save the new threshold to user_profile.json preferences
            update_user_preference("mic_energy_threshold", threshold)
            
            return f"Microphone calibrated. Background noise floor evaluated. Sensitivity threshold set to {threshold}."
    except Exception as e:
        return f"Microphone calibration failed: {e}"
