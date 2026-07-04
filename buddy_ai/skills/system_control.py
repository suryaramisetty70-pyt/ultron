"""
Ultron System Control Skills
Controls PC volume, brightness, lock, shutdown, restart, and app launching.
"""
import subprocess
import ctypes
import os

# ============================================
# VOLUME CONTROL (Using nircmd or pycaw)
# ============================================
def set_volume(level):
    """Set system volume to a percentage (0-100)."""
    try:
        # Use PowerShell to set volume
        # Scale 0-100 to 0-65535
        scaled = int((level / 100) * 65535)
        subprocess.run(
            ['powershell', '-Command', 
             f'$wshShell = New-Object -ComObject WScript.Shell; '
             f'1..50 | ForEach-Object {{$wshShell.SendKeys([char]174)}}; '  # Mute first
             f'1..{level // 2} | ForEach-Object {{$wshShell.SendKeys([char]175)}}'],  # Set level
            capture_output=True, timeout=10
        )
        return f"Volume set to {level}%."
    except Exception as e:
        return f"Failed to set volume: {str(e)}"

def volume_up():
    """Increase volume by 10%."""
    try:
        subprocess.run(
            ['powershell', '-Command',
             '$wshShell = New-Object -ComObject WScript.Shell; '
             '1..5 | ForEach-Object {$wshShell.SendKeys([char]175)}'],
            capture_output=True, timeout=10
        )
        return "Volume increased."
    except Exception as e:
        return f"Failed: {str(e)}"

def volume_down():
    """Decrease volume by 10%."""
    try:
        subprocess.run(
            ['powershell', '-Command',
             '$wshShell = New-Object -ComObject WScript.Shell; '
             '1..5 | ForEach-Object {$wshShell.SendKeys([char]174)}'],
            capture_output=True, timeout=10
        )
        return "Volume decreased."
    except Exception as e:
        return f"Failed: {str(e)}"

def mute_volume():
    """Toggle mute."""
    try:
        subprocess.run(
            ['powershell', '-Command',
             '$wshShell = New-Object -ComObject WScript.Shell; '
             '$wshShell.SendKeys([char]173)'],
            capture_output=True, timeout=10
        )
        return "Volume muted/unmuted."
    except Exception as e:
        return f"Failed: {str(e)}"

# ============================================
# SYSTEM POWER COMMANDS
# ============================================
def lock_pc():
    """Lock the PC instantly."""
    ctypes.windll.user32.LockWorkStation()
    return "PC locked."

def shutdown_pc():
    """Shutdown PC in 30 seconds."""
    os.system("shutdown /s /t 30")
    return "Shutting down in 30 seconds. Say 'cancel shutdown' to abort."

def restart_pc():
    """Restart the PC."""
    os.system("shutdown /r /t 30")
    return "Restarting in 30 seconds."

def cancel_shutdown():
    """Cancel a pending shutdown."""
    os.system("shutdown /a")
    return "Shutdown cancelled."

def sleep_pc():
    """Put PC to sleep."""
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "PC going to sleep."

# ============================================
# APPLICATION LAUNCHER
# ============================================
APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "settings": "ms-settings:",
    "control panel": "control.exe",
    "snipping tool": "SnippingTool.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "firefox": "firefox.exe",
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "telegram": "telegram.exe",
    "whatsapp": "whatsapp.exe",
    "vs code": "code.exe",
    "visual studio code": "code.exe",
    "cursor": "cursor.exe",
}

def open_application(app_name):
    """Open any application by name."""
    app_name_lower = app_name.lower().strip()
    
    # Check known apps
    for key, exe in APP_MAP.items():
        if key in app_name_lower:
            try:
                if exe.startswith("ms-"):
                    os.system(f"start {exe}")
                else:
                    subprocess.Popen(exe)
                return f"Opening {key}."
            except Exception:
                try:
                    os.startfile(exe)
                    return f"Opening {key}."
                except Exception:
                    return f"Could not find {key} on your system."
    
    # Try to open as raw executable
    try:
        subprocess.Popen(app_name_lower)
        return f"Opening {app_name}."
    except Exception:
        try:
            os.system(f"start {app_name_lower}")
            return f"Opening {app_name}."
        except Exception:
            return f"Could not find application: {app_name}"

def close_application(app_name):
    """Close an application by name."""
    app_name_lower = app_name.lower().strip()
    try:
        os.system(f"taskkill /im {app_name_lower}.exe /f")
        return f"Closed {app_name}."
    except Exception:
        return f"Could not close {app_name}."

# ============================================
# SCREENSHOT
# ============================================
def take_screenshot():
    """Take a screenshot and save it."""
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        path = os.path.join(os.path.expanduser("~"), "Desktop", "ultron_screenshot.png")
        screenshot.save(path)
        return f"Screenshot saved to {path}."
    except Exception as e:
        return f"Screenshot failed: {str(e)}"

# ============================================
# MUSIC CONTROL (YouTube)
# ============================================
def play_music(song_name):
    """Play a song on YouTube."""
    import webbrowser
    search_query = song_name.replace(" ", "+")
    url = f"https://www.youtube.com/results?search_query={search_query}"
    webbrowser.open(url)
    return f"Playing {song_name} on YouTube."

# ============================================
# DATETIME & WEATHER
# ============================================
def get_current_time():
    """Get current date and time."""
    from datetime import datetime
    now = datetime.now()
    return now.strftime("It is %I:%M %p on %A, %B %d, %Y.")

def get_battery_status():
    """Get battery percentage."""
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            return f"Battery is at {battery.percent}%. {'Plugged in.' if battery.power_plugged else 'Running on battery.'}"
        return "No battery detected (Desktop PC)."
    except Exception:
        return "Could not read battery status."
