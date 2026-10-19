"""
J.A.R.V.I.S. (Just A Rather Very Intelligent System) - Sci-Fi HUD Application
Coordinator & Main Shell integrating modular telemetry, reactor canvas, media,
task directives, environment, quick controls, and console panels.
"""

import sys
import os
import socket

# Ensure project root is in sys.path when running gui.py directly
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Single-instance lock to prevent duplicate voices / dual instances
_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    _lock_socket.bind(("127.0.0.1", 54321))
    _lock_socket.listen(1)
except OSError:
    print("\n" + "=" * 60)
    print(" [WARNING] J.A.R.V.I.S. is already running in another process!")
    print(" Only one instance is allowed at a time to prevent dual voices.")
    print("=" * 60 + "\n")
    sys.exit(0)

import customtkinter as ctk
import tkinter as tk
import threading
import time
from datetime import datetime

from voice_engine.voice import (
    speak,
    speaking_status
)
from program_finder import build_program_database
import core.assistant as assistant_core
from core.assistant import start_jarvis, command_queue

# Import Modular Panel Components
from gui.panels import (
    TelemetryPanel,
    ReactorPanel,
    MediaPanel,
    TodoPanel,
    EnvironmentPanel,
    ControlsPanel,
)

# Ensure programs database exists
if not os.path.exists("programs.json"):
    threading.Thread(target=build_program_database, daemon=True).start()

# ---------------- COLOR SYSTEM (J.A.R.V.I.S. HUD PALETTE) ----------------

HUD_BG = "#020813"           # Deep space dark navy
PANEL_BG = "#041021"         # Tech panel body
PANEL_BORDER = "#00f0ff"     # Neon cyan border
PANEL_BORDER_DIM = "#0a3656" # Inactive/subtle border
CYAN_BRIGHT = "#00f0ff"      # Primary neon cyan
BLUE_ACCENT = "#0088ff"      # Core reactor blue
GREEN_ACCENT = "#00ff66"     # Online status emerald green
TEXT_WHITE = "#ffffff"       # Crisp primary text
TEXT_CYAN = "#a5f3fc"        # High-legibility soft cyan
TEXT_MUTED = "#3a7a94"       # Subdued tech text

FONT_TITLE = ("Consolas", 11, "bold")
FONT_VALUE = ("Consolas", 12, "bold")
FONT_LABEL = ("Consolas", 10)
FONT_SMALL = ("Consolas", 9)
FONT_HEADER = ("Consolas", 22, "bold")
FONT_CONSOLE = ("Consolas", 11)

# ---------------- ROOT APPLICATION SETUP ----------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.title("J.A.R.V.I.S. - Artificial Intelligence System")
app.geometry("1440x900")
app.configure(fg_color=HUD_BG)

is_fullscreen = True
app.attributes("-fullscreen", True)

def toggle_fullscreen(event=None):
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    app.attributes("-fullscreen", is_fullscreen)

def minimize_window(event=None):
    app.iconify()

def close_app(event=None):
    app.destroy()
    os._exit(0)

app.bind("<F11>", toggle_fullscreen)

# ---------------- ROOT CONTAINER ----------------

root_frame = ctk.CTkFrame(app, fg_color=HUD_BG, corner_radius=0)
root_frame.pack(fill="both", expand=True, padx=14, pady=10)

# ============================================================
# 1. TOP HEADER BAR
# ============================================================

header_frame = ctk.CTkFrame(root_frame, fg_color="transparent", height=48)
header_frame.pack(fill="x", side="top", pady=(0, 6))

# Left: Pulse beacon + Logo
header_left = ctk.CTkFrame(header_frame, fg_color="transparent")
header_left.pack(side="left", anchor="w")

beacon_canvas = tk.Canvas(header_left, width=24, height=24, bg=HUD_BG, highlightthickness=0)
beacon_canvas.pack(side="left", padx=(0, 8))
beacon_ring = beacon_canvas.create_oval(3, 3, 21, 21, outline=CYAN_BRIGHT, width=2)
beacon_core = beacon_canvas.create_oval(8, 8, 16, 16, fill=CYAN_BRIGHT, outline="")

logo_label = ctk.CTkLabel(
    header_left,
    text="J.A.R.V.I.S.",
    font=FONT_HEADER,
    text_color=TEXT_WHITE
)
logo_label.pack(side="left")

version_label = ctk.CTkLabel(
    header_left,
    text="  - v7.4.2 -",
    font=FONT_SMALL,
    text_color=TEXT_MUTED
)
version_label.pack(side="left")

# Center: Subtitle
header_center = ctk.CTkLabel(
    header_frame,
    text="ARTIFICIAL INTELLIGENCE  •  YOUR PERSONAL ASSISTANT",
    font=("Consolas", 11, "bold"),
    text_color=CYAN_BRIGHT
)
header_center.pack(side="left", expand=True)

# Right: Window Management Buttons
header_right = ctk.CTkFrame(header_frame, fg_color="transparent")
header_right.pack(side="right", anchor="e")

def make_win_btn(parent, text, cmd, hover_color="#005577"):
    return ctk.CTkButton(
        parent,
        text=text,
        width=32,
        height=28,
        fg_color="#061f36",
        hover_color=hover_color,
        border_color="#00b4d8",
        border_width=1,
        corner_radius=4,
        font=("Consolas", 12, "bold"),
        text_color=CYAN_BRIGHT,
        command=cmd
    )

btn_min = make_win_btn(header_right, "—", minimize_window)
btn_min.pack(side="left", padx=2)

btn_max = make_win_btn(header_right, "□", toggle_fullscreen)
btn_max.pack(side="left", padx=2)

btn_close = make_win_btn(header_right, "✕", close_app, hover_color="#881122")
btn_close.pack(side="left", padx=2)

# Divider line
header_divider = ctk.CTkFrame(root_frame, fg_color=PANEL_BORDER_DIM, height=1)
header_divider.pack(fill="x", side="top", pady=(0, 8))

# ============================================================
# 2. MAIN 3-COLUMN DASHBOARD GRID
# ============================================================

main_grid = ctk.CTkFrame(root_frame, fg_color="transparent")
main_grid.pack(fill="both", expand=True, side="top")

main_grid.grid_columnconfigure(0, weight=3) # Left column
main_grid.grid_columnconfigure(1, weight=6) # Center column
main_grid.grid_columnconfigure(2, weight=3) # Right column
main_grid.grid_rowconfigure(0, weight=1)

# Panel Factory used across modules
def create_hud_panel(parent, title_text, icon="▪"):
    frame = ctk.CTkFrame(
        parent,
        fg_color=PANEL_BG,
        border_color=PANEL_BORDER,
        border_width=1,
        corner_radius=8
    )
    title_bar = ctk.CTkFrame(frame, fg_color="transparent", height=28)
    title_bar.pack(fill="x", padx=12, pady=(8, 4))

    icon_lbl = ctk.CTkLabel(
        title_bar,
        text=f"{icon} ",
        font=FONT_TITLE,
        text_color=CYAN_BRIGHT
    )
    icon_lbl.pack(side="left")

    title_lbl = ctk.CTkLabel(
        title_bar,
        text=title_text,
        font=FONT_TITLE,
        text_color=TEXT_WHITE
    )
    title_lbl.pack(side="left")

    return frame

# ------------------------------------------------------------
# RIGHT COLUMN & SYSTEM NOTIFICATIONS (Initialized early for callbacks)
# ------------------------------------------------------------

right_col = ctk.CTkFrame(main_grid, fg_color="transparent")
right_col.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=0)

# System Notifications Panel
notif_panel = create_hud_panel(right_col, "SYSTEM NOTIFICATIONS", icon="🔔")
notif_panel.pack(fill="both", expand=True)

notif_box = ctk.CTkTextbox(
    notif_panel,
    fg_color="transparent",
    text_color=TEXT_CYAN,
    font=FONT_SMALL,
    border_width=0
)
notif_box.pack(fill="both", expand=True, padx=8, pady=4)
notif_box.insert("end", "• JARVIS: All systems operational. [10:42]\n")
notif_box.insert("end", "• JARVIS: 41 Modular Skills verified. [10:41]\n")
notif_box.insert("end", "• JARVIS: Ready for your command. [10:40]\n")
notif_box.configure(state="disabled")

def add_notification(text):
    now_str = datetime.now().strftime("%H:%M")
    notif_box.configure(state="normal")
    notif_box.insert("0.0", f"• JARVIS: {text} [{now_str}]\n")
    notif_box.configure(state="disabled")

# ------------------------------------------------------------
# 3. BOTTOM SECTION: TERMINAL CONSOLE & COMMAND INPUT DOCK
# ------------------------------------------------------------

bottom_section = ctk.CTkFrame(root_frame, fg_color="transparent")
bottom_section.pack(fill="x", side="bottom", pady=(6, 0))

terminal_panel = ctk.CTkFrame(
    bottom_section,
    fg_color=PANEL_BG,
    border_color=PANEL_BORDER,
    border_width=1,
    corner_radius=8,
    height=100
)
terminal_panel.pack(fill="x", pady=(0, 6))

term_header = ctk.CTkFrame(terminal_panel, fg_color="transparent", height=20)
term_header.pack(fill="x", padx=10, pady=(4, 0))

term_lbl = ctk.CTkLabel(
    term_header,
    text="TERMINAL CONSOLE // SYSTEM OUTPUT",
    font=("Consolas", 9, "bold"),
    text_color=CYAN_BRIGHT
)
term_lbl.pack(side="left")

textbox = ctk.CTkTextbox(
    terminal_panel,
    height=80,
    font=FONT_CONSOLE,
    fg_color="transparent",
    text_color=CYAN_BRIGHT,
    border_width=0
)
textbox.pack(fill="both", expand=True, padx=10, pady=(2, 6))
textbox.insert("end", "J.A.R.V.I.S.: System online.\nJ.A.R.V.I.S.: Ready to assist you.\nJ.A.R.V.I.S.: What can I do for you today?\n")
textbox.configure(state="disabled")

# Typewriter Engine
typewriter_job = None
typewriter_active = False

def stop_typewriter():
    global typewriter_job, typewriter_active
    typewriter_active = False
    if typewriter_job is not None:
        try:
            app.after_cancel(typewriter_job)
        except Exception:
            pass
        typewriter_job = None

def type_writer(text, index=0):
    global typewriter_job, typewriter_active
    if not typewriter_active:
        typewriter_job = None
        return

    if index < len(text):
        textbox.configure(state="normal")
        textbox.insert("end", text[index])
        textbox.see("end")
        textbox.configure(state="disabled")
        typewriter_job = app.after(10, type_writer, text, index + 1)
        return

    textbox.configure(state="normal")
    textbox.insert("end", "\n")
    textbox.see("end")
    textbox.configure(state="disabled")
    typewriter_active = False
    typewriter_job = None

def update_display(text):
    global typewriter_active
    stop_typewriter()
    textbox.configure(state="normal")
    textbox.insert("end", "\nJ.A.R.V.I.S.: ")
    textbox.see("end")
    textbox.configure(state="disabled")
    typewriter_active = True
    type_writer(str(text), 0)
    add_notification(str(text)[:45])

# ------------------------------------------------------------
# CENTER COLUMN: Modular ReactorPanel Component
# ------------------------------------------------------------

reactor_panel = ReactorPanel(main_grid, app, notif_callback=add_notification)

def set_status(color_or_name):
    reactor_panel.set_status(color_or_name)

# ------------------------------------------------------------
# LEFT COLUMN: Modular TelemetryPanel & Active Skills List
# ------------------------------------------------------------

left_col = ctk.CTkFrame(main_grid, fg_color="transparent")
left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

# PANEL 1: Telemetry Panel
telemetry_panel = TelemetryPanel(left_col, create_hud_panel)

# PANEL 2: Active Skills Panel
skills_panel = create_hud_panel(left_col, "ACTIVE SKILLS", icon="⚙")
skills_panel.pack(fill="both", expand=True)

skills_content = ctk.CTkScrollableFrame(skills_panel, fg_color="transparent")
skills_content.pack(fill="both", expand=True, padx=6, pady=4)

active_skills_list = [
    ("AI / Chat", "Online"),
    ("System Control", "Online"),
    ("File Manager", "Online"),
    ("Web / Browser", "Online"),
    ("Music / Spotify", "Online"),
    ("YouTube Search", "Online"),
    ("Weather", "Online"),
    ("Coding / Dev Copilot", "Online"),
    ("Vision / Camera", "Online"),
    ("Hand Gesture Control", "Online"),
    ("Volume Control", "Online"),
    ("Brightness Control", "Online"),
    ("Task Planner", "Online"),
    ("Memory Engine", "Online"),
    ("Live Web Search", "Online"),
    ("Proactive Reminders", "Online"),
    ("Desktop Auto-Pilot", "Online"),
    ("Focus Guard", "Online"),
    ("Neural Voice (Offline)", "Online"),
    ("Sound FX Engine", "Online"),
    ("Maid Protocol", "Online"),
    ("Custom Protocols", "Online"),
    ("Voice Ghostwriter", "Online"),
    ("Media Swiss Knife", "Online"),
    ("System Tray Hub", "Online"),
    ("Sentry Guard", "Online"),
    ("Deep Research", "Online"),
    ("Stark Taskmaster", "Online"),
    ("Wellness Protocol", "Online"),
    ("Mark VII Diagnostics", "Online"),
    ("Web Navigator", "Online"),
    ("Executive Briefing", "Online"),
    ("Voice Biometrics", "Online"),
]

for skill_name, status_text in active_skills_list:
    row = ctk.CTkFrame(skills_content, fg_color="transparent", height=24)
    row.pack(fill="x", pady=2, padx=4)

    name_lbl = ctk.CTkLabel(
        row,
        text=f"▪ {skill_name}",
        font=FONT_LABEL,
        text_color=TEXT_CYAN
    )
    name_lbl.pack(side="left")

    stat_frame = ctk.CTkFrame(row, fg_color="transparent")
    stat_frame.pack(side="right")

    dot = ctk.CTkLabel(stat_frame, text="●", font=("Consolas", 10), text_color=GREEN_ACCENT)
    dot.pack(side="left", padx=(0, 4))

    stat_lbl = ctk.CTkLabel(stat_frame, text=status_text, font=FONT_SMALL, text_color=GREEN_ACCENT)
    stat_lbl.pack(side="left")

# ------------------------------------------------------------
# RIGHT COLUMN PANELS: Environment, Controls, Media, Todos
# ------------------------------------------------------------

# Insert panels before the notification panel in right_col
env_panel = EnvironmentPanel(right_col, create_hud_panel, city="Vadodara")
env_panel.panel.pack(fill="x", pady=(0, 8), before=notif_panel)

controls_panel = ControlsPanel(
    right_col,
    create_hud_panel,
    notif_callback=add_notification,
    display_callback=update_display,
    status_callback=set_status
)
controls_panel.panel.pack(fill="x", pady=(0, 8), before=notif_panel)

media_panel = MediaPanel(right_col, create_hud_panel, notif_callback=add_notification)
media_panel.panel.pack(fill="x", pady=(0, 8), before=notif_panel)

todo_panel = TodoPanel(right_col, create_hud_panel, notif_callback=add_notification)
todo_panel.panel.pack(fill="x", pady=(0, 8), before=notif_panel)

# Command Input Dock Row (Bottom of HUD)
dock_row = ctk.CTkFrame(bottom_section, fg_color="transparent")
dock_row.pack(fill="x")

voice_active = [True]
def toggle_voice_btn():
    voice_active[0] = not voice_active[0]
    if voice_active[0]:
        mic_btn.configure(fg_color="#062f48", border_color=CYAN_BRIGHT, text_color=CYAN_BRIGHT)
        mic_lbl.configure(text="Voice Active", text_color=CYAN_BRIGHT)
        set_status("yellow")
        add_notification("Voice recognition activated.")
    else:
        mic_btn.configure(fg_color="#360a14", border_color="#ff4444", text_color="#ff4444")
        mic_lbl.configure(text="Voice Muted", text_color="#ff4444")
        set_status("red")
        add_notification("Voice recognition muted.")

mic_frame = ctk.CTkFrame(dock_row, fg_color="transparent")
mic_frame.pack(side="left", padx=(0, 10))

mic_btn = ctk.CTkButton(
    mic_frame,
    text="🎤",
    width=38,
    height=36,
    corner_radius=18,
    font=("Segoe UI Emoji", 14),
    fg_color="#062f48",
    border_color=CYAN_BRIGHT,
    border_width=1,
    text_color=CYAN_BRIGHT,
    command=toggle_voice_btn
)
mic_btn.pack(side="left", padx=(0, 6))

mic_lbl = ctk.CTkLabel(mic_frame, text="Voice Active", font=FONT_LABEL, text_color=CYAN_BRIGHT)
mic_lbl.pack(side="left")

input_frame = ctk.CTkFrame(
    dock_row,
    fg_color=PANEL_BG,
    border_color=PANEL_BORDER,
    border_width=1,
    corner_radius=6
)
input_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))

ctk.CTkLabel(input_frame, text="  > ", font=FONT_VALUE, text_color=CYAN_BRIGHT).pack(side="left")

command_entry = ctk.CTkEntry(
    input_frame,
    placeholder_text="Enter a command... (e.g., 'weather', 'scan', 'time', 'search youtube for jazz', 'open chrome')",
    placeholder_text_color=TEXT_MUTED,
    font=FONT_CONSOLE,
    fg_color="transparent",
    border_width=0,
    text_color=TEXT_WHITE,
    height=36
)
command_entry.pack(side="left", fill="x", expand=True, padx=4)

def submit_command(event=None):
    cmd = command_entry.get().strip()
    if not cmd:
        return
    command_entry.delete(0, "end")
    textbox.configure(state="normal")
    textbox.insert("end", f"\n> {cmd}\n")
    textbox.see("end")
    textbox.configure(state="disabled")
    add_notification(f"Executed: {cmd}")
    command_queue.put(cmd)

command_entry.bind("<Return>", submit_command)

send_btn = ctk.CTkButton(
    dock_row,
    text="SEND ✈",
    font=("Consolas", 11, "bold"),
    width=88,
    height=36,
    fg_color="#062f48",
    hover_color="#006699",
    border_color=CYAN_BRIGHT,
    border_width=1,
    text_color=TEXT_WHITE,
    corner_radius=6,
    command=submit_command
)
send_btn.pack(side="left", padx=(0, 10))

brand_lbl = ctk.CTkLabel(
    dock_row,
    text="J.A.R.V.I.S. PROTOCOL",
    font=("Consolas", 9, "bold"),
    text_color=CYAN_BRIGHT
)
brand_lbl.pack(side="right")

# ============================================================
# 4. PERIODIC TELEMETRY, MEDIA & SCHEDULER UPDATE LOOPS
# ============================================================

def telemetry_update_loop():
    telemetry_panel.update_stats(speaking_status_fn=speaking_status)
    app.after(1500, telemetry_update_loop)

def clock_update_loop():
    env_panel.update_clock()
    app.after(1000, clock_update_loop)

def weather_update_loop():
    env_panel.fetch_weather(app)
    app.after(10 * 60 * 1000, weather_update_loop)

def media_update_loop():
    media_panel.update_display()
    app.after(1500, media_update_loop)

def todo_update_loop():
    todo_panel.refresh()
    app.after(3000, todo_update_loop)

# Trigger initial cycles
app.after(500, telemetry_update_loop)
app.after(200, clock_update_loop)
app.after(1000, weather_update_loop)
app.after(1500, media_update_loop)
app.after(1200, todo_update_loop)
app.after(1000, controls_panel.sync_hardware)

# ============================================================
# 5. ASSISTANT CORE STATUS & BOOTSTRAP CALLBACKS
# ============================================================

def thinking_animation():
    dots = ["Thinking.", "Thinking..", "Thinking..."]
    def animate(idx=0):
        if getattr(assistant_core, "thinking_active", False):
            reactor_panel.status_readout.configure(text=f"STATUS: {dots[idx % 3]}", text_color=BLUE_ACCENT)
            app.after(350, lambda: animate(idx + 1))
    animate()

def startup_sequence():
    messages = [
        "Initializing core neural architecture...",
        "Calibrating radar and audio interfaces...",
        "Loaded 41 modular skills...",
        "All systems online and operational."
    ]
    def run_seq(idx=0):
        if idx < len(messages):
            update_display(messages[idx])
            speak(messages[idx])
            def wait_speech():
                while speaking_status():
                    time.sleep(0.1)
                run_seq(idx + 1)
            threading.Thread(target=wait_speech, daemon=True).start()
        else:
            set_status("yellow")
            start_jarvis(app, set_status, update_display, thinking_animation)

    app.after(500, lambda: run_seq(0))

app.after(1000, startup_sequence)

# ============================================================
# 6. GLOBAL HOTKEY (CTRL + SPACE) SYSTEM-WIDE LISTENER
# ============================================================

hotkey_thread_id = [None]

def toggle_jarvis_window():
    """Toggles JARVIS HUD between foreground focus and minimized."""
    try:
        state = app.state()
        if state == "iconic" or not app.winfo_viewable():
            app.deiconify()
            app.lift()
            app.attributes("-topmost", True)
            app.after(100, lambda: app.attributes("-topmost", False))
            app.focus_force()
            add_notification("HUD restored to foreground via [Ctrl+Space].")
            print("[GLOBAL HOTKEY] JARVIS summoned to foreground!")
            try:
                from wake_word import trigger_wake_word
                from voice_engine.sound_effects import play_fx
                play_fx("wake")
                trigger_wake_word()
            except Exception:
                pass
        else:
            app.iconify()
            print("[GLOBAL HOTKEY] JARVIS minimized.")
    except Exception as e:
        print("[HOTKEY TOGGLE ERROR]:", e)

def start_global_hotkey_listener():
    def hotkey_worker():
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        MOD_CONTROL = 0x0002
        VK_SPACE = 0x20
        HOTKEY_ID = 1001

        hotkey_thread_id[0] = ctypes.windll.kernel32.GetCurrentThreadId()

        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL, VK_SPACE):
            print("[GLOBAL HOTKEY] Could not register Ctrl+Space (may already be in use).")
            return

        print("[GLOBAL HOTKEY] Registered: [Ctrl + Space] to summon / minimize JARVIS anywhere!")

        try:
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                    app.after(0, toggle_jarvis_window)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            print("[HOTKEY WORKER ERROR]:", e)
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    t = threading.Thread(target=hotkey_worker, daemon=True)
    t.start()

def on_app_closing():
    try:
        from gui.tray_manager import stop_tray_icon
        stop_tray_icon()
    except Exception:
        pass
    try:
        if hotkey_thread_id[0]:
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(hotkey_thread_id[0], 0x0012, 0, 0)
    except Exception:
        pass
    app.destroy()
    os._exit(0)

app.protocol("WM_DELETE_WINDOW", on_app_closing)
start_global_hotkey_listener()

# ============================================================
# 7. WINDOWS SYSTEM TRAY NOTIFICATION AREA INTEGRATION
# ============================================================

def setup_tray():
    try:
        from gui.tray_manager import create_tray_icon

        def _tray_show():
            app.after(0, toggle_jarvis_window)

        def _tray_privacy():
            try:
                from wake_word import set_privacy_mute, is_privacy_muted
                new_state = not is_privacy_muted()
                set_privacy_mute(new_state)
                add_notification(f"Privacy Mode {'engaged' if new_state else 'disengaged'} via Tray.")
            except Exception:
                pass

        def _tray_focus():
            try:
                from background_tasks.focus_guard import start_focus_session
                start_focus_session(25)
                add_notification("25-minute Focus Session launched via Tray.")
            except Exception:
                pass

        def _tray_maid():
            def _worker():
                try:
                    from system_layer.maid_controller import run_maid_protocol
                    res = run_maid_protocol('both')
                    add_notification(res)
                except Exception:
                    pass
            threading.Thread(target=_worker, daemon=True).start()

        def _tray_sentry():
            try:
                from background_tasks.sentry_guard import is_sentry_active, start_sentry_mode, stop_sentry_mode
                if is_sentry_active():
                    res = stop_sentry_mode()
                else:
                    res = start_sentry_mode()
                add_notification(res)
            except Exception as e:
                add_notification(f"Sentry error: {e}")

        def _tray_water():
            try:
                from background_tasks.wellness_monitor import log_water_intake
                res = log_water_intake(1)
                add_notification(res)
            except Exception as e:
                add_notification(f"Hydration error: {e}")

        def _tray_exit():
            try:
                from gui.tray_manager import stop_tray_icon
                stop_tray_icon()
            except Exception:
                pass
            app.after(0, close_app)

        create_tray_icon(
            on_show_hud=_tray_show,
            on_toggle_privacy=_tray_privacy,
            on_start_focus=_tray_focus,
            on_run_maid=_tray_maid,
            on_exit=_tray_exit,
            on_toggle_sentry=_tray_sentry,
            on_log_water=_tray_water
        )
    except Exception as e:
        print("[TRAY SETUP ERROR]:", e)

setup_tray()

# ---------------- APPLICATION MAINLOOP ----------------

if __name__ == "__main__":
    app.mainloop()
