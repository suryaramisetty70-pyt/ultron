"""
Biometric AI Engine (Heart-Rate Shield)
Uses Remote Photoplethysmography (rPPG) to calculate heart rate from the webcam.
Tracks micro-color changes in the face caused by blood flow.
"""

import cv2
import numpy as np
import time

def calculate_heart_rate(duration: int = 10) -> str:
    """
    Calculates the user's heart rate (BPM) by analyzing the webcam feed for a set duration.
    """
    print(f"\n[Ultron Biometrics] Activating PPG Scanner for {duration} seconds...")
    print("[Ultron Biometrics] Please look directly at the camera and remain still.")
    
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    green_signals = []
    
    start_time = time.time()
    
    while (time.time() - start_time) < duration:
        ret, frame = cap.read()
        if not ret: 
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            # Target the forehead (most stable skin area for PPG)
            fh_x = x + int(w * 0.25)
            fh_y = y + int(h * 0.1)
            fh_w = int(w * 0.5)
            fh_h = int(h * 0.2)
            
            forehead = frame[fh_y:fh_y+fh_h, fh_x:fh_x+fh_w]
            
            # The green channel absorbs hemoglobin light the best
            if forehead.size > 0:
                avg_green = np.mean(forehead[:, :, 1])
                green_signals.append(avg_green)
                
                # Draw visual feedback for the user
                cv2.rectangle(frame, (fh_x, fh_y), (fh_x+fh_w, fh_y+fh_h), (0, 255, 0), 2)
            break
            
        cv2.putText(frame, "BIOMETRIC SCAN IN PROGRESS...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Ultron Biometrics", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    
    if len(green_signals) < 30:
        return "ERROR: Could not get a stable facial reading. Scan aborted."
        
    # Perform Fast Fourier Transform (FFT) to extract the heart rate frequency
    green_signals = np.array(green_signals)
    green_signals = green_signals - np.mean(green_signals) # Detrend
    
    fps = len(green_signals) / duration
    fft_data = np.abs(np.fft.rfft(green_signals))
    freqs = np.fft.rfftfreq(len(green_signals), 1.0/fps)
    
    # Human heart rate range (40 BPM - 180 BPM) => (0.67 Hz - 3.0 Hz)
    valid_idx = np.where((freqs >= 0.67) & (freqs <= 3.0))[0]
    
    if len(valid_idx) == 0:
         return "ERROR: Biological signal was too noisy."
         
    best_freq_idx = valid_idx[np.argmax(fft_data[valid_idx])]
    heart_rate = freqs[best_freq_idx] * 60.0
    bpm = int(heart_rate)
    
    print(f"[Ultron Biometrics] Scan complete. Reading: {bpm} BPM")
    
    if bpm > 100:
        return f"WARNING: Your heart rate is dangerously elevated at {bpm} BPM. I am activating Zen Mode. Muting notifications and playing ambient audio."
    else:
        return f"Vitals are stable. Your heart rate is {bpm} BPM."
