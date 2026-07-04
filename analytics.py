import json
import os
from datetime import datetime

DATA_FILE = "analytics_data.json"

def init_analytics():
    if not os.path.exists(DATA_FILE):
        data = {
            "total_commands": 0,
            "files_created": 0,
            "websites_opened": 0,
            "volume_actions": 0,
            "errors": 0,
            "history": []
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)

def update_stat(key):
    if not os.path.exists(DATA_FILE):
        init_analytics()

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if key in data:
        data[key] += 1

    data["history"].append({
        "time": str(datetime.now()),
        "action": key
    })

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
