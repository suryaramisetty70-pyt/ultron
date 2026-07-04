"""
pc_agent.py — Production PC Control Agent
Extends BaseAgent for full Buddy ecosystem compatibility.
Windows-safe, async-compatible, subprocess-based control.
"""

import asyncio
import logging
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Optional

from core.base_agent import BaseAgent
from core.event_bus import EventBus
from core.command_queue import CommandQueue

logger = logging.getLogger(__name__)

# ── Windows-only imports (guarded) ───────────────────────────────────────────
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    _PYCAW_AVAILABLE = True
except ImportError:
    _PYCAW_AVAILABLE = False
    logger.warning("[PCAgent] pycaw not installed — volume control disabled. pip install pycaw comtypes")

try:
    import pyautogui
    pyautogui.FAILSAFE = True   # Move mouse to corner to abort
    _PYAUTOGUI_AVAILABLE = True
except ImportError:
    _PYAUTOGUI_AVAILABLE = False
    logger.warning("[PCAgent] pyautogui not installed — hotkey fallback disabled. pip install pyautogui")


# ── App path registry (Windows defaults + user-overridable) ──────────────────
DEFAULT_APP_PATHS: dict[str, list[str]] = {
    "vscode": [
        r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        r"C:\Program Files\Microsoft VS Code\Code.exe",
        r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
    ],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{user}\AppData\Local\Google\Chrome\Application\chrome.exe",
    ],
    "whatsapp": [
        r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
        r"C:\Users\{user}\AppData\Roaming\WhatsApp\WhatsApp.exe",
        # Microsoft Store version via explorer shell
    ],
    "notepad":    [r"C:\Windows\System32\notepad.exe"],
    "calculator": [r"C:\Windows\System32\calc.exe"],
    "explorer":   [r"C:\Windows\explorer.exe"],
    "cmd":        [r"C:\Windows\System32\cmd.exe"],
    "powershell": [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"],
    "word": [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
    ],
    "excel": [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
    ],
    "spotify": [
        r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    ],
    "discord": [
        r"C:\Users\{user}\AppData\Local\Discord\Update.exe",
    ],
    "taskmanager": [r"C:\Windows\System32\Taskmgr.exe"],
    "settings":    ["ms-settings:"],   # UWP URI
}

VOLUME_STEP = 0.05   # 5% per up/down command


class PCAgent(BaseAgent):
    """
    Production PC Control Agent.
    Safe, modular, async-compatible, Windows-native.
    """

    AGENT_ID = "pc_agent"

    HANDLED_INTENTS = [
        "open_app",
        "close_app",
        "open_website",
        "shutdown_pc",
        "restart_pc",
        "volume_up",
        "volume_down",
        "mute",
        "unmute",
        "toggle_mute",
        "open_folder",
        "create_folder",
        "launch_vscode",
        "launch_chrome",
        "launch_whatsapp",
        "get_volume",
        "set_volume",
        "lock_pc",
        "sleep_pc",
        "list_running_apps",
        "open_settings",
        "open_task_manager",
    ]

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(
        self,
        event_bus: EventBus,
        command_queue: CommandQueue,
        custom_app_paths: Optional[dict] = None,
        safe_mode: bool = True,
    ):
        """
        Args:
            custom_app_paths: Override or extend DEFAULT_APP_PATHS.
                              e.g. {"vscode": [r"D:\\Code\\Code.exe"]}
            safe_mode: If True, shutdown/restart require confirmation payload flag.
        """
        super().__init__(
            agent_id=self.AGENT_ID,
            event_bus=event_bus,
            command_queue=command_queue,
        )
        self.safe_mode = safe_mode
        self._app_paths: dict[str, list[str]] = {**DEFAULT_APP_PATHS}
        if custom_app_paths:
            self._app_paths.update(custom_app_paths)

        # Resolve {user} placeholder
        self._username = os.environ.get("USERNAME", os.environ.get("USER", ""))
        self._resolve_user_placeholders()

        # Volume endpoint (cached)
        self._volume_endpoint: Optional[object] = None

    def _resolve_user_placeholders(self) -> None:
        resolved = {}
        for key, paths in self._app_paths.items():
            resolved[key] = [p.replace("{user}", self._username) for p in paths]
        self._app_paths = resolved

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def on_start(self) -> None:
        for intent in self.HANDLED_INTENTS:
            self.register_intent(intent, self._dispatch_intent)
        if _PYCAW_AVAILABLE:
            await asyncio.get_event_loop().run_in_executor(None, self._init_volume)
        logger.info("[PCAgent] started — %d intents registered", len(self.HANDLED_INTENTS))

    async def on_stop(self) -> None:
        self._volume_endpoint = None
        logger.info("[PCAgent] stopped")

    # ── BaseAgent entrypoint ──────────────────────────────────────────────────

    async def handle_command(self, command: dict) -> dict:
        intent = command.get("intent", "")
        payload = command.get("payload", {})
        try:
            result = await self._dispatch_intent(intent, payload)
            result["agent"] = self.AGENT_ID
            return result
        except Exception as exc:
            logger.exception("[PCAgent] unhandled error in intent '%s'", intent)
            return {"success": False, "error": str(exc), "agent": self.AGENT_ID}

    # ── Dispatcher ────────────────────────────────────────────────────────────

    async def _dispatch_intent(self, intent: str, payload: dict) -> dict:
        table = {
            "open_app":          self._handle_open_app,
            "close_app":         self._handle_close_app,
            "open_website":      self._handle_open_website,
            "shutdown_pc":       self._handle_shutdown,
            "restart_pc":        self._handle_restart,
            "volume_up":         self._handle_volume_up,
            "volume_down":       self._handle_volume_down,
            "mute":              self._handle_mute,
            "unmute":            self._handle_unmute,
            "toggle_mute":       self._handle_toggle_mute,
            "open_folder":       self._handle_open_folder,
            "create_folder":     self._handle_create_folder,
            "launch_vscode":     lambda p: self._handle_open_app({"app": "vscode"}),
            "launch_chrome":     lambda p: self._handle_open_app({"app": "chrome"}),
            "launch_whatsapp":   lambda p: self._handle_open_app({"app": "whatsapp"}),
            "get_volume":        self._handle_get_volume,
            "set_volume":        self._handle_set_volume,
            "lock_pc":           self._handle_lock,
            "sleep_pc":          self._handle_sleep,
            "list_running_apps": self._handle_list_apps,
            "open_settings":     lambda p: self._handle_open_app({"app": "settings"}),
            "open_task_manager": lambda p: self._handle_open_app({"app": "taskmanager"}),
        }
        handler = table.get(intent)
        if handler is None:
            return {"success": False, "error": f"Unknown intent: {intent}"}
        return await handler(payload)

    # ══════════════════════════════════════════════════════════════════════════
    # FEATURE HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    # ── 1. Open application ───────────────────────────────────────────────────

    async def _handle_open_app(self, payload: dict) -> dict:
        """
        payload: {"app": "chrome"} or {"app": "notepad"}
        Also accepts {"path": "C:/full/path/to/app.exe"}
        """
        app_name = payload.get("app", "").lower().strip()
        custom_path = payload.get("path", "")

        if custom_path:
            return await self._launch_exe(custom_path)

        if not app_name:
            return {"success": False, "error": "app name or path required"}

        # UWP / ms-settings URI
        paths = self._app_paths.get(app_name, [])
        if paths and paths[0].startswith("ms-"):
            return await self._launch_uri(paths[0])

        # WhatsApp — try Store version if no exe found
        if app_name == "whatsapp":
            exe_result = await self._try_paths(paths)
            if not exe_result["success"]:
                return await self._launch_uri("whatsapp://")
            return exe_result

        if not paths:
            # Last resort: try to open by name via explorer/shell
            return await self._shell_open(app_name)

        return await self._try_paths(paths)

    async def _try_paths(self, paths: list[str]) -> dict:
        """Try each candidate path in order."""
        loop = asyncio.get_event_loop()
        for path in paths:
            if os.path.isfile(path):
                return await self._launch_exe(path)
        return {
            "success": False,
            "error": f"Application not found. Checked: {paths}",
        }

    async def _launch_exe(self, path: str) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._launch_exe_sync, path)

    def _launch_exe_sync(self, path: str) -> dict:
        try:
            subprocess.Popen(
                [path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            return {"success": True, "action": "opened", "path": path}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _launch_uri(self, uri: str) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._shell_exec_sync, uri)

    def _shell_exec_sync(self, target: str) -> dict:
        try:
            os.startfile(target)   # Windows native — handles URIs and files
            return {"success": True, "action": "opened", "target": target}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _shell_open(self, name: str) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._shell_open_sync, name)

    def _shell_open_sync(self, name: str) -> dict:
        try:
            # Try via explorer shell (handles registered app names on Windows)
            subprocess.Popen(
                f'start "" "{name}"',
                shell=True,                     # Required for `start` built-in
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {"success": True, "action": "opened", "app": name}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ── 2. Close application ──────────────────────────────────────────────────

    async def _handle_close_app(self, payload: dict) -> dict:
        """
        payload: {"app": "notepad"}  — uses taskkill (graceful, then force)
        Optional: {"force": true} to hard-kill immediately
        """
        app = payload.get("app", "").strip()
        if not app:
            return {"success": False, "error": "app name required"}

        force = payload.get("force", False)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._kill_process_sync, app, force)

    def _kill_process_sync(self, app: str, force: bool) -> dict:
        # Ensure process name ends with .exe
        proc = app if app.lower().endswith(".exe") else f"{app}.exe"
        try:
            flags = ["/F"] if force else []
            result = subprocess.run(
                ["taskkill", "/IM", proc] + flags,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return {"success": True, "action": "closed", "app": proc}
            # Try without .exe (some processes register differently)
            result2 = subprocess.run(
                ["taskkill", "/IM", app] + flags,
                capture_output=True,
                text=True,
            )
            if result2.returncode == 0:
                return {"success": True, "action": "closed", "app": app}
            return {
                "success": False,
                "error": f"Could not close {app}: {result.stderr.strip()}",
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ── 3. Open website ───────────────────────────────────────────────────────

    async def _handle_open_website(self, payload: dict) -> dict:
        """
        payload: {"url": "https://google.com"}
        Optionally: {"browser": "chrome"} to force a specific browser
        """
        url = payload.get("url", "").strip()
        if not url:
            return {"success": False, "error": "url required"}

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        browser_name = payload.get("browser", "").lower()
        loop = asyncio.get_event_loop()

        if browser_name == "chrome":
            chrome_paths = self._app_paths.get("chrome", [])
            for p in chrome_paths:
                if os.path.isfile(p):
                    return await loop.run_in_executor(
                        None,
                        lambda: self._open_with_browser_sync(p, url),
                    )

        return await loop.run_in_executor(None, self._open_url_sync, url)

    def _open_url_sync(self, url: str) -> dict:
        try:
            webbrowser.open(url)
            return {"success": True, "action": "opened", "url": url}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _open_with_browser_sync(self, browser_path: str, url: str) -> dict:
        try:
            subprocess.Popen(
                [browser_path, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {"success": True, "action": "opened", "url": url, "browser": browser_path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ── 4 & 5. Shutdown / Restart ─────────────────────────────────────────────

    async def _handle_shutdown(self, payload: dict) -> dict:
        """
        payload: {"confirmed": true}  — required in safe_mode
        Optional: {"delay": 30}  seconds (default 0)
        """
        if self.safe_mode and not payload.get("confirmed", False):
            return {
                "success": False,
                "error": "Shutdown requires payload confirmed=True in safe_mode",
            }
        delay = int(payload.get("delay", 0))
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._shutdown_sync, delay)

    def _shutdown_sync(self, delay: int) -> dict:
        try:
            subprocess.run(
                ["shutdown", "/s", "/t", str(delay)],
                check=True,
                capture_output=True,
            )
            return {"success": True, "action": "shutdown_scheduled", "delay": delay}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _handle_restart(self, payload: dict) -> dict:
        """
        payload: {"confirmed": true}  — required in safe_mode
        Optional: {"delay": 0}
        """
        if self.safe_mode and not payload.get("confirmed", False):
            return {
                "success": False,
                "error": "Restart requires payload confirmed=True in safe_mode",
            }
        delay = int(payload.get("delay", 0))
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._restart_sync, delay)

    def _restart_sync(self, delay: int) -> dict:
        try:
            subprocess.run(
                ["shutdown", "/r", "/t", str(delay)],
                check=True,
                capture_output=True,
            )
            return {"success": True, "action": "restart_scheduled", "delay": delay}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ── 6 & 7 & 8. Volume control ─────────────────────────────────────────────

    def _init_volume(self) -> None:
        """Initialise pycaw volume endpoint (runs in executor)."""
        if not _PYCAW_AVAILABLE:
            return
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._volume_endpoint = cast(interface, POINTER(IAudioEndpointVolume))
        except Exception as exc:
            logger.error("[PCAgent] volume init failed: %s", exc)
            self._volume_endpoint = None

    def _get_volume_level(self) -> Optional[float]:
        if self._volume_endpoint is None:
            return None
        try:
            return self._volume_endpoint.GetMasterVolumeLevelScalar()
        except Exception:
            return None

    def _set_volume_level(self, level: float) -> bool:
        if self._volume_endpoint is None:
            return False
        try:
            level = max(0.0, min(1.0, level))
            self._volume_endpoint.SetMasterVolumeLevelScalar(level, None)
            return True
        except Exception:
            return False

    async def _handle_volume_up(self, payload: dict) -> dict:
        step = float(payload.get("step", VOLUME_STEP))
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._volume_change_sync, step)

    async def _handle_volume_down(self, payload: dict) -> dict:
        step = float(payload.get("step", VOLUME_STEP))
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._volume_change_sync, -step)

    def _volume_change_sync(self, delta: float) -> dict:
        if not _PYCAW_AVAILABLE or self._volume_endpoint is None:
            return self._volume_fallback_sync(delta)
        current = self._get_volume_level()
        if current is None:
            return {"success": False, "error": "Cannot read volume"}
        new_level = max(0.0, min(1.0, current + delta))
        if self._set_volume_level(new_level):
            return {
                "success": True,
                "action": "volume_changed",
                "volume_pct": round(new_level * 100),
            }
        return {"success": False, "error": "Failed to set volume"}

    def _volume_fallback_sync(self, delta: float) -> dict:
        """Fallback using nircmd if pycaw unavailable."""
        try:
            # nircmd changesysvolume: range 0–65535
            change = int(delta * 65535)
            subprocess.run(
                ["nircmd", "changesysvolume", str(change)],
                capture_output=True,
                timeout=3,
            )
            return {"success": True, "action": "volume_changed", "method": "nircmd"}
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Volume control unavailable. Install pycaw: pip install pycaw comtypes",
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _handle_mute(self, payload: dict) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._set_mute_sync, True)

    async def _handle_unmute(self, payload: dict) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._set_mute_sync, False)

    async def _handle_toggle_mute(self, payload: dict) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._toggle_mute_sync)

    def _set_mute_sync(self, muted: bool) -> dict:
        if not _PYCAW_AVAILABLE or self._volume_endpoint is None:
            return {"success": False, "error": "pycaw not available"}
        try:
            self._volume_endpoint.SetMute(int(muted), None)
            return {"success": True, "action": "muted" if muted else "unmuted"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _toggle_mute_sync(self) -> dict:
        if not _PYCAW_AVAILABLE or self._volume_endpoint is None:
            return {"success": False, "error": "pycaw not available"}
        try:
            current = self._volume_endpoint.GetMute()
            self._volume_endpoint.SetMute(not current, None)
            state = "unmuted" if current else "muted"
            return {"success": True, "action": state}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _handle_get_volume(self, payload: dict) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_volume_info_sync)

    def _get_volume_info_sync(self) -> dict:
        if not _PYCAW_AVAILABLE or self._volume_endpoint is None:
            return {"success": False, "error": "pycaw not available"}
        try:
            level = self._get_volume_level()
            muted = bool(self._volume_endpoint.GetMute())
            return {
                "success": True,
                "volume_pct": round(level * 100) if level is not None else None,
                "muted": muted,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _handle_set_volume(self, payload: dict) -> dict:
        """payload: {"level": 50}  — 0 to 100"""
        level_pct = payload.get("level", None)
        if level_pct is None:
            return {"success": False, "error": "level (0-100) required"}
        level = float(level_pct) / 100.0
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._set_volume_exact_sync, level)

    def _set_volume_exact_sync(self, level: float) -> dict:
        if not _PYCAW_AVAILABLE or self._volume_endpoint is None:
            return {"success": False, "error": "pycaw not available"}
        if self._set_volume_level(level):
            return {"success": True, "action": "volume_set", "volume_pct": round(level * 100)}
        return {"success": False, "error": "Failed to set volume"}

    # ── 9. Open folder ────────────────────────────────────────────────────────

    async def _handle_open_folder(self, payload: dict) -> dict:
        """
        payload: {"path": "C:/Users/you/Documents"}
        Optional shorthand: {"folder": "documents"} — resolves known folders
        """
        folder_path = payload.get("path", "").strip()
        shorthand = payload.get("folder", "").lower().strip()

        if shorthand and not folder_path:
            folder_path = self._resolve_known_folder(shorthand)
            if not folder_path:
                return {"success": False, "error": f"Unknown folder shorthand: {shorthand}"}

        if not folder_path:
            return {"success": False, "error": "path or folder required"}

        folder = Path(folder_path)
        if not folder.exists():
            return {"success": False, "error": f"Folder does not exist: {folder_path}"}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._open_folder_sync, str(folder))

    def _resolve_known_folder(self, name: str) -> str:
        home = Path.home()
        known = {
            "documents": str(home / "Documents"),
            "downloads": str(home / "Downloads"),
            "desktop":   str(home / "Desktop"),
            "pictures":  str(home / "Pictures"),
            "music":     str(home / "Music"),
            "videos":    str(home / "Videos"),
            "home":      str(home),
            "temp":      os.environ.get("TEMP", "C:\\Windows\\Temp"),
        }
        return known.get(name, "")

    def _open_folder_sync(self, path: str) -> dict:
        try:
            os.startfile(path)
            return {"success": True, "action": "opened", "path": path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ── 10. Create folder ─────────────────────────────────────────────────────

    async def _handle_create_folder(self, payload: dict) -> dict:
        """
        payload: {"path": "C:/Users/you/Projects/NewFolder"}
        Optional: {"open": true}  — open folder after creation
        """
        folder_path = payload.get("path", "").strip()
        if not folder_path:
            return {"success": False, "error": "path required"}

        folder = Path(folder_path)
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            return {"success": False, "error": f"Permission denied: {folder_path}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

        result = {"success": True, "action": "created", "path": str(folder)}

        if payload.get("open", False):
            open_result = await self._handle_open_folder({"path": str(folder)})
            result["opened"] = open_result.get("success", False)

        return result

    # ── Lock / Sleep ──────────────────────────────────────────────────────────

    async def _handle_lock(self, payload: dict) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._lock_sync)

    def _lock_sync(self) -> dict:
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return {"success": True, "action": "locked"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _handle_sleep(self, payload: dict) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sleep_sync)

    def _sleep_sync(self) -> dict:
        try:
            subprocess.run(
                ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"],
                capture_output=True,
            )
            return {"success": True, "action": "sleep"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ── List running apps ─────────────────────────────────────────────────────

    async def _handle_list_apps(self, payload: dict) -> dict:
        """Returns list of running process names."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._list_apps_sync)

    def _list_apps_sync(self) -> dict:
        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            apps = []
            for line in result.stdout.strip().splitlines():
                parts = line.split(",")
                if parts:
                    name = parts[0].strip('"')
                    pid  = parts[1].strip('"') if len(parts) > 1 else ""
                    apps.append({"name": name, "pid": pid})
            return {"success": True, "apps": apps, "count": len(apps)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ── Public utility: add custom app path at runtime ────────────────────────

    def register_app(self, name: str, paths: list[str]) -> None:
        """Register a custom app path. Call before or after start()."""
        self._app_paths[name.lower()] = paths
        logger.info("[PCAgent] registered app '%s' with %d path(s)", name, len(paths))
