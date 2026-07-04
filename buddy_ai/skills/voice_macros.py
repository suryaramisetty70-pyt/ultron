# voice_macros.py
"""Voice Macros Skill

Spoken phrases trigger custom Python scripts or system commands.
Macros are defined in config/voice_features.yaml.
"""
import subprocess
import os
import json

# Default macros (overridden by config)
DEFAULT_MACROS = {
    "open calculator": "calc",
    "open notepad": "notepad",
    "open browser": "start chrome",
    "open file explorer": "explorer",
    "lock screen": "rundll32.exe user32.dll,LockWorkStation",
    "take screenshot": "snippingtool",
    "open task manager": "taskmgr",
    "open terminal": "wt",
    "open settings": "start ms-settings:",
}

_custom_macros = {}

def load_macros(config_path: str = "config/voice_features.yaml"):
    """Load custom macros from YAML config."""
    global _custom_macros
    try:
        import yaml
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        _custom_macros = cfg.get("voice_macros", {})
    except Exception:
        _custom_macros = {}

def get_all_macros() -> dict:
    """Return merged default + custom macros."""
    merged = dict(DEFAULT_MACROS)
    merged.update(_custom_macros)
    return merged

def execute_macro(spoken_text: str) -> str:
    """Match spoken text against known macros and execute.
    Returns a status message.
    """
    macros = get_all_macros()
    spoken_lower = spoken_text.lower().strip()

    for trigger, command in macros.items():
        if trigger in spoken_lower:
            try:
                if command.endswith(".py"):
                    subprocess.Popen(["python", command], shell=True)
                else:
                    subprocess.Popen(command, shell=True)
                return f"Executed macro: {trigger}"
            except Exception as e:
                return f"Macro failed: {e}"

    return "No matching macro found."
