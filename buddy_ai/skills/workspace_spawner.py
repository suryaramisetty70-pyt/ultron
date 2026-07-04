# workspace_spawner.py
"""Workspace Spawner Skill

Opens specific folders, files, and browser tabs from a single
voice command or config definition.
"""
import os
import subprocess
import webbrowser

# Predefined workspaces (can be overridden via config)
WORKSPACES = {
    "coding": {
        "folders": [os.path.expanduser("~/OneDrive/Desktop/BUUDY_AI")],
        "files": [],
        "urls": ["https://github.com"],
        "apps": ["code"],  # VS Code
    },
    "research": {
        "folders": [],
        "files": [],
        "urls": [
            "https://scholar.google.com",
            "https://arxiv.org",
            "https://chat.openai.com",
        ],
        "apps": [],
    },
    "social": {
        "folders": [],
        "files": [],
        "urls": [
            "https://twitter.com",
            "https://instagram.com",
            "https://reddit.com",
        ],
        "apps": [],
    },
}

def spawn_workspace(name: str) -> str:
    """Open all items defined for the named workspace."""
    name_lower = name.lower().strip()
    if name_lower not in WORKSPACES:
        return f"Unknown workspace: '{name}'. Available: {', '.join(WORKSPACES.keys())}"

    ws = WORKSPACES[name_lower]
    opened = []

    # Open folders
    for folder in ws.get("folders", []):
        if os.path.isdir(folder):
            os.startfile(folder)
            opened.append(f"Folder: {folder}")

    # Open files
    for file_path in ws.get("files", []):
        if os.path.isfile(file_path):
            os.startfile(file_path)
            opened.append(f"File: {file_path}")

    # Open URLs
    for url in ws.get("urls", []):
        webbrowser.open(url)
        opened.append(f"URL: {url}")

    # Launch apps
    for app in ws.get("apps", []):
        try:
            subprocess.Popen(app, shell=True)
            opened.append(f"App: {app}")
        except Exception as e:
            opened.append(f"App FAILED ({app}): {e}")

    return f"Workspace '{name}' spawned: {len(opened)} items opened.\n" + "\n".join(opened)

def add_workspace(name: str, folders: list = None, files: list = None,
                  urls: list = None, apps: list = None):
    """Dynamically add a workspace definition."""
    WORKSPACES[name.lower()] = {
        "folders": folders or [],
        "files": files or [],
        "urls": urls or [],
        "apps": apps or [],
    }

def list_workspaces() -> list:
    """Return available workspace names."""
    return list(WORKSPACES.keys())
