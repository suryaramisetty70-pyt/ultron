import cv2
import time

def capture_baseline():
    print("Ultron Security Registration")
    print("Please look directly into the camera...")
    
    cap = cv2.VideoCapture(0)
    time.sleep(2) # Warm up
    success, img = cap.read()
    cap.release()
    
    if success:
        cv2.imwrite("baseline_face.jpg", img)
        print("SUCCESS: baseline_face.jpg saved. Ultron can now recognize you.")
    else:
        print("ERROR: Could not access webcam.")

if __name__ == "__main__":
    capture_baseline()
