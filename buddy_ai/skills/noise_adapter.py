# noise_adapter.py
"""Room-Noise Adapter Skill

Continuously samples microphone RMS level and dynamically adjusts
system output volume via pycaw when ambient noise exceeds a threshold.
"""
import threading
import numpy as np
import sounddevice as sd
import time

_running = False
_thread = None
_noise_threshold_db = 60  # dB above which volume is raised

def _rms_to_db(rms):
    """Convert RMS amplitude to approximate dB."""
    if rms < 1e-10:
        return 0
    return 20 * np.log10(rms)

def _set_system_volume(level: float):
    """Set system master volume (0.0 to 1.0) using pycaw."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level)), None)
    except Exception as e:
        print(f"[NoiseAdapter] Volume set failed: {e}")

def _monitor_loop():
    """Background loop: sample mic, adjust volume."""
    global _running
    base_volume = 0.5
    while _running:
        try:
            recording = sd.rec(int(0.5 * 16000), samplerate=16000, channels=1, dtype='float32')
            sd.wait()
            rms = np.sqrt(np.mean(recording ** 2))
            db = _rms_to_db(rms)

            if db > _noise_threshold_db:
                boost = min(1.0, base_volume + (db - _noise_threshold_db) * 0.01)
                _set_system_volume(boost)
            else:
                _set_system_volume(base_volume)

            time.sleep(2)  # Check every 2 seconds
        except Exception:
            time.sleep(5)

def start_noise_adapter(threshold_db: float = 60, base_vol: float = 0.5):
    """Start the background noise adapter."""
    global _running, _thread, _noise_threshold_db
    _noise_threshold_db = threshold_db
    _running = True
    _thread = threading.Thread(target=_monitor_loop, daemon=True)
    _thread.start()
    print("[NoiseAdapter] Started ambient noise monitoring.")

def stop_noise_adapter():
    """Stop the background noise adapter."""
    global _running
    _running = False
    print("[NoiseAdapter] Stopped.")
