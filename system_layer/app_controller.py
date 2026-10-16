"""
JARVIS Universal App & Game Controller
Supports fuzzy matching across installed Windows applications,
Start Menu shortcuts, and active processes.
"""

import os
import subprocess
import difflib
import psutil
from typing import Dict, Optional, Tuple

COMMON_ALIASES = {
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "chrome": "Google Chrome",
    "google": "Google Chrome",
    "browser": "Google Chrome",
    "edge": "Microsoft Edge",
    "calculator": "calc",
    "calc": "calc",
    "notepad": "notepad",
    "paint": "mspaint",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "powershell": "powershell",
    "explorer": "explorer",
    "file explorer": "explorer",
    "files": "explorer",
    "settings": "start ms-settings:",
    "task manager": "taskmgr",
    "taskmgr": "taskmgr",
    "spotify": "Spotify",
    "discord": "Discord",
    "steam": "Steam",
    "youtube": "https://www.youtube.com",
    "whatsapp": "whatsapp:",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://www.x.com",
    "x": "https://www.x.com",
    "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com",
    "netflix": "https://www.netflix.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com"
}

_app_cache: Optional[Dict[str, str]] = None


def get_installed_apps() -> Dict[str, str]:
    """
    Scan Start Menu and common application folders to build
    a map of lowercase app name -> launchable path (.lnk / .exe).
    """
    global _app_cache
    if _app_cache is not None:
        return _app_cache

    apps = {}

    fast_dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs")
    ]

    for d in fast_dirs:
        if not os.path.exists(d):
            continue
        try:
            for root, dirs, files in os.walk(d):
                for f in files:
                    if f.lower().endswith((".lnk", ".exe")):
                        base_name = os.path.splitext(f)[0]
                        clean_key = base_name.lower().strip()
                        if clean_key not in apps or f.lower().endswith(".lnk"):
                            apps[clean_key] = os.path.join(root, f)
        except Exception:
            pass

    _app_cache = apps
    return apps


def find_app_path(target_name: str) -> Optional[Tuple[str, str]]:
    """
    Resolve requested name to (display_name, target_path) using aliases and fuzzy matching.
    """
    clean_target = target_name.lower().strip()
    apps = get_installed_apps()

    # 1. Direct Alias Check
    if clean_target in COMMON_ALIASES:
        resolved = COMMON_ALIASES[clean_target]
        res_lower = resolved.lower()
        # If the resolved alias matches a discovered shortcut path, use the actual file path!
        if res_lower in apps:
            return (resolved, apps[res_lower])
        for k, p in apps.items():
            if res_lower in k:
                return (resolved, p)
        return (resolved, resolved)

    # 2. Exact match in installed apps
    if clean_target in apps:
        return (clean_target.title(), apps[clean_target])

    # 3. Substring match
    for key, path in apps.items():
        if clean_target in key:
            return (key.title(), path)

    # 4. Fuzzy match using difflib
    candidates = list(apps.keys())
    matches = difflib.get_close_matches(clean_target, candidates, n=1, cutoff=0.55)
    if matches:
        matched_key = matches[0]
        return (matched_key.title(), apps[matched_key])

    return None


def open_app(name: str) -> str:
    """
    Launch requested application or game.
    """
    clean = name.strip()
    if not clean:
        return "Please specify an application to open, Sir."

    # Protocol handlers (Spotify, WhatsApp, etc.)
    if clean.lower() in ("spotify", "music"):
        try:
            os.startfile("spotify:")
            return "Opening Spotify, Sir."
        except Exception:
            pass

    if clean.lower() == "whatsapp":
        try:
            os.startfile("whatsapp:")
            return "Opening WhatsApp, Sir."
        except Exception:
            import webbrowser
            webbrowser.open("https://web.whatsapp.com")
            return "Opening WhatsApp Web, Sir."

    match = find_app_path(clean)

    if match:
        display_name, target = match
        try:
            if target.startswith("start "):
                os.system(target)
                return f"Opening {display_name}, Sir."
            elif target.startswith("http://") or target.startswith("https://"):
                import webbrowser
                webbrowser.open(target)
                return f"Opening {display_name}, Sir."
            elif os.path.exists(target):
                os.startfile(target)
                return f"Opening {display_name}, Sir."
            else:
                try:
                    os.startfile(target)
                    return f"Opening {display_name}, Sir."
                except Exception:
                    pass
                import webbrowser
                webbrowser.open(f"https://www.{clean}.com")
                return f"Opening {display_name}, Sir."
        except Exception as e:
            return f"Error launching {display_name}: {e}"

    # Fallback to browser for web applications
    try:
        import webbrowser
        webbrowser.open(f"https://www.{clean}.com")
        return f"Opening {clean.title()}, Sir."
    except Exception:
        pass

    return f"I couldn't locate {clean} on your system, Sir."


def close_app(name: str) -> str:
    """
    Terminate matching running processes by name or executable.
    """
    clean = name.lower().strip()
    if not clean:
        return "Please specify an application to close, Sir."

    # Process keyword mappings
    term_keys = [clean]
    if clean in COMMON_ALIASES:
        term_keys.append(COMMON_ALIASES[clean].lower())

    killed_count = 0
    killed_names = set()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pname = proc.info['name'].lower()
            if any(k in pname for k in term_keys):
                proc.terminate()
                killed_count += 1
                killed_names.add(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed_count > 0:
        names_str = ", ".join(killed_names)
        return f"Closed {names_str}, Sir."

    return f"I could not find an active process for {name}, Sir."