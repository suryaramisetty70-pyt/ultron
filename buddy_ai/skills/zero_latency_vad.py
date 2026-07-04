"""
Zero-Latency Conversational Engine (VAD)
Uses Silero-VAD (Deep Learning) to monitor the microphone in real-time.
Allows the user to interrupt Ultron mid-sentence, cutting off his speech instantly.
"""

import time
import torch
import sounddevice as sd
import numpy as np
import os
import signal
import psutil

# Load the lightweight Silero-VAD model via PyTorch Hub
# It will download a ~1MB cache on the first run, then work offline forever.
print("[VAD Boot] Loading Silero-VAD Neural Network...")
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False,
                              trust_repo=True)

def kill_process_and_children(pid):
    """Kills a process and all its child processes (e.g. edge-playback/mpv)"""
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except:
        pass

def listen_for_interruption(tts_pid: int = None):
    """
    Listens to the microphone continuously at 16kHz.
    If speech probability exceeds 0.75, it kills the currently running TTS process.
    """
    samplerate = 16000
    blocksize = 512  # 32ms audio chunks for absolute zero-latency
    
    print("\n[VAD Engine] Zero-Latency listening active. You can interrupt Ultron now.")
    
    interrupted = False
    
    def callback(indata, frames, time_info, status):
        nonlocal interrupted
        if status:
            pass
            
        # Convert numpy audio stream to PyTorch tensor
        audio_data = np.squeeze(indata)
        tensor = torch.from_numpy(audio_data).float()
        
        # Run inference through Silero-VAD
        with torch.no_grad():
            speech_prob = model(tensor, samplerate).item()
            
        if speech_prob > 0.8:
            print(f"[VAD Engine] HUMAN INTERRUPTION DETECTED (Confidence: {speech_prob:.2f})!")
            interrupted = True
            
            # Immediately cut off the TTS audio if it's playing
            if tts_pid:
                kill_process_and_children(tts_pid)
                
            raise sd.CallbackStop()

    try:
        # Open the microphone stream
        with sd.InputStream(samplerate=samplerate, blocksize=blocksize,
                            channels=1, dtype='float32', callback=callback):
            while not interrupted:
                sd.sleep(100)
    except sd.CallbackStop:
        return True # User successfully interrupted
    except Exception as e:
        print(f"[VAD Engine] Stream Error: {e}")
        return False
        
    return False
