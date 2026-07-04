"""
Ultron Vision Skills
Analyzes screenshots using Google Gemini API.
"""
import os
import pyautogui
import google.generativeai as genai

# Setup Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def analyze_screen(prompt="Describe what is on this screen in detail."):
    """
    Takes a screenshot of the current display and uses Gemini Vision to analyze it.
    """
    if not GEMINI_API_KEY:
        return (
            "Vision systems are offline. You need to provide a Google Gemini API Key "
            "to use the Screen Analysis feature. Please set the GEMINI_API_KEY environment variable."
        )

    try:
        # Take screenshot
        screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "vision_temp.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        # Initialize Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Upload image to Gemini
        import PIL.Image
        img = PIL.Image.open(screenshot_path)
        
        # Generate content
        response = model.generate_content([prompt, img])
        
        # Cleanup
        try:
            img.close()
            os.remove(screenshot_path)
        except:
            pass
            
        return f"Screen Analysis: {response.text}"
        
    except Exception as e:
        return f"Vision processing failed: {str(e)}"
