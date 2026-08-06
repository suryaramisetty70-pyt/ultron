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

def close_application(app_name: str) -> str:
    """
    Closes running applications on Windows by process name or app title using taskkill.
    """
    import subprocess
    if not app_name or not app_name.strip():
        return "Please specify the application name to close."
        
    target = app_name.strip().lower()
    
    # Map common app aliases to process names
    process_map = {
        "chrome": "chrome.exe",
        "browser": "chrome.exe",
        "vs code": "Code.exe",
        "vscode": "Code.exe",
        "code": "Code.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "spotify": "Spotify.exe",
        "discord": "Discord.exe",
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "terminal": "cmd.exe",
        "powershell": "powershell.exe",
        "edge": "msedge.exe",
        "msedge": "msedge.exe"
    }
    
    proc_name = process_map.get(target, f"{target}.exe")
    
    try:
        print(f"[App Control] Closing application: {app_name} (process: {proc_name})")
        result = subprocess.run(["taskkill", "/f", "/im", proc_name], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully closed {app_name}."
        else:
            # Try taskkill by window title match
            alt_res = subprocess.run(["taskkill", "/f", "/fi", f"WINDOWTITLE eq {app_name}*"], capture_output=True, text=True)
            if alt_res.returncode == 0:
                return f"Successfully closed window matching {app_name}."
            return f"Could not find or close active application: {app_name}."
    except Exception as e:
        return f"Error while closing application {app_name}: {str(e)}"
