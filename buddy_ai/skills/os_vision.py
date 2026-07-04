"""
OS-Level Vision (Self-Operating Desktop)
Allows Ultron to "see" the actual desktop by taking screenshots, analyzing them with AI Vision,
and physically moving the mouse to click on UI elements like a human.
"""

import os
import json
import time
import pyautogui
from PIL import ImageGrab
import google.generativeai as genai
from dotenv import load_dotenv

def os_vision_click(objective: str) -> str:
    """
    Takes a screenshot, uses Gemini Vision to find the X/Y coordinates of the objective, and clicks it.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
         return "ERROR: OS Vision Engine requires GEMINI_API_KEY in the .env file."

    genai.configure(api_key=api_key)
    
    print(f"\n[OS Vision] New Objective: '{objective}'")
    print("[OS Vision] Capturing retina screen data...")
    
    screenshot_path = "current_screen.png"
    screen = ImageGrab.grab()
    screen.save(screenshot_path)
    
    try:
        print("[OS Vision] Connecting to Vision Matrix...")
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        prompt = f"""
        You are a highly advanced OS automation AI. I have provided a screenshot of my computer desktop.
        My objective is: "{objective}".
        Analyze the screenshot and find the exact pixel coordinates (x, y) on the screen that I need to click to accomplish this objective.
        The screen resolution is {screen.width}x{screen.height}.
        Respond ONLY with a valid JSON object in this exact format:
        {{"x": 500, "y": 300, "reason": "Found the target icon here."}}
        Do not include markdown formatting or any other text.
        """
        
        import PIL.Image
        img = PIL.Image.open(screenshot_path)
        
        response = model.generate_content([prompt, img])
        
        # Parse JSON output from the Vision model
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        
        x = int(data['x'])
        y = int(data['y'])
        reason = data.get('reason', 'Target acquired.')
        
        print(f"[OS Vision] Analysis Complete: {reason}")
        print(f"[OS Vision] Moving physical mouse to ({x}, {y})...")
        
        # Animate the mouse moving to the target just like a human
        pyautogui.moveTo(x, y, duration=0.7, tween=pyautogui.easeInOutQuad)
        pyautogui.click()
        
        os.remove(screenshot_path)
        return f"SUCCESS: I have visually located and clicked the target at ({x}, {y})."
        
    except Exception as e:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        return f"ERROR: OS Vision failed. {str(e)}"
