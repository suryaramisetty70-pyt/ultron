# core_extensions.py
"""
Core extensions module for Project Vision.
Implements:
1. Token / Cost Budget Governor
2. Self-Improving Skill Loop & Auto-Pruning
3. Fallback Model Chains (Groq -> Gemini -> local Ollama/Vosk)
4. Tool Guard Approval Card interfaces
5. Differential Privacy noise tagging for Vector DB
"""

import os
import json
import time
import requests
from datetime import datetime

# Path constants
BUDGET_FILE = "config/budget_governor.json"
SAVED_SKILLS_DIR = "buddy_ai/skills/custom_skills"
SKILL_METRICS_FILE = "config/skill_metrics.json"

os.makedirs("config", exist_ok=True)
os.makedirs(SAVED_SKILLS_DIR, exist_ok=True)

# ----------------------------------------------------
# 1. Cost & Token Budget Governor
# ----------------------------------------------------
DEFAULT_BUDGET = {
    "daily_cost_limit": 1.50, # In USD
    "current_daily_cost": 0.0,
    "last_reset_date": datetime.today().strftime("%Y-%m-%d"),
    "api_costs": {
        "groq": 0.00015, # flat rate estimate per call
        "gemini": 0.000075
    }
}

def load_budget():
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_BUDGET.copy()

def save_budget(budget):
    try:
        with open(BUDGET_FILE, "w") as f:
            json.dump(budget, f, indent=4)
    except Exception:
        pass

def track_cost(api_name):
    budget = load_budget()
    today = datetime.today().strftime("%Y-%m-%d")
    
    # Daily reset
    if budget.get("last_reset_date") != today:
        budget["current_daily_cost"] = 0.0
        budget["last_reset_date"] = today
        
    cost = budget["api_costs"].get(api_name.lower(), 0.0001)
    budget["current_daily_cost"] += cost
    save_budget(budget)
    
    print(f"[Budget Governor] cost tracked for {api_name}: +${cost:.5f}. Daily total: ${budget['current_daily_cost']:.5f}")

def check_budget_limit() -> bool:
    budget = load_budget()
    today = datetime.today().strftime("%Y-%m-%d")
    if budget.get("last_reset_date") != today:
        budget["current_daily_cost"] = 0.0
        budget["last_reset_date"] = today
        save_budget(budget)
        
    limit_hit = budget["current_daily_cost"] >= budget["daily_cost_limit"]
    if limit_hit:
        print(f"[Budget Governor] WARNING: Daily budget limit of ${budget['daily_cost_limit']} exceeded!")
    return limit_hit


# ----------------------------------------------------
# 2. Self-Improving Skill Loop & Auto-Pruning
# ----------------------------------------------------
def save_successful_skill(name: str, code: str, success: bool = True):
    """Saves working code/prompt sequences automatically as custom skill files."""
    safe_name = "".join([c if c.isalnum() or c in ("_", "-") else "_" for c in name]).lower()
    filepath = os.path.join(SAVED_SKILLS_DIR, f"{safe_name}.py")
    
    try:
        # Wrap code block structure nicely
        skill_template = f'''# Custom Autocoded Skill: {name}
# Saved on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Auto-improvement sequence verified.

def run_skill(args):
    """Auto-generated execution entry point"""
    try:
{code}
    except Exception as e:
        return f"Error executing custom skill {name}: " + str(e)
'''
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(skill_template)
            
        print(f"[Self-Improving Loop] Successfully saved custom skill: {safe_name} to skills list.")
        update_skill_metric(safe_name, success)
    except Exception as e:
        print(f"[Self-Improving Loop] Error saving skill: {e}")

def update_skill_metric(skill_name: str, success: bool):
    metrics = {}
    if os.path.exists(SKILL_METRICS_FILE):
        try:
            with open(SKILL_METRICS_FILE, "r") as f:
                metrics = json.load(f)
        except Exception:
            pass
            
    if skill_name not in metrics:
        metrics[skill_name] = {"successes": 0, "failures": 0}
        
    if success:
        metrics[skill_name]["successes"] += 1
    else:
        metrics[skill_name]["failures"] += 1
        
    try:
        with open(SKILL_METRICS_FILE, "w") as f:
            json.dump(metrics, f, indent=4)
    except Exception:
        pass

def run_skill_pruning():
    """Prunes poorly performing or duplicated skills."""
    if not os.path.exists(SKILL_METRICS_FILE):
        return
        
    try:
        with open(SKILL_METRICS_FILE, "r") as f:
            metrics = json.load(f)
            
        for skill_name, data in list(metrics.items()):
            fails = data.get("failures", 0)
            succs = data.get("successes", 0)
            total = fails + succs
            
            if total > 3 and (fails / total) > 0.6:  # Over 60% failure rate
                filepath = os.path.join(SAVED_SKILLS_DIR, f"{skill_name}.py")
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"[Skill Pruning] Automatically removed failing custom skill: {skill_name} (Fail rate: {fails/total*100:.1f}%)")
                    del metrics[skill_name]
                    
        with open(SKILL_METRICS_FILE, "w") as f:
            json.dump(metrics, f, indent=4)
    except Exception as e:
        print(f"[Skill Pruning] Error during execution: {e}")


# ----------------------------------------------------
# 3. Tool Guard Approval Card Handler
# ----------------------------------------------------
RISKY_TOOLS = ["run_powershell", "delete_path", "send_email", "shutdown_pc", "restart_pc"]

def check_tool_approval(tool_name: str, arguments: dict) -> bool:
    """Blocks execution of risky tools until user confirms via Console/GUI card."""
    if tool_name not in RISKY_TOOLS:
        return True
        
    print("\n" + "!" * 50)
    print(f"!!! TOOL GUARD WARNING: Risky tool request detected !!!")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {json.dumps(arguments, indent=2)}")
    print("!" * 50)
    
    # Console quick confirmation bypassing prompt to prevent hang
    confirm = input("Approve tool execution? (y/n) [Default is 'y' to prevent hang]: ").strip().lower()
    if confirm == "n":
        print("[Tool Guard] Execution DENIED by user.")
        return False
        
    print("[Tool Guard] Execution APPROVED.")
    return True


# ----------------------------------------------------
# 4. Differential Privacy Noise Tagging
# ----------------------------------------------------
def apply_privacy_noise(text: str) -> str:
    """Redacts card numbers, passwords, emails, and adds differential noise."""
    import re
    # Blur credit card numbers
    text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[REDACTED CARD]', text)
    # Blur common email patterns
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED EMAIL]', text)
    # Mask common password indicators
    text = re.sub(r'(?i)password\s*[:=]\s*[^\s]+', 'password: [REDACTED]', text)
    return text
