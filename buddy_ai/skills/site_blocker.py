# site_blocker.py
"""Smart Site-Blocker Skill

Edits the Windows hosts file to block distracting websites during
focus sessions. Requires admin privileges.
"""
import os
import ctypes
import sys

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"
BLOCK_MARKER = "# === ULTRON FOCUS BLOCK ==="

DEFAULT_DISTRACTIONS = [
    "www.youtube.com", "youtube.com",
    "www.reddit.com", "reddit.com",
    "www.twitter.com", "twitter.com", "x.com",
    "www.instagram.com", "instagram.com",
    "www.facebook.com", "facebook.com",
    "www.tiktok.com", "tiktok.com",
]

def _is_admin() -> bool:
    """Check if current process has admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def block_sites(sites: list = None) -> str:
    """Add sites to hosts file to block them."""
    if not _is_admin():
        return "ERROR: Admin privileges required. Run as Administrator."

    sites = sites or DEFAULT_DISTRACTIONS
    try:
        with open(HOSTS_PATH, "r") as f:
            content = f.read()

        if BLOCK_MARKER in content:
            return "Sites already blocked. Unblock first to update."

        lines = [f"\n{BLOCK_MARKER}\n"]
        for site in sites:
            lines.append(f"{REDIRECT_IP}  {site}\n")
        lines.append(f"{BLOCK_MARKER}\n")

        with open(HOSTS_PATH, "a") as f:
            f.writelines(lines)

        # Flush DNS cache
        os.system("ipconfig /flushdns")
        return f"Blocked {len(sites)} sites. Focus mode ON."
    except Exception as e:
        return f"Failed to block sites: {e}"

def unblock_sites() -> str:
    """Remove Ultron-blocked entries from hosts file."""
    if not _is_admin():
        return "ERROR: Admin privileges required. Run as Administrator."

    try:
        with open(HOSTS_PATH, "r") as f:
            lines = f.readlines()

        new_lines = []
        inside_block = False
        for line in lines:
            if BLOCK_MARKER in line:
                inside_block = not inside_block
                continue
            if not inside_block:
                new_lines.append(line)

        with open(HOSTS_PATH, "w") as f:
            f.writelines(new_lines)

        os.system("ipconfig /flushdns")
        return "All sites unblocked. Focus mode OFF."
    except Exception as e:
        return f"Failed to unblock sites: {e}"

def list_blocked() -> list:
    """Return list of currently blocked sites."""
    try:
        with open(HOSTS_PATH, "r") as f:
            lines = f.readlines()

        blocked = []
        inside_block = False
        for line in lines:
            if BLOCK_MARKER in line:
                inside_block = not inside_block
                continue
            if inside_block and line.strip():
                parts = line.strip().split()
                if len(parts) >= 2:
                    blocked.append(parts[1])
        return blocked
    except Exception:
        return []
