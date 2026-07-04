"""
Ultron Computer Use (Claude Parity)
Allows Ultron to physically control the mouse and keyboard to navigate the UI.
"""
import pyautogui
import time

# Security: Failsafe enabled. Moving mouse to a corner will abort pyautogui.
pyautogui.FAILSAFE = True

def move_mouse(x, y):
    """Moves the mouse to specific coordinates on the screen."""
    try:
        pyautogui.moveTo(int(x), int(y), duration=0.5)
        return f"Mouse moved to ({x}, {y})."
    except Exception as e:
        return f"Failed to move mouse: {str(e)}"

def click_mouse(x=None, y=None):
    """Clicks the mouse at current location or specified coordinates."""
    try:
        if x is not None and y is not None:
            pyautogui.click(int(x), int(y))
            return f"Clicked mouse at ({x}, {y})."
        else:
            pyautogui.click()
            return "Clicked mouse at current location."
    except Exception as e:
        return f"Failed to click mouse: {str(e)}"

def type_text(text, press_enter=False):
    """Types text using the keyboard."""
    try:
        pyautogui.write(text, interval=0.02)
        if press_enter:
            pyautogui.press('enter')
        return f"Typed text: '{text}'"
    except Exception as e:
        return f"Failed to type text: {str(e)}"

def press_shortcut(key_combo):
    """
    Presses a combination of keys (e.g. 'ctrl+c', 'win+r').
    Pass the keys separated by a plus sign.
    """
    try:
        keys = key_combo.split('+')
        pyautogui.hotkey(*keys)
        return f"Pressed shortcut: {key_combo}"
    except Exception as e:
        return f"Failed to press shortcut: {str(e)}"
