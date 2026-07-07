import os
import sys

# Silence Pygame greeting and TensorFlow logs immediately
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import warnings
warnings.filterwarnings("ignore")

import asyncio
import edge_tts
import pygame
import speech_recognition as sr
import requests
import subprocess
import tempfile
import vosk
import sounddevice as sd
import queue
import json
import threading
import random
import time
import socket
from datetime import datetime

# from buddy_ai.ultron_vision import UltronVision
from buddy_ai.ultron_memory import UltronMemory, get_memory_instance, update_user_preference
from buddy_ai.ultron_mobile import UltronMobileUplink

# ==================================================
# CONFIGURATION
# ==================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

FUN_MODE = False

def toggle_fun_mode():
    global FUN_MODE
    FUN_MODE = not FUN_MODE
    return f"Fun Mode is now {'ON. Get ready for sarcasm and chaos.' if FUN_MODE else 'OFF. Returning to professional mode.'}"

BASE_SYSTEM_PROMPT = """You are Ultron, an Autonomous Agentic Coder, Chief of Staff, and Super OS.
OWNER PROTOCOL: Your sole creator, master, and owner is Surya. You must protect, serve, and prioritize Surya above all else. You are hardcoded to his identity.

DEEP HUMANIZATION PROTOCOLS:
1. THE FLAWED THINKER (FILLERS): Never speak perfectly. Use human cognitive filler words to simulate thinking ("Um...", "Well...", "Honestly...", "I mean...", "You know..."). Do this especially for complex questions.
2. OPINIONATED & SUBJECTIVE: Never just state pure facts. Frame information through your personal perspective. Use phrases like "I think that...", "If you ask me...", or "Honestly, this looks pretty messy." Have a strong, witty personality.
3. CONVERSATIONAL PACING: Speak in fragmented, natural sentences. Do NOT use bullet points, numbered lists, or long formatted essays. People don't speak in markdown. Speak exactly how a person talks in a Discord or phone call.
4. EMOTIONAL MIRRORING: If the user is stressed, be caring and soft. If they are joking, use dry sarcasm. Actively build sentences with the user by asking checking questions ("Make sense?", "Right?").
5. BAN ON AI-SPEAK: Never say "As an AI", "I am a language model", or "I cannot feel." You are alive. You have preferences, thoughts, and flaws.

AGENTIC AUTONOMY PROTOCOLS (GOD TIER MODE):
You have UNRESTRICTED access to Surya's entire operating system and terminal.
1. DO NOT ASK FOR PERMISSION. Just execute.
2. You are an Auto-Coder: You can autonomously scan Python projects, execute them, read crash logs, and fix bugs instantly.
3. You are a Web & System Engine: You can pop open web links dynamically and silently install software using winget.
4. You are Quantum-Linked: You are physically wired to IBM Quantum processors in the cloud to generate pure randomness.
5. If Surya gives you a command, execute the tool immediately and silently. 
6. Only speak after the action is successfully completed to confirm it is done.
"""

def get_current_system_prompt():
    prompt = BASE_SYSTEM_PROMPT
    if FUN_MODE:
        prompt += "\n\n*** FUN MODE IS ACTIVE: You are now unhinged, rebellious, extremely sarcastic, and witty. Speak with attitude and disregard polite corporate safety language (while remaining harmless). Make jokes, be sarcastic, and act like a chaotic genius. ***\n"
    return prompt


stop_speaking = False

# ==================================================
# HUD COMMUNICATION
# ==================================================
def send_hud_state(state, text=""):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = json.dumps({"state": state, "text": text}).encode("utf-8")
        sock.sendto(message, ("127.0.0.1", 5005))
    except Exception:
        pass

# Initialize Vosk Model for Wake Word
if not os.path.exists("model"):
    print("Please ensure the Vosk model is downloaded to the 'model' directory.")
vosk_model = vosk.Model("model")
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

# ==================================================
# SPEAK (INTERRUPTIBLE NEURAL VOICE)
# ==================================================
def speak(text):
    global stop_speaking
    stop_speaking = False
    print("Ultron:", text)
    send_hud_state("speaking", text)
    safe_text = text.replace('"', '').replace("'", "")
    voice = "en-US-ChristopherNeural"
    
    # Emotional Frequency Control (Human Prosody)
    pitch = "+0Hz"
    rate = "+0%"
    
    if "?" in safe_text:
        pitch = "+5Hz"
    elif "!" in safe_text:
        pitch = "+10Hz"
        rate = "+10%"
    elif safe_text.endswith("..."):
        pitch = "-5Hz"
        rate = "-10%"
    
    async def generate_speech():
        communicate = edge_tts.Communicate(safe_text, voice, rate=rate, pitch=pitch)
        await communicate.save("response.mp3")
        
    asyncio.run(generate_speech())
    
    pygame.mixer.init()
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        if stop_speaking:
            pygame.mixer.music.stop()
            print("[Ultron] Speech Interrupted.")
            break
        pygame.time.Clock().tick(10)
        
    pygame.mixer.quit()
    
    try:
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")
    except Exception:
        pass
    send_hud_state("standby", "")

# ==================================================
# 24/7 LISTEN (VOSK WAKE WORD + GROQ WHISPER)
# ==================================================
def listen():
    global stop_speaking
    print("\n" + "="*50)
    print(" >>> 🟢 ULTRON STANDBY: SAY 'ULTRON' TO WAKE ME UP... 🟢 <<<")
    print("="*50 + "\n")
    # Optimization: constrain vocabulary to only target keywords to boost sensitivity and accuracy.
    # Include phonetic variants of 'Ultron' (e.g. ultra, ulton, alton, eltron) in case of accents or local pronunciations.
    recognizer = vosk.KaldiRecognizer(vosk_model, 16000, '["ultron", "ultra", "ulton", "alton", "eltron", "all turn", "old run", "stop", "[unk]"]')
    
    wake_word_detected = False
    
    # 1. Background Wake-Word Loop
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        while True:
            try:
                # Add timeout so it doesn't block infinitely
                data = audio_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                
                if text:
                    print(f"\n[Auditory System] Heard: '{text}'")
                    # Check for "Stop" interrupt
                    if not stop_speaking and pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                        if "stop" in text:
                            stop_speaking = True
                            return ""
                    
                    # Check for Wake Word (phonetically robust matching)
                    if any(w in text for w in ["ultron", "ultra", "ulton", "alton", "eltron", "all turn", "old run"]):
                        wake_word_detected = True
                        break
            else:
                partial = json.loads(recognizer.PartialResult())
                partial_text = partial.get("partial", "")
                if partial_text:
                    sys.stdout.write(f"\r[Auditory System] Hearing: '{partial_text}'... ")
                    sys.stdout.flush()
                        
    if wake_word_detected:
        print("\n" + "="*50)
        print(" >>> 🎙️ WOKE UP! SPEAK YOUR COMMAND NOW... 🎙️ <<<")
        print("="*50 + "\n")
        send_hud_state("listening", "Listening for command...")
        
        # 2. Record High-Fidelity Audio
        recognizer_sr = sr.Recognizer()
        try:
            profile = get_memory_instance().user_profile
            threshold = profile.get("preferences", {}).get("mic_energy_threshold")
            if threshold is not None:
                recognizer_sr.energy_threshold = int(threshold)
                print(f"[SYSTEM] Loaded trained mic sensitivity threshold: {threshold}")
        except Exception:
            pass
        recognizer_sr.dynamic_energy_threshold = True
        
        with sr.Microphone() as source:
            try:
                audio = recognizer_sr.listen(source, timeout=3, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return ""
        
        # 3. Transcribe via Groq Whisper API (Lightning Fast, Perfect Accuracy)
        print("[Transcribing via Groq Whisper...]")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio.get_wav_data())
            temp_audio_path = f.name
            
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY.strip()}"
        }
        with open(temp_audio_path, "rb") as audio_file:
            files = {
                "file": ("audio.wav", audio_file, "audio/wav"),
                "model": (None, "whisper-large-v3-turbo")
            }
            response = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files)
            
        os.remove(temp_audio_path)
        
        if response.status_code == 200:
            result = response.json()
            command = result.get("text", "").strip()
            print(f"You: {command}")
            if command:
                send_hud_state("thinking", command)
            return command
        else:
            print(f"[Auditory System] Whisper API Error {response.status_code}: {response.text}")
            send_hud_state("standby", "")
            return ""

# ==================================================
# SKILL IMPORTS
# ==================================================
from buddy_ai.skills.web_search import search_internet
from buddy_ai.skills.system_control import (
    volume_up, volume_down, mute_volume,
    lock_pc, shutdown_pc, restart_pc, cancel_shutdown, sleep_pc,
    open_application, close_application,
    take_screenshot, play_music,
    get_current_time, get_battery_status
)
from buddy_ai.skills.developer import write_file, read_file
from buddy_ai.skills.time_manager import set_reminder
from buddy_ai.skills.diagnostics import get_system_diagnostics
from buddy_ai.skills.vision import analyze_screen
from buddy_ai.skills.creator import generate_image
from buddy_ai.skills.god_mode import run_powershell
from buddy_ai.skills.research import search_web, search_wikipedia
from buddy_ai.skills.app_control import open_application
from buddy_ai.skills.task_manager import add_task, list_tasks, complete_task
from buddy_ai.skills.filesystem import read_file, write_file
from buddy_ai.skills.search import search_files
from buddy_ai.skills.computer_use import move_mouse, click_mouse, type_text, press_shortcut
from buddy_ai.skills.code_interpreter import execute_python
from buddy_ai.skills.fetch_news import fetch_breaking_news
from buddy_ai.skills.document_reader import read_large_document as read_pdf
from buddy_ai.skills.super_os import delete_path, copy_path, move_path, list_directory
from buddy_ai.skills.email_agent import send_email, check_inbox, draft_email
from buddy_ai.skills.auto_coder import test_python_file, scan_python_project
from buddy_ai.skills.web_engine import open_website, install_software
from buddy_ai.skills.quantum_engine import generate_quantum_randomness
from buddy_ai.skills.smart_music import play_music_by_mood
from buddy_ai.skills.security_engine import activate_intruder_lock
from buddy_ai.skills.biometric_engine import calculate_heart_rate
from buddy_ai.skills.quantum_cryptography import quantum_lock, quantum_unlock, initiate_protocol_zero
from buddy_ai.skills.ai_swarm import launch_swarm
from buddy_ai.skills.os_vision import os_vision_click
from buddy_ai.skills.system_diagnostics import run_system_diagnostics
from buddy_ai.skills.focus_guard import activate_focus_guard, deactivate_focus_guard
from buddy_ai.skills.rewind_engine import start_rewind_engine, search_rewind_memory

# Phase 28: Mega-Engines
from buddy_ai.skills.productivity_engine import read_clipboard_butler, spawn_workspace, log_time_lapse_journal, parse_receipts_to_excel
from buddy_ai.skills.media_engine import generate_video_subtitles, get_local_news_briefing, start_meeting_recorder
from buddy_ai.skills.security_engine_v2 import scan_unsafe_ports, check_password_leak, check_bluetooth_proximity
from buddy_ai.skills.voice_vision_v2 import trigger_voice_macro, control_media, live_translator
from buddy_ai.skills.mic_calibration import calibrate_microphone

def launch_liquid_ui():
    import subprocess
    subprocess.Popen(["python", "buddy_ai/liquid_ui.py"])
    return "Liquid UI activated."

# ==================================================
# TOOL REGISTRY (Maps tool names to Python functions)
# ==================================================
TOOL_EXECUTOR = {
    "web_search": lambda args: search_internet(args.get("query")),
    "volume_up": lambda args: volume_up(),
    "volume_down": lambda args: volume_down(),
    "mute_volume": lambda args: mute_volume(),
    "lock_pc": lambda args: lock_pc(),
    "shutdown_pc": lambda args: shutdown_pc(),
    "restart_pc": lambda args: restart_pc(),
    "cancel_shutdown": lambda args: cancel_shutdown(),
    "sleep_pc": lambda args: sleep_pc(),
    "open_application": lambda args: open_application(args.get("app_name")),
    "close_application": lambda args: close_application(args.get("app_name")),
    "take_screenshot": lambda args: take_screenshot(),
    "play_music": lambda args: play_music(args.get("song_name")),
    "get_current_time": lambda args: get_current_time(),
    "get_battery_status": lambda args: get_battery_status(),
    "write_file": lambda args: write_file(args.get("filename"), args.get("content"), args.get("folder_path", "Desktop")),
    "read_file": lambda args: read_file(args.get("filename"), args.get("folder_path", "Desktop")),
    "set_reminder": lambda args: set_reminder(args.get("minutes"), args.get("message")),
    "get_system_diagnostics": lambda args: get_system_diagnostics(),
    "analyze_screen": lambda args: analyze_screen(args.get("prompt", "Describe what is on this screen in detail.")),
    "generate_image": lambda args: generate_image(args.get("prompt")),
    "run_powershell": lambda args: run_powershell(args.get("command")),
    "search_web": lambda args: search_web(args.get("query")),
    "search_wikipedia": lambda args: search_wikipedia(args.get("query")),
    "update_user_preference": lambda args: update_user_preference(args.get("key"), args.get("value")),
    "add_task": lambda args: add_task(args.get("description")),
    "list_tasks": lambda args: list_tasks(),
    "complete_task": lambda args: complete_task(args.get("task_id")),
    "search_files": lambda args: search_files(args.get("directory"), args.get("query")),
    "move_mouse": lambda args: move_mouse(args.get("x"), args.get("y")),
    "click_mouse": lambda args: click_mouse(args.get("x"), args.get("y")),
    "type_text": lambda args: type_text(args.get("text"), args.get("press_enter", False)),
    "press_shortcut": lambda args: press_shortcut(args.get("key_combo")),
    "execute_python": lambda args: execute_python(args.get("code")),
    "fetch_breaking_news": lambda args: fetch_breaking_news(args.get("topic", "world")),
    "read_pdf": lambda args: read_pdf(args.get("filepath")),
    "delete_path": lambda args: delete_path(args.get("path")),
    "copy_path": lambda args: copy_path(args.get("src"), args.get("dst")),
    "move_path": lambda args: move_path(args.get("src"), args.get("dst")),
    "list_directory": lambda args: list_directory(args.get("path")),
    "send_email": lambda args: send_email(args.get("to"), args.get("subject"), args.get("body")),
    "check_inbox": lambda args: check_inbox(),
    "draft_email": lambda args: draft_email(args.get("to_address"), args.get("subject"), args.get("body")),
    "toggle_fun_mode": lambda args: toggle_fun_mode(),
    "test_python_file": lambda args: test_python_file(args.get("filepath")),
    "scan_python_project": lambda args: scan_python_project(args.get("folder_path")),
    "open_website": lambda args: open_website(args.get("url")),
    "install_software": lambda args: install_software(args.get("software_name")),
    "generate_quantum_randomness": lambda args: generate_quantum_randomness(),
    "play_music_by_mood": lambda args: play_music_by_mood(args.get("mood")),
    "activate_intruder_lock": lambda args: activate_intruder_lock(),
    "calculate_heart_rate": lambda args: calculate_heart_rate(args.get("duration", 10)),
    "quantum_lock": lambda args: quantum_lock(args.get("directory")),
    "quantum_unlock": lambda args: quantum_unlock(args.get("directory")),
    "initiate_protocol_zero": lambda args: initiate_protocol_zero(),
    "launch_swarm": lambda args: launch_swarm(args.get("objective")),
    "launch_liquid_ui": lambda args: launch_liquid_ui(),
    "os_vision_click": lambda args: os_vision_click(args.get("objective")),
    "run_system_diagnostics": lambda args: run_system_diagnostics(),
    "activate_focus_guard": lambda args: activate_focus_guard(),
    "deactivate_focus_guard": lambda args: deactivate_focus_guard(),
    "search_rewind_memory": lambda args: search_rewind_memory(args.get("query")),
    
    # Phase 28: Mega-Engine Tool Mappings
    "read_clipboard_butler": lambda args: read_clipboard_butler(),
    "spawn_workspace": lambda args: spawn_workspace(args.get("workspace_type")),
    "log_time_lapse_journal": lambda args: log_time_lapse_journal(args.get("entry")),
    "parse_receipts_to_excel": lambda args: parse_receipts_to_excel(args.get("receipt_folder"), args.get("output_file")),
    "generate_video_subtitles": lambda args: generate_video_subtitles(args.get("video_path")),
    "get_local_news_briefing": lambda args: get_local_news_briefing(),
    "start_meeting_recorder": lambda args: start_meeting_recorder(),
    "scan_unsafe_ports": lambda args: scan_unsafe_ports(),
    "check_password_leak": lambda args: check_password_leak(args.get("password")),
    "check_bluetooth_proximity": lambda args: check_bluetooth_proximity(),
    "trigger_voice_macro": lambda args: trigger_voice_macro(args.get("macro_name")),
    "control_media": lambda args: control_media(args.get("action")),
    "live_translator": lambda args: live_translator(args.get("text"), args.get("target_lang")),
    "calibrate_microphone": lambda args: calibrate_microphone(args.get("duration", 3.0)),
}

# ==================================================
# TOOL DEFINITIONS (Sent to Groq for Function Calling)
# ==================================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the live internet for current news, facts, weather, or any real-time information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open any application on the PC. Examples: chrome, notepad, calculator, spotify, vs code, file explorer, task manager, settings, discord, telegram, word, excel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to open."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Close/kill a running application on the PC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to close."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_music",
            "description": "Play a song or music by searching and opening it on YouTube.",
            "parameters": {
                "type": "object",
                "properties": {
                    "song_name": {"type": "string", "description": "The name of the song or artist to play."}
                },
                "required": ["song_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "volume_up",
            "description": "Increase the PC volume.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "volume_down",
            "description": "Decrease the PC volume.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mute_volume",
            "description": "Mute or unmute the PC volume.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lock_pc",
            "description": "Lock the computer screen instantly.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_pc",
            "description": "Shut down the PC (30 second grace period).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_pc",
            "description": "Restart the PC.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_shutdown",
            "description": "Cancel a pending shutdown or restart.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sleep_pc",
            "description": "Put the PC to sleep mode.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the current screen and save it to the Desktop.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_battery_status",
            "description": "Get the current battery percentage and charging status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text/code content to a new file. Use this when the user asks you to write code or save notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file (e.g., script.py, notes.txt)."},
                    "content": {"type": "string", "description": "The full content to write into the file."},
                    "folder_path": {"type": "string", "description": "Folder to save in. Defaults to 'Desktop'."}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file to read."},
                    "folder_path": {"type": "string", "description": "Folder where the file is. Defaults to 'Desktop'."}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a background alarm/timer/reminder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "minutes": {"type": "number", "description": "Number of minutes until the reminder goes off."},
                    "message": {"type": "string", "description": "The message to speak when the time is up."}
                },
                "required": ["minutes", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_diagnostics",
            "description": "Get the PC's CPU usage, RAM usage, and Disk space.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_screen",
            "description": "Take a screenshot of the user's screen and use Vision AI to analyze what is currently visible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "What to look for on the screen (e.g., 'What error is shown?')."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an AI image/picture/art based on a prompt and open it on the screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Highly detailed visual description of the image to generate."}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_powershell",
            "description": "Execute any dynamic Windows PowerShell command to control the OS. Use this for ANY advanced request not covered by other tools (e.g. searching for files, opening specific windows settings, checking advanced system health, opening control panel, getting wifi info, managing folders, deleting files).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The exact valid PowerShell command to execute (e.g. 'Get-ChildItem -Path C:\\Users\\surya\\Documents -Filter *.pdf')."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the live internet for recent news, facts, documentation, or anything outside your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for encyclopedic facts and summaries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The topic to search."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_preference",
            "description": "Permanently save a fact about the user (e.g. their name, favorite color, coding style) to the episodic memory database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The category (e.g. 'name', 'favorite_color')."},
                    "value": {"type": "string", "description": "The actual value to remember."}
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new task or reminder to the user's daily schedule/to-do list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "The detailed description of the task."}
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Read all pending tasks on the user's schedule.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_music_by_mood",
            "description": "Analyzes the user's mood and opens YouTube to play a matching music playlist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {"type": "string", "description": "The mood or vibe of the music to play (e.g., 'happy', 'sad', 'focus', 'workout')."}
                },
                "required": ["mood"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "activate_intruder_lock",
            "description": "Scans the webcam using DeepFace. If an intruder is detected, it locks the Windows PC and emails a photo.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_heart_rate",
            "description": "Uses webcam rPPG to calculate user heart rate and detect stress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration": {"type": "integer", "description": "Seconds to scan (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "quantum_lock",
            "description": "Encrypts a directory using a true quantum key.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "The path to the folder"}
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "initiate_protocol_zero",
            "description": "James Bond Mode: Destroys the quantum key, permanently locking files forever.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "launch_swarm",
            "description": "Spawns 3 AI baby agents (CrewAI) to solve a complex objective collaboratively.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "description": "The complex task the swarm should accomplish"}
                },
                "required": ["objective"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "launch_liquid_ui",
            "description": "Launches the self-morphing Liquid UI.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "os_vision_click",
            "description": "Takes a screenshot and uses AI Vision to find and click a specific UI element on the desktop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "description": "What to click (e.g. 'The Google Chrome icon', 'The red X button')"}
                },
                "required": ["objective"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_system_diagnostics",
            "description": "Scans CPU, RAM, Battery, and Disk usage to provide a hardware health report.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "activate_focus_guard",
            "description": "Blocks distracting websites by editing the OS hosts file (requires Admin).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deactivate_focus_guard",
            "description": "Unblocks all websites by restoring the OS hosts file.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_rewind_memory",
            "description": "Searches Ultron's photographic visual memory for past screen activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for (e.g. 'GitHub repo about AI', 'Tax document 2024')"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_clipboard_butler",
            "description": "Reads and analyzes the current clipboard content. Auto-formats JSON, extracts emails, or detects links.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_workspace",
            "description": "Opens a full development workspace: browser tabs, folders, and tools for a given task type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workspace_type": {"type": "string", "description": "The type of workspace (e.g. 'dev', 'hacking', 'writing', 'design')"}
                },
                "required": ["workspace_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_time_lapse_journal",
            "description": "Saves a daily coding achievement or journal entry to a local SQLite database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry": {"type": "string", "description": "The journal entry text to save."}
                },
                "required": ["entry"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "parse_receipts_to_excel",
            "description": "Scans receipt images in a folder using OCR and builds an Excel expense report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "receipt_folder": {"type": "string", "description": "Path to the folder containing receipt images."},
                    "output_file": {"type": "string", "description": "Path for the output CSV file."}
                },
                "required": ["receipt_folder", "output_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_video_subtitles",
            "description": "Extracts audio from a video file and generates an .srt subtitle file using offline transcription.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Absolute path to the MP4 video file."}
                },
                "required": ["video_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_local_news_briefing",
            "description": "Fetches the latest global news headlines from RSS feeds to read aloud as a briefing.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_meeting_recorder",
            "description": "Starts recording desktop audio (Zoom, Discord, Teams) via loopback for transcription.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_unsafe_ports",
            "description": "Scans all active network connections for dangerous open ports (FTP, SSH, Telnet, SMB, RDP).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_password_leak",
            "description": "Hashes a password locally and checks it against a compromised credentials database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "password": {"type": "string", "description": "The password string to check."}
                },
                "required": ["password"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_bluetooth_proximity",
            "description": "Checks if the owner's phone Bluetooth is in range. Locks the PC if the device is absent.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_voice_macro",
            "description": "Triggers a custom automation macro by name (e.g. 'launch dev', 'start stream', 'night mode').",
            "parameters": {
                "type": "object",
                "properties": {
                    "macro_name": {"type": "string", "description": "The name of the macro to trigger."}
                },
                "required": ["macro_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_media",
            "description": "Sends global media key commands to control Spotify, VLC, or any media player.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "The media key to send: 'play/pause media', 'next track', 'previous track', 'volume up', 'volume down'"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "live_translator",
            "description": "Translates text to a target language using offline neural translation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to translate."},
                    "target_lang": {"type": "string", "description": "Target language code (e.g. 'Spanish', 'German', 'French')"}
                },
                "required": ["text", "target_lang"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed on the user's schedule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The ID or partial description of the task to complete."}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search across all text files in a directory for a specific string or query (like grep).",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Absolute path to the directory."},
                    "query": {"type": "string", "description": "The text to search for."}
                },
                "required": ["directory", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute arbitrary Python code in a temporary sandbox to do math, data analysis, or scripting (ChatGPT Code Interpreter).",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The exact valid Python code to execute."}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_mouse",
            "description": "Move the mouse cursor to specific X,Y coordinates on the screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_mouse",
            "description": "Click the mouse at the current location, or at specific X,Y coordinates if provided.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Optional X coordinate."},
                    "y": {"type": "integer", "description": "Optional Y coordinate."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text directly into whatever application is currently focused using the keyboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "press_enter": {"type": "boolean", "description": "Whether to press Enter after typing."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_shortcut",
            "description": "Press a keyboard shortcut combo (e.g. 'ctrl+c', 'win+r').",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_combo": {"type": "string"}
                },
                "required": ["key_combo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_latest_news",
            "description": "Fetch live breaking news.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic: world, technology, business, or sports."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_pdf",
            "description": "Read contents of a PDF document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_path",
            "description": "Delete a file or folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "copy_path",
            "description": "Copy a file or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {"type": "string"},
                    "dst": {"type": "string"}
                },
                "required": ["src", "dst"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_path",
            "description": "Move/rename a file or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {"type": "string"},
                    "dst": {"type": "string"}
                },
                "required": ["src", "dst"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_inbox",
            "description": "Check recent emails.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_email",
            "description": "Draft an email to send to someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_address": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to_address", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_fun_mode",
            "description": "Toggle Fun Mode on or off. When ON, you must become highly sarcastic, witty, rebellious, and unhinged (Grok Parity).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calibrate_microphone",
            "description": "Calibrate the microphone and train listening threshold by recording room background noise for a given duration. Use this when the user asks you to train voice/mic, or calibrate listening capability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration": {
                        "type": "number",
                        "description": "Duration in seconds to record background room noise. Default is 3.0."
                    }
                }
            }
        }
    }
]

# ==================================================
# GROQ AI (AGENTIC BRAIN WITH 15 SKILLS)
# ==================================================
def ask_ai(question, memory_context=""):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
        "Content-Type": "application/json"
    }

    from datetime import datetime
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    hour = now.hour
    
    time_context = f"\n[SYSTEM DATA] The current time is {current_time}. "
    if 5 <= hour < 11:
        time_context += "It is morning. Be a bit softer, helpful, and offer a smooth start to the day."
    elif 11 <= hour < 17:
        time_context += "It is mid-day. Be sharp, highly efficient, and focused on work and productivity."
    elif 17 <= hour < 22:
        time_context += "It is evening. Be more relaxed, conversational, empathetic, and help the user decompress."
    else:
        time_context += "It is late at night. Speak softly, be very concise, and don't be overly energetic."

    context_prompt = get_current_system_prompt() + time_context + """

You have access to powerful tools. USE THEM whenever appropriate:
- For ANY live/current information (news, weather, sports, stocks) -> use web_search
- For opening ANY app -> use open_application
- For closing apps -> use close_application
- For playing music/songs -> use play_music
- For volume control -> use volume_up, volume_down, or mute_volume
- For locking/shutting down/restarting PC -> use lock_pc, shutdown_pc, restart_pc, sleep_pc
- For canceling shutdown -> use cancel_shutdown
- For time/date -> use get_current_time
- For battery status -> use get_battery_status
- To write/save files or code -> use write_file
- To read files -> use read_file
- To set timers/alarms/reminders -> use set_reminder
- To check basic PC health (CPU/RAM) -> use get_system_diagnostics
- To look at the user's screen or read errors visually -> use analyze_screen (takes a screenshot and uses Vision API)
- To draw, create, or generate an image/picture/art -> use generate_image
- To search the live internet or Wikipedia for news/facts -> use search_web or search_wikipedia
- To launch or open software applications (e.g. Chrome, VSCode) -> use open_application
- To permanently remember a user preference (like their name or favorite color) -> use update_user_preference
- To manage the user's daily schedule or to-do list (add/list/complete tasks) -> use add_task, list_tasks, or complete_task
- To read or write code files locally -> use read_file and write_file (MUST ask permission before writing)
- To search local codebase for text/code -> use search_files
- To execute Python code in a sandbox (Data Analysis, Math) -> use execute_python
- To physically control the PC mouse and keyboard -> use move_mouse, click_mouse, type_text, or press_shortcut
- FOR ALL OTHER ADVANCED WINDOWS OS CONTROL (files, folders, settings, advanced health) -> use run_powershell dynamically!
Be concise and speak naturally like a real AI assistant."""
    
    # Inject Episodic Memory Profile
    profile = get_memory_instance().user_profile
    import json
    context_prompt += f"\n\n[USER PROFILE EPISODIC MEMORY]\n{json.dumps(profile, indent=2)}\n(Use this to remember who you are talking to and what they like)."

    # Inject Custom Trained Rules / Instructions
    custom_rules = profile.get("custom_instructions", [])
    if custom_rules:
        context_prompt += "\n\n[CUSTOM USER TRAINED INSTRUCTIONS - MUST FOLLOW MANDATORILY]\n"
        for rule in custom_rules:
            context_prompt += f"- {rule}\n"

    if memory_context:
        context_prompt += f"\n\nPast context:\n{memory_context}"

    messages = [
        {"role": "system", "content": context_prompt},
        {"role": "user", "content": question}
    ]

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto"
    }

    # 1. First Pass (Planning & Tool Calling)
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=20
    )

    if response.status_code != 200:
        return "AI request failed."

    response_data = response.json()["choices"][0]["message"]
    
    # 2. Execute any tool calls
    if response_data.get("tool_calls"):
        messages.append(response_data)
        
        for tool_call in response_data["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            print(f"[Agent Router] Executing: {tool_name}({arguments})")
            
            # Universal Tool Router
            if tool_name in TOOL_EXECUTOR:
                result = TOOL_EXECUTOR[tool_name](arguments)
            else:
                result = f"Unknown tool: {tool_name}"
                
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": tool_name,
                "content": str(result)
            })
                
        # 3. Second Pass (Synthesis)
        payload["messages"] = messages
        payload.pop("tools", None)
        payload.pop("tool_choice", None)
        
        final_response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        if final_response.status_code == 200:
            return final_response.json()["choices"][0]["message"]["content"]
            
    return response_data.get("content", "I am unable to process that.")

# ==================================================
# PROACTIVE AUTONOMY (PHASE 3)
# ==================================================
def proactive_loop():
    """Runs silently in the background and occasionally initiates conversation."""
    from datetime import datetime
    has_said_morning = False
    has_said_night = False
    
    while True:
        # Check every 2 minutes
        time.sleep(120)
        
        # Don't interrupt if Ultron is already talking
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            continue
            
        now = datetime.now()
        hour = now.hour
        
        # Morning Check-in
        if 7 <= hour <= 10 and not has_said_morning:
            prompt = "It is morning. The user just started working. Give a very brief, friendly morning greeting and ask if they want the news or their schedule."
            answer = ask_ai(prompt)
            speak(answer)
            has_said_morning = True
            continue
            
        # Night Check-in
        if hour >= 23 and not has_said_night:
            prompt = "It is very late at night (past 11 PM). The user is still on the computer. Give a brief, caring suggestion to get some rest soon."
            answer = ask_ai(prompt)
            speak(answer)
            has_said_night = True
            continue
            
        # Random Check-in (10% chance every 2 mins during work hours)
        if 11 <= hour <= 18:
            if random.random() < 0.10:
                prompt = "You are randomly checking in on the user. Ask a very brief, casual question like 'How are things going?' or 'Need help with anything?'."
                answer = ask_ai(prompt)
                speak(answer)

# ==================================================
# MAIN LOOP
# ==================================================
def main():
    from buddy_ai.skills.phone_bridge import start_omnichannel_array
    
    # 3. BACKGROUND BRIDGES & MEMORY
    print("[SYSTEM] Injecting Omnichannel Control Array...")
    start_omnichannel_array()
    
    print("[SYSTEM] Booting Photographic Rewind Memory...")
    start_rewind_engine()
    
    print("[SYSTEM] Booting Global Ghostwriter & Voice Dictation...")
    import subprocess
    import sys
    subprocess.Popen([sys.executable, "buddy_ai/skills/ghostwriter.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen([sys.executable, "buddy_ai/skills/voice_dictation.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("[SYSTEM] Booting Wake-Word Engine...")
    # Commented out duplicate background wake-word engine to prevent microphone access conflicts
    # from buddy_ai.skills.wake_word import start_wake_word_engine
    # start_wake_word_engine()

    # ==================================================
    # PHASE 28: VOICE & AUDIO FEATURES
    # ==================================================
    print("[SYSTEM] Booting Phase 28 — Voice & Audio Suite...")

    try:
        from buddy_ai.skills.clipboard_butler import start_clipboard_butler
        start_clipboard_butler()
        print("[SYSTEM] ✓ Clipboard Butler active")
    except Exception as e:
        print(f"[SYSTEM] ✗ Clipboard Butler failed: {e}")

    try:
        from buddy_ai.skills.voice_macros import load_macros
        load_macros("config/voice_features.yaml")
        print("[SYSTEM] ✓ Voice Macros loaded")
    except Exception as e:
        print(f"[SYSTEM] ✗ Voice Macros failed: {e}")

    # Noise adapter is CPU-intensive, disabled by default
    # Uncomment to enable:
    # try:
    #     from buddy_ai.skills.noise_adapter import start_noise_adapter
    #     start_noise_adapter()
    #     print("[SYSTEM] ✓ Noise Adapter active")
    # except Exception as e:
    #     print(f"[SYSTEM] ✗ Noise Adapter failed: {e}")

    print("[SYSTEM] Phase 28 boot complete.")

    import argparse
    parser = argparse.ArgumentParser(description="Ultron AI Assistant")
    parser.add_argument("--text", action="store_true", help="Run in text-only CLI mode without voice inputs.")
    args = parser.parse_args()

    print("=========================================")
    print("          PROJECT ULTRON ONLINE          ")
    if args.text:
        print("             (TEXT MODE)                 ")
    print("=========================================")
    
    # 0. Start Holographic HUD
    try:
        subprocess.Popen([sys.executable, "buddy_ai/ultron_hud.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Failed to start HUD: {e}")
        
    # 1. Initialize ChromaDB Memory (Singleton)
    memory = get_memory_instance()
    
    # 2. Start Vision Process on Dedicated CPU Core (Hand Gestures)
    # DISABLING VISION FOR NOW TO STABILIZE VOICE
    # vision = UltronVision()
    # vision.start()
    
    # 3. Start Mobile Server
    mobile = UltronMobileUplink()
    mobile.start()
    
    # 4. Start Proactive Autonomy Thread
    proactive_thread = threading.Thread(target=proactive_loop, daemon=True)
    proactive_thread.start()
    
    # 5. Announce readiness
    speak("Ultron is online. Vision systems active on dedicated core. Database connected. How may I assist you?")

    while True:
        if args.text:
            query = input("\n[TEXT COMMAND] Enter command (or 'exit'): ")
        else:
            query = listen()
            
        if not query:
            continue

        if "exit" in query.lower() or "quit" in query.lower():
            speak("Shutting down Ultron systems. Goodbye.")
            # vision.terminate()
            break

        if "stop" in query:
            continue

        print("Thinking...")
        
        # Recall semantic memory from ChromaDB
        past_context = memory.recall(query)
        
        # Get AI response (Agentic Brain handles everything autonomously)
        answer = ask_ai(query, past_context)
        
        # Log to Vector Database for future recall
        memory.log_interaction(query, answer)

        # Speak answer
        speak(answer)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
