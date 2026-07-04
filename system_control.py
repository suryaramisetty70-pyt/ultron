import subprocess
import webbrowser
import os

# =============================
# SYSTEM CONTROL FUNCTIONS
# =============================

def open_notepad():
    try:
        subprocess.Popen(["notepad.exe"])
        return "Notepad opened"
    except Exception as e:
        return f"Failed to open Notepad: {e}"


def open_calculator():
    try:
        subprocess.Popen(["calc.exe"])
        return "Calculator opened"
    except Exception as e:
        return f"Failed to open Calculator: {e}"


def open_chrome():
    try:
        # First try normal way
        webbrowser.open("https://www.google.com")
        return "Chrome opened"
    except:
        try:
            # Fallback (direct chrome path)
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            subprocess.Popen(chrome_path)
            return "Chrome opened"
        except Exception as e:
            return f"Failed to open Chrome: {e}"
