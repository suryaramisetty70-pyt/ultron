import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")

EVENTS_FILE = os.path.join(MEMORY_DIR, "events.json")
ROUTINES_FILE = os.path.join(MEMORY_DIR, "routines.json")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

os.makedirs(EXPORT_DIR, exist_ok=True)

# ===============================
# LOAD JSON SAFELY
# ===============================
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

# ===============================
# VIEW MEMORY
# ===============================
def view_memory():
    events = load_json(EVENTS_FILE)
    routines = load_json(ROUTINES_FILE)

    print("\n--- EVENTS ---")
    print(f"Total events stored: {len(events)}")

    print("\n--- ROUTINES ---")
    for r in routines:
        print(
            f"Command: {r['command']} | "
            f"Confidence: {int(r['confidence']*100)}%"
        )

# ===============================
# CLEAR MEMORY
# ===============================
def clear_memory():
    confirm = input("Are you sure you want to delete all memory? (yes/no): ")
    if confirm.lower() == "yes":
        with open(EVENTS_FILE, "w") as f:
            json.dump([], f)
        with open(ROUTINES_FILE, "w") as f:
            json.dump([], f)
        print("All memory deleted successfully.")
    else:
        print("Operation cancelled.")

# ===============================
# EXPORT AI TWIN
# ===============================
def export_ai_twin():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = os.path.join(EXPORT_DIR, f"ai_twin_{timestamp}")

    os.makedirs(export_path, exist_ok=True)

    shutil.copy(EVENTS_FILE, export_path)
    shutil.copy(ROUTINES_FILE, export_path)

    print(f"AI Twin exported to: {export_path}")

# ===============================
# DASHBOARD MENU
# ===============================
def dashboard():
    while True:
        print("\n=== PRIVACY DASHBOARD ===")
        print("1. View stored memory")
        print("2. Delete all memory")
        print("3. Export AI Twin")
        print("4. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            view_memory()
        elif choice == "2":
            clear_memory()
        elif choice == "3":
            export_ai_twin()
        elif choice == "4":
            print("Exiting dashboard.")
            break
        else:
            print("Invalid choice.")

# ===============================
# START
# ===============================
if __name__ == "__main__":
    dashboard()
