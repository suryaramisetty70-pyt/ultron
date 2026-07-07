"""
Security Engine (Intruder Lock)
Uses DeepFace to verify the user's face. If it fails, locks the PC and emails the intruder's photo.
"""

import ctypes
import time
import os
from buddy_ai.skills.email_agent import send_email
from dotenv import load_dotenv

def activate_intruder_lock(baseline_image_path="baseline_face.jpg") -> str:
    """
    Scans the webcam. If the face doesn't match the baseline, locks the PC and emails a photo.
    """
    # Lazy import - only load heavy DeepFace+TensorFlow when this skill is actually triggered
    import cv2
    from deepface import DeepFace
    if not os.path.exists(baseline_image_path):
        return f"ERROR: Baseline image '{baseline_image_path}' not found. Run capture_baseline.py first."
        
    print("[Ultron Security] Scanning for intruders...")
    cap = cv2.VideoCapture(0)
    time.sleep(1) # Let camera warm up
    success, img = cap.read()
    cap.release()
    
    if not success:
        return "ERROR: Could not access webcam."
        
    temp_path = "current_scan.jpg"
    cv2.imwrite(temp_path, img)
    
    try:
        # Compare current face with the baseline
        print("[Ultron Security] Verifying biometrics...")
        result = DeepFace.verify(img1_path=temp_path, img2_path=baseline_image_path, enforce_detection=False)
        
        if result["verified"]:
            os.remove(temp_path)
            return "SUCCESS: Face verified. Welcome back, Boss."
        else:
            # Face does not match! Lock PC and email photo.
            print("[Ultron Security] INTRUDER DETECTED! Locking system...")
            
            # Lock Windows PC
            ctypes.windll.user32.LockWorkStation()
            
            # Email the photo
            load_dotenv()
            target_email = os.getenv("GMAIL_ADDRESS")
            if target_email and target_email != "your_actual_email@gmail.com":
                send_email(
                    to_address=target_email,
                    subject="SECURITY ALERT: Intruder Detected",
                    body="Ultron detected an unauthorized face at your terminal. System has been locked. See attached photo.",
                    attachment=temp_path
                )
            else:
                print("[Ultron Security] Could not send email because GMAIL_ADDRESS is not configured.")
            
            time.sleep(2)
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return "ALERT: Intruder detected. System locked and photo emailed."
            
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return f"SECURITY ENGINE ERROR: {str(e)}"
