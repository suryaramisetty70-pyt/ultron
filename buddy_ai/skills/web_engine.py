"""
Web & System Engine
Allows Ultron to open websites and silently install software using Windows Package Manager.
"""

import webbrowser
import subprocess

def open_website(url: str) -> str:
    """Instantly opens a URL in the user's default web browser."""
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
        webbrowser.open(url)
        return f"SUCCESS: Opened {url} in the web browser."
    except Exception as e:
        return f"Failed to open website: {str(e)}"

def install_software(software_name: str) -> str:
    """
    Silently downloads and installs software using Windows Package Manager (winget).
    E.g. 'python', 'vlc', 'googlechrome'
    """
    try:
        # We use winget to search and install
        # --accept-package-agreements --accept-source-agreements bypasses prompts
        command = ["winget", "install", software_name, "--accept-package-agreements", "--accept-source-agreements"]
        
        # Start the process in the background
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return f"SUCCESS: {software_name} has been installed on the system.\nLog: {result.stdout}"
        else:
            return f"FAILED to install {software_name}.\nError: {result.stderr}\nOutput: {result.stdout}"
            
    except subprocess.TimeoutExpired:
        return f"Installation of {software_name} is taking longer than 2 minutes. It might be running in the background."
    except Exception as e:
        return f"Failed to run installer for {software_name}: {str(e)}"
