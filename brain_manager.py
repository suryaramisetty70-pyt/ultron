import json
import os
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
BRAIN_FILE = os.path.join(MEMORY_DIR, "brain.json")

# ===============================
# INITIALIZE BRAIN
# ===============================
def init_brain():
    if not os.path.exists(BRAIN_FILE):
        brain = {
            "episodic": [],
            "habits": [],
            "preferences": {},
            "context": {
                "focus_mode": False,
                "last_active": None,
                "current_mode": "unknown"
            }
        }
        save_brain(brain)

# ===============================
# LOAD / SAVE
# ===============================
def load_brain():
    with open(BRAIN_FILE, "r") as f:
        return json.load(f)

def save_brain(brain):
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain, f, indent=4)

# ===============================
# EPISODIC MEMORY
# ===============================
def record_event(command, category="general"):
    brain = load_brain()
    event = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "command": command,
        "category": category
    }
    brain["episodic"].append(event)
    brain["context"]["last_active"] = event["time"]
    save_brain(brain)

# ===============================
# HABIT LEARNING
# ===============================
def update_habit(command):
    brain = load_brain()
    habits = brain["habits"]

    for h in habits:
        if h["command"] == command:
            h["count"] += 1
            h["last_used"] = time.time()
            save_brain(brain)
            return

    habits.append({
        "command": command,
        "count": 1,
        "first_seen": time.time(),
        "last_used": time.time()
    })
    save_brain(brain)

# ===============================
# CONTEXT UPDATE
# ===============================
def set_focus(state: bool):
    brain = load_brain()
    brain["context"]["focus_mode"] = state
    save_brain(brain)

def set_mode(mode: str):
    brain = load_brain()
    brain["context"]["current_mode"] = mode
    save_brain(brain)

# ===============================
# QUERY FUNCTIONS
# ===============================
def get_recent_events(limit=5):
    brain = load_brain()
    return brain["episodic"][-limit:]

def get_habits():
    brain = load_brain()
    return sorted(brain["habits"], key=lambda x: x["count"], reverse=True)

# ===============================
# INIT ON IMPORT
# ===============================
init_brain()
