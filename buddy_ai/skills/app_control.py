"""
Ultron Application Control
Handles opening and managing Windows applications reliably.
"""
import pyautogui
import time

def open_application(app_name):
    """
    Simulates pressing the Windows key, typing the app name, and pressing Enter.
    This reliably opens apps like VSCode, Chrome, Spotify, etc.
    """
    try:
        print(f"[App Control] Launching application: {app_name}")
        # Press the Windows key to open Start Menu
        pyautogui.press('win')
        time.sleep(0.5)
        
        # Type the name of the app
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.5)
        
        # Press Enter to open it
        pyautogui.press('enter')
        
        return f"Successfully executed start sequence for application: {app_name}. The application should now be opening on your screen."
    except Exception as e:
        return f"Failed to open application {app_name}: {str(e)}"
