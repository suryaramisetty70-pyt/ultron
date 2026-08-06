import cv2
import pyautogui
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import multiprocessing
import time
import math
import os
import urllib.request
import ctypes

class UltronVision(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.daemon = True
        
    def calculate_distance(self, p1, p2):
        return math.hypot(p2.x - p1.x, p2.y - p1.y)

    def run(self):
        # We initialize everything inside the run method for multiprocessing safety
        model_path = "hand_landmarker.task"
        if not os.path.exists(model_path):
            print("[Ultron Vision] Downloading Hand Tracking Model...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            urllib.request.urlretrieve(url, model_path)
            print("[Ultron Vision] Download Complete.")
        
        # Audio Volume Setup (PyCaw)
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            from ctypes import cast, POINTER
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            volRange = self.volume.GetVolumeRange()
            self.minVol = volRange[0]
            self.maxVol = volRange[1]
        except Exception as e:
            self.volume = None

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        detector = vision.HandLandmarker.create_from_options(options)

        try:
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        except Exception:
            self.face_mesh = None
        
        # Screen dimensions using ctypes (bare metal, no lag)
        user32 = ctypes.windll.user32
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        
        is_clicking = False
        
        # Smoothing variables
        smooth_x, smooth_y = 0, 0
        smoothing_factor = 0.5  # Adjust between 0.1 (smooth/slow) and 0.9 (fast/jittery)

        self.cap = cv2.VideoCapture(0)
        time.sleep(1)
        
        if not self.cap.isOpened():
            print("[Ultron Vision] Error: Could not open webcam.")
            return

        print("[Ultron Vision] Active on Dedicated CPU Core. Zero-Lag Mode Online.")
        
        # Mouse event constants
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        
        # Swipe tracking
        history_x = []
        swipe_cooldown = 0
        
        # Zoom tracking
        history_zoom = []
        zoom_cooldown = 0
        
        while True:
            success, img = self.cap.read()
            if not success:
                break
                
            frame = cv2.flip(img, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = detector.detect(mp_image)
            
            if swipe_cooldown > 0:
                swipe_cooldown -= 1
            if zoom_cooldown > 0:
                zoom_cooldown -= 1
            
            if detection_result.hand_landmarks:
                # ---------------------------------------------------------
                # HOLOGRAPHIC ZOOM (TWO HANDS)
                # ---------------------------------------------------------
                if len(detection_result.hand_landmarks) == 2:
                    h1_index = detection_result.hand_landmarks[0][8]
                    h2_index = detection_result.hand_landmarks[1][8]
                    dist_zoom = self.calculate_distance(h1_index, h2_index)
                    history_zoom.append(dist_zoom)
                    if len(history_zoom) > 5:
                        history_zoom.pop(0)
                    if len(history_zoom) == 5 and zoom_cooldown == 0:
                        delta_zoom = history_zoom[-1] - history_zoom[0]
                        if delta_zoom > 0.15:
                            pyautogui.hotkey('win', '+')
                            zoom_cooldown = 30
                            history_zoom.clear()
                        elif delta_zoom < -0.15:
                            pyautogui.hotkey('win', '-')
                            zoom_cooldown = 30
                            history_zoom.clear()
                
                # Hand tracking for mouse (hand 0) and volume (hand 1)
                is_two_handed = len(detection_result.hand_landmarks) == 2
                for hand_idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                    if hand_idx == 0:
                        # PRIMARY HAND: MOUSE CONTROL
                        index_tip = hand_landmarks[8]
                        thumb_tip = hand_landmarks[4]
                        wrist = hand_landmarks[0]
                        
                        # Target screen coordinates (Tracking Index Finger)
                        target_x = int(index_tip.x * screen_w)
                        target_y = int(index_tip.y * screen_h)
                        
                        # Swipe detection logic (track wrist movement)
                        history_x.append(wrist.x)
                        if len(history_x) > 10:
                            history_x.pop(0)
                            
                        if len(history_x) == 10 and swipe_cooldown == 0:
                            dx = history_x[-1] - history_x[0]
                            if dx > 0.3: # Fast Swipe Right
                                # Iron Man Screen Swipe -> Next Desktop / Alt Tab
                                pyautogui.hotkey('ctrl', 'win', 'right')
                                swipe_cooldown = 30
                                history_x.clear()
                            elif dx < -0.3: # Fast Swipe Left
                                pyautogui.hotkey('ctrl', 'win', 'left')
                                swipe_cooldown = 30
                                history_x.clear()
                        
                        # Exponential Smoothing (Anti-jitter)
                        smooth_x = (1 - smoothing_factor) * smooth_x + smoothing_factor * target_x
                        smooth_y = (1 - smoothing_factor) * smooth_y + smoothing_factor * target_y
                        
                        ctypes.windll.user32.SetCursorPos(int(smooth_x), int(smooth_y))
                        
                        # Draw visual tracking pointer on camera preview frame
                        cx, cy = int(index_tip.x * img_w), int(index_tip.y * img_h)
                        cv2.circle(frame, (cx, cy), 10, (255, 0, 255), cv2.FILLED)
                        
                        # Pinch Detection (Thumb + Index Tip) -> Click
                        dist = self.calculate_distance(index_tip, thumb_tip)
                        if dist < 0.07: # Slightly higher pinch sensitivity for effortless clicks
                            cv2.circle(frame, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
                            cv2.putText(frame, "CLICKING", (cx + 20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            if not is_clicking:
                                ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                                is_clicking = True
                        else:
                            if is_clicking:
                                ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                                is_clicking = False
                                
                    elif hand_idx == 1 and self.volume:
                        # SECONDARY HAND: VOLUME DIAL
                        index_tip = hand_landmarks[8]
                        thumb_tip = hand_landmarks[4]
                        dist = self.calculate_distance(index_tip, thumb_tip)
                        
                        vol_setting = np.interp(dist, [0.05, 0.25], [self.minVol, self.maxVol])
                        try:
                            self.volume.SetMasterVolumeLevel(vol_setting, None)
                        except:
                            pass

            # --- PHASE 24: JARVIS EYE-POINTER (Gaze Tracking) ---
            # Process Face Mesh to find Irises
            if self.face_mesh:
                face_results = self.face_mesh.process(rgb_frame)
                if face_results.multi_face_landmarks:
                    for face_landmarks in face_results.multi_face_landmarks:
                        # Left Eye Landmarks: Top=159, Bottom=145, Iris Center=473
                        left_iris_y = face_landmarks.landmark[473].y
                        eye_top_y = face_landmarks.landmark[159].y
                        eye_bottom_y = face_landmarks.landmark[145].y
                        
                        # Calculate vertical gaze ratio (0.0 = looking all the way up, 1.0 = looking down)
                        eye_height = eye_bottom_y - eye_top_y
                        if eye_height > 0:
                            vertical_ratio = (left_iris_y - eye_top_y) / eye_height
                            
                            # Trigger Scrolling based on Gaze
                            if vertical_ratio < 0.35:
                                # Looking UP -> Scroll UP
                                pyautogui.scroll(40)
                            elif vertical_ratio > 0.65:
                                # Looking DOWN -> Scroll DOWN
                                pyautogui.scroll(-40)

            try:
                cv2.imshow("Ultron Vision (Gestures + Gaze)", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as gui_err:
                # Log once if GUI backend is unavailable and run vision in headless mode
                if not hasattr(self, '_gui_warned'):
                    print(f"[Ultron Vision] GUI display warning: {gui_err}. Continuing in headless background mode.")
                    self._gui_warned = True

        self.cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
