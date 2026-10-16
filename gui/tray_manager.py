"""
Windows System Tray Integration for J.A.R.V.I.S.
Powered by pystray + Pillow with thread-safe CustomTkinter hooks.
Allows Jarvis to live quietly in the taskbar notification area.
"""

import os
import threading
from PIL import Image
from typing import Callable, Optional

_tray_icon = None
_tray_thread = None

ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons", "jarvis.ico")


def create_tray_icon(
    on_show_hud: Callable[[], None],
    on_toggle_privacy: Callable[[], None],
    on_start_focus: Callable[[], None],
    on_run_maid: Callable[[], None],
    on_exit: Callable[[], None],
    on_toggle_sentry: Optional[Callable[[], None]] = None,
    on_log_water: Optional[Callable[[], None]] = None,
):
    """
    Build and start the system tray icon in a dedicated daemon thread.
    """
    global _tray_icon, _tray_thread
    try:
        import pystray
        from pystray import MenuItem as item

        if not os.path.exists(ICON_PATH):
            print(f"[TRAY WARNING] Icon file not found: {ICON_PATH}")
            return None

        image = Image.open(ICON_PATH)

        menu_items = [
            item("👁️  Show / Hide HUD", lambda icon, item: on_show_hud()),
            item("🛡️  Toggle Privacy Mode", lambda icon, item: on_toggle_privacy()),
            item("🎯  Start 25m Focus Session", lambda icon, item: on_start_focus()),
            item("🧹  Run Maid Protocol", lambda icon, item: on_run_maid()),
        ]

        if on_toggle_sentry:
            menu_items.append(item("🚨  Toggle Sentry Guard", lambda icon, item: on_toggle_sentry()))
        if on_log_water:
            menu_items.append(item("💧  Log Glass of Water", lambda icon, item: on_log_water()))

        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(item("❌  Exit J.A.R.V.I.S.", lambda icon, item: on_exit()))

        menu = pystray.Menu(*menu_items)

        _tray_icon = pystray.Icon(
            name="JARVIS",
            icon=image,
            title="J.A.R.V.I.S. - Artificial Intelligence System",
            menu=menu
        )

        def _run():
            try:
                _tray_icon.run()
            except Exception as e:
                print(f"[TRAY RUN ERROR]: {e}")

        _tray_thread = threading.Thread(target=_run, daemon=True, name="TrayThread")
        _tray_thread.start()
        print("[SYSTEM TRAY] J.A.R.V.I.S. system tray icon active in notification area.")
        return _tray_icon

    except Exception as e:
        print(f"[TRAY INIT ERROR]: {e}")
        return None


def stop_tray_icon():
    """Stop the system tray loop cleanly."""
    global _tray_icon
    if _tray_icon:
        try:
            _tray_icon.stop()
        except Exception:
            pass
        _tray_icon = None
