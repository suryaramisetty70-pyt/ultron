# clipboard_butler.py
"""Clipboard Butler Skill

Background thread that monitors the clipboard for new content,
auto-extracts emails and URLs, and stores them in a log file.
"""
import threading
import re
import time
import json
import os

_running = False
_thread = None
_last_content = ""
_log_path = "clipboard_butler_log.json"

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')

def _load_log() -> list:
    if os.path.exists(_log_path):
        try:
            with open(_log_path, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_log(entries: list):
    with open(_log_path, "w") as f:
        json.dump(entries, f, indent=2)

def _extract_data(text: str) -> dict:
    """Extract emails and URLs from clipboard text."""
    emails = EMAIL_PATTERN.findall(text)
    urls = URL_PATTERN.findall(text)
    return {"emails": list(set(emails)), "urls": list(set(urls))}

def _monitor_loop():
    """Background loop: watch clipboard for changes."""
    global _running, _last_content
    try:
        import pyperclip
    except ImportError:
        print("[ClipboardButler] pyperclip not installed.")
        return

    while _running:
        try:
            current = pyperclip.paste()
            if current and current != _last_content:
                _last_content = current
                extracted = _extract_data(current)
                if extracted["emails"] or extracted["urls"]:
                    entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "raw_text": current[:200],  # truncate
                        "emails": extracted["emails"],
                        "urls": extracted["urls"],
                    }
                    log = _load_log()
                    log.append(entry)
                    _save_log(log)
                    print(f"[ClipboardButler] Captured: {len(extracted['emails'])} emails, {len(extracted['urls'])} URLs")
            time.sleep(1)
        except Exception:
            time.sleep(3)

def start_clipboard_butler():
    """Start the clipboard monitoring daemon."""
    global _running, _thread
    _running = True
    _thread = threading.Thread(target=_monitor_loop, daemon=True)
    _thread.start()
    print("[ClipboardButler] Started clipboard monitoring.")

def stop_clipboard_butler():
    """Stop the clipboard monitor."""
    global _running
    _running = False
    print("[ClipboardButler] Stopped.")

def get_captured() -> list:
    """Return all captured entries."""
    return _load_log()

def clear_log():
    """Clear the capture log."""
    _save_log([])
