"""
Ultron Task Manager (Chief of Staff Protocol)
Manages the user's daily schedule, to-do list, and reminders.
"""
import json
import os
import uuid
from datetime import datetime

TASKS_FILE = "tasks.json"

def _load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

def add_task(description):
    """Adds a new task to the user's to-do list."""
    tasks = _load_tasks()
    task_id = str(uuid.uuid4())[:6]
    task = {
        "id": task_id,
        "description": description,
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    tasks.append(task)
    _save_tasks(tasks)
    return f"Successfully added task: '{description}'. (ID: {task_id})"

def list_tasks():
    """Lists all pending tasks."""
    tasks = _load_tasks()
    pending = [t for t in tasks if t["status"] == "pending"]
    if not pending:
        return "You have no pending tasks. Your schedule is completely clear!"
    
    result = "Here are your pending tasks:\n"
    for t in pending:
        result += f"- [ID: {t['id']}] {t['description']} (Created: {t['created_at']})\n"
    return result

def complete_task(task_id):
    """Marks a task as complete using its ID or partial description."""
    tasks = _load_tasks()
    for t in tasks:
        if t["status"] == "pending" and (task_id.lower() in t["id"].lower() or task_id.lower() in t["description"].lower()):
            t["status"] = "completed"
            _save_tasks(tasks)
            return f"Excellent. I have marked the task '{t['description']}' as completed."
            
    return f"I could not find a pending task matching '{task_id}'. Please check your active tasks."
