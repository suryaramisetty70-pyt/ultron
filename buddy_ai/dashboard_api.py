# dashboard_api.py
"""
Ultron Real-Time Dashboard API Server
Provides authentic system health, process monitoring, skill metrics, and logs.
"""
import os
import json
import time
import socket
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend cross-origin requests

ANALYTICS_FILE = "analytics_data.json"
CLIPBOARD_FILE = "clipboard_butler_log.json"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
BLOCK_MARKER = "# === ULTRON FOCUS BLOCK ==="

def get_uptime():
    """Get system boot time and calculate uptime."""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    return str(uptime).split(".")[0]  # Format: hh:mm:ss or days, hh:mm:ss

def get_ultron_processes():
    """Check running processes to determine which Ultron modules are alive."""
    states = {
        "ultron_core": False,
        "ultron_vision": False,
        "ghostwriter": False,
        "voice_dictation": False,
        "wake_word": False
    }
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = proc.info.get('cmdline')
            if cmd:
                cmd_str = " ".join(cmd).lower()
                if "ultron.py" in cmd_str:
                    states["ultron_core"] = True
                if "ultron_vision.py" in cmd_str:
                    states["ultron_vision"] = True
                if "ghostwriter.py" in cmd_str:
                    states["ghostwriter"] = True
                if "voice_dictation.py" in cmd_str:
                    states["voice_dictation"] = True
                if "wake_word.py" in cmd_str:
                    states["wake_word"] = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return states

def check_focus_mode():
    """Check if site blocker is active by looking inside the hosts file."""
    if not os.path.exists(HOSTS_PATH):
        return False
    try:
        with open(HOSTS_PATH, "r") as f:
            content = f.read()
        return BLOCK_MARKER in content
    except Exception:
        return False

@app.route("/api/vitals", methods=["GET"])
def get_vitals():
    """Real system statistics."""
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    net_io = psutil.net_io_counters()
    
    return jsonify({
        "status": "online",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "uptime": get_uptime(),
        "cpu": {
            "usage_percent": cpu_percent,
            "cores": psutil.cpu_count(logical=True)
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "free_gb": round(memory.available / (1024**3), 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": disk.percent
        },
        "network": {
            "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2)
        }
    })

@app.route("/api/modules", methods=["GET"])
def get_modules():
    """Status of running Ultron software layers."""
    return jsonify(get_ultron_processes())

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Metrics compiled from Ultron data files."""
    # Default fallback metrics
    metrics = {
        "total_commands": 0,
        "files_created": 0,
        "websites_opened": 0,
        "volume_actions": 0,
        "errors": 0,
        "clipboard_items_captured": 0,
        "focus_mode_active": check_focus_mode()
    }
    
    # Read core analytics
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r") as f:
                data = json.load(f)
                for key in ["total_commands", "files_created", "websites_opened", "volume_actions", "errors"]:
                    metrics[key] = data.get(key, 0)
        except Exception:
            pass
            
    # Read clipboard logs count
    if os.path.exists(CLIPBOARD_FILE):
        try:
            with open(CLIPBOARD_FILE, "r") as f:
                clip_data = json.load(f)
                metrics["clipboard_items_captured"] = len(clip_data)
        except Exception:
            pass
            
    return jsonify(metrics)

@app.route("/api/history", methods=["GET"])
def get_history():
    """Get the recent command execution history log."""
    history = []
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r") as f:
                data = json.load(f)
                history = data.get("history", [])[-15:]  # Get last 15 items
        except Exception:
            pass
    return jsonify(history[::-1])  # Reverse so latest is first

@app.route("/api/focus/toggle", methods=["POST"])
def toggle_focus():
    """Trigger focus mode blocking / unblocking via host scripts (needs admin)."""
    # This route bridges to site_blocker skills
    data = request.json or {}
    enable = data.get("enable", False)
    
    try:
        from buddy_ai.skills.site_blocker import block_sites, unblock_sites
        if enable:
            res = block_sites()
        else:
            res = unblock_sites()
        return jsonify({"success": True, "message": res, "focus_active": check_focus_mode()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

USER_PROFILE_FILE = "user_profile.json"
CONFIG_FILE = "config/voice_features.yaml"

def load_profile():
    if os.path.exists(USER_PROFILE_FILE):
        try:
            with open(USER_PROFILE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"preferences": {}, "custom_instructions": []}

def save_profile(data):
    with open(USER_PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/api/training", methods=["GET"])
def get_training():
    """Retrieve all current user preferences, custom instructions, and voice macros."""
    profile = load_profile()
    
    # Load voice macros
    voice_macros = {}
    if os.path.exists(CONFIG_FILE):
        try:
            import yaml
            with open(CONFIG_FILE, "r") as f:
                cfg = yaml.safe_load(f)
            voice_macros = cfg.get("voice_macros", {})
        except Exception:
            pass
            
    return jsonify({
        "preferences": profile.get("preferences", {}),
        "custom_instructions": profile.get("custom_instructions", []),
        "voice_macros": voice_macros
    })

@app.route("/api/train", methods=["POST"])
def train_system():
    """Train the system with a new preference, instruction, or voice macro."""
    data = request.json or {}
    action_type = data.get("type")
    
    profile = load_profile()
    
    if action_type == "preference":
        key = data.get("key", "").strip()
        value = data.get("value", "").strip()
        if key and value:
            if "preferences" not in profile:
                profile["preferences"] = {}
            profile["preferences"][key] = value
            save_profile(profile)
            return jsonify({"success": True, "message": f"Learned preference: {key} = {value}"})
            
    elif action_type == "instruction":
        text = data.get("text", "").strip()
        if text:
            if "custom_instructions" not in profile:
                profile["custom_instructions"] = []
            profile["custom_instructions"].append(text)
            save_profile(profile)
            return jsonify({"success": True, "message": "Learned behavior instruction."})
            
    elif action_type == "delete_instruction":
        idx = data.get("index")
        if idx is not None and "custom_instructions" in profile:
            try:
                removed = profile["custom_instructions"].pop(int(idx))
                save_profile(profile)
                return jsonify({"success": True, "message": f"Deleted instruction: '{removed}'"})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400
                
    elif action_type == "delete_preference":
        key = data.get("key")
        if key and "preferences" in profile and key in profile["preferences"]:
            del profile["preferences"][key]
            save_profile(profile)
            return jsonify({"success": True, "message": f"Forgotten preference: {key}"})
            
    elif action_type == "voice_macro":
        trigger = data.get("trigger", "").lower().strip()
        command = data.get("command", "").strip()
        if trigger and command:
            try:
                import yaml
                cfg = {}
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, "r") as f:
                        cfg = yaml.safe_load(f) or {}
                if "voice_macros" not in cfg:
                    cfg["voice_macros"] = {}
                cfg["voice_macros"][trigger] = command
                
                with open(CONFIG_FILE, "w") as f:
                    yaml.safe_dump(cfg, f, default_flow_style=False)
                return jsonify({"success": True, "message": f"Registered macro: '{trigger}' -> '{command}'"})
            except Exception as e:
                return jsonify({"success": False, "error": f"Failed to save voice macro config: {e}"}), 500
                
    elif action_type == "delete_voice_macro":
        trigger = data.get("trigger")
        if trigger:
            try:
                import yaml
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, "r") as f:
                        cfg = yaml.safe_load(f) or {}
                    if "voice_macros" in cfg and trigger in cfg["voice_macros"]:
                        del cfg["voice_macros"][trigger]
                        with open(CONFIG_FILE, "w") as f:
                            yaml.safe_dump(cfg, f, default_flow_style=False)
                        return jsonify({"success": True, "message": f"Deleted macro: '{trigger}'"})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": False, "error": "Invalid training parameters."}), 400

if __name__ == "__main__":
    print("[DASHBOARD API] Starting real-time service on port 5001...")
    app.run(host="127.0.0.1", port=5001, debug=True)
