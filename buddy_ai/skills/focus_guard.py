"""
Focus Guard Engine
Edits the Windows Hosts file to block or unblock distracting websites globally.
Requires Ultron to be run as Administrator to function.
"""

import ctypes
import os

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"
DISTRACTIONS = [
    "www.facebook.com", "facebook.com", 
    "www.youtube.com", "youtube.com", 
    "www.reddit.com", "reddit.com",
    "www.instagram.com", "instagram.com",
    "twitter.com", "x.com"
]

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def activate_focus_guard() -> str:
    """
    Blocks distracting websites by routing them to localhost in the Windows hosts file.
    """
    print("\n[Focus Guard] Initiating Neural Blockade on distracting domains...")
    if not is_admin():
        return "ERROR: Focus Guard requires Administrator privileges. Please restart Ultron Terminal as Administrator."
        
    try:
        with open(HOSTS_PATH, "r+") as file:
            content = file.read()
            for site in DISTRACTIONS:
                if site not in content:
                    file.write(f"\n{REDIRECT_IP} {site}")
        print("[Focus Guard] Blockade active. All distracting incoming traffic severed.")
        return "SUCCESS: Focus Guard is active. All distracting websites have been hard-blocked at the OS level."
    except Exception as e:
        return f"ERROR: Failed to activate Focus Guard due to file lock or permissions: {e}"

def deactivate_focus_guard() -> str:
    """
    Unblocks websites by removing them from the Windows hosts file.
    """
    print("\n[Focus Guard] Lifting Neural Blockade...")
    if not is_admin():
        return "ERROR: Focus Guard requires Administrator privileges."
        
    try:
        with open(HOSTS_PATH, "r") as file:
            lines = file.readlines()
            
        with open(HOSTS_PATH, "w") as file:
            for line in lines:
                if not any(site in line for site in DISTRACTIONS):
                    file.write(line)
                    
        print("[Focus Guard] Blockade lifted. Free browsing restored.")
        return "SUCCESS: Focus Guard deactivated. Normal internet routing restored."
    except Exception as e:
        return f"ERROR: Failed to deactivate Focus Guard: {e}"
