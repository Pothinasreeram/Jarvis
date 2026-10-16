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
import random
import math
import pyaudio
import numpy as np
import psutil
import time
from datetime import datetime

from voice_engine.voice import (
    speak,
    speaking_status
)
from memory_layer.memory import load_memory
from program_finder import build_program_database
from system_layer.system_monitor import system_watchdog
from system_layer.weather_controller import get_weather_data
import core.assistant as assistant_core
from core.assistant import start_jarvis, command_queue

# Optional hardware control libraries
try:
    from pycaw.pycaw import AudioUtilities
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

try:
    import screen_brightness_control as sbc
    HAS_SBC = True
except Exception:
    HAS_SBC = False

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
TROUGH_BG = "#061a33"        # Progress bar background

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

app.bind("<Escape>", toggle_fullscreen)
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

# Panel Factory
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
# LEFT COLUMN: System Status & Active Skills
# ------------------------------------------------------------

left_col = ctk.CTkFrame(main_grid, fg_color="transparent")
left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

# PANEL 1: SYSTEM STATUS
status_panel = create_hud_panel(left_col, "SYSTEM STATUS", icon="⚡")
status_panel.pack(fill="x", pady=(0, 8))

status_content = ctk.CTkFrame(status_panel, fg_color="transparent")
status_content.pack(fill="x", padx=12, pady=(4, 10))

# Circular Dual Radial Gauges (CPU & RAM)
TELEMETRY_WIDTH = 260
TELEMETRY_HEIGHT = 96

telemetry_canvas = tk.Canvas(
    status_content,
    width=TELEMETRY_WIDTH,
    height=TELEMETRY_HEIGHT,
    bg="#030c1a",
    highlightthickness=1,
    highlightbackground=PANEL_BORDER_DIM
)
telemetry_canvas.pack(fill="x", pady=(2, 6))

def init_gauge_background(cx, cy, r=32, label="CPU LOAD"):
    telemetry_canvas.create_oval(cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4, outline="#08182b", width=1)
    telemetry_canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=210, extent=-240, style="arc", width=5, outline="#0d2238")
    telemetry_canvas.create_oval(cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8, outline="#091a2e", width=1)
    telemetry_canvas.create_text(cx, cy + 22, text=label, fill="#5a7090", font=("Consolas", 8, "bold"))

# Draw static tracks
init_gauge_background(65, 44, r=32, label="CPU LOAD")
init_gauge_background(195, 44, r=32, label="RAM ALLOC")

# Dynamic gauge elements
cpu_gauge_arc = telemetry_canvas.create_arc(33, 12, 97, 76, start=210, extent=-1, style="arc", width=5, outline=CYAN_BRIGHT)
cpu_gauge_text = telemetry_canvas.create_text(65, 40, text="0%", fill=TEXT_WHITE, font=("Consolas", 11, "bold"))

ram_gauge_arc = telemetry_canvas.create_arc(163, 12, 227, 76, start=210, extent=-1, style="arc", width=5, outline=CYAN_BRIGHT)
ram_gauge_text = telemetry_canvas.create_text(195, 40, text="0%", fill=TEXT_WHITE, font=("Consolas", 11, "bold"))

# Memory Detail Row
ram_detail_lbl = ctk.CTkLabel(
    status_content,
    text="MEM ALLOC: 0.0 / 0.0 GB",
    font=FONT_SMALL,
    text_color=TEXT_CYAN
)
ram_detail_lbl.pack(fill="x", pady=(0, 2))

# Live Network Traffic Speedometer
net_speed_frame = ctk.CTkFrame(status_content, fg_color="transparent")
net_speed_frame.pack(fill="x", pady=2)

net_down_lbl = ctk.CTkLabel(
    net_speed_frame,
    text="↓ 0.0 KB/s",
    font=FONT_SMALL,
    text_color=GREEN_ACCENT
)
net_down_lbl.pack(side="left")

net_up_lbl = ctk.CTkLabel(
    net_speed_frame,
    text="↑ 0.0 KB/s",
    font=FONT_SMALL,
    text_color=CYAN_BRIGHT
)
net_up_lbl.pack(side="right")

# Battery Status Row
batt_row = ctk.CTkFrame(status_content, fg_color="transparent")
batt_row.pack(fill="x", pady=2)

batt_head = ctk.CTkFrame(batt_row, fg_color="transparent")
batt_head.pack(fill="x")

batt_title_lbl = ctk.CTkLabel(
    batt_head,
    text="⚡ BATTERY (AC)",
    font=FONT_SMALL,
    text_color=TEXT_CYAN
)
batt_title_lbl.pack(side="left")

batt_val_lbl = ctk.CTkLabel(
    batt_head,
    text="100%",
    font=FONT_SMALL,
    text_color=TEXT_WHITE
)
batt_val_lbl.pack(side="right")

batt_bar = ctk.CTkProgressBar(
    batt_row,
    fg_color=TROUGH_BG,
    progress_color=CYAN_BRIGHT,
    height=6,
    corner_radius=3
)
batt_bar.pack(fill="x", pady=(2, 0))
batt_bar.set(1.0)

# Badges for network and voice
status_badges = ctk.CTkFrame(status_content, fg_color="transparent")
status_badges.pack(fill="x", pady=(6, 2))

net_badge_lbl = ctk.CTkLabel(
    status_badges,
    text="NET: ONLINE",
    font=FONT_SMALL,
    text_color=GREEN_ACCENT
)
net_badge_lbl.pack(side="left")

voice_badge_lbl = ctk.CTkLabel(
    status_badges,
    text="VOICE: READY",
    font=FONT_SMALL,
    text_color=CYAN_BRIGHT
)
voice_badge_lbl.pack(side="right")

# Focus Guard Active Readout
focus_badge_lbl = ctk.CTkLabel(
    status_content,
    text="FOCUS GUARD: STANDBY",
    font=FONT_SMALL,
    text_color=TEXT_MUTED
)
focus_badge_lbl.pack(fill="x", pady=(2, 1))

sentry_badge_lbl = ctk.CTkLabel(
    status_content,
    text="SENTRY GUARD: STANDBY",
    font=FONT_SMALL,
    text_color=TEXT_MUTED
)
sentry_badge_lbl.pack(fill="x", pady=(1, 1))

wellness_badge_lbl = ctk.CTkLabel(
    status_content,
    text="WELLNESS: ACTIVE (0m | 0/8 💧)",
    font=FONT_SMALL,
    text_color=CYAN_BRIGHT
)
wellness_badge_lbl.pack(fill="x", pady=(1, 2))


# PANEL 2: ACTIVE SKILLS
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
    ("Weather", "Online"),
    ("Coding / Dev", "Online"),
    ("Vision / Camera", "Online"),
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
# CENTER COLUMN: Arc Reactor, Radar Compass, Equalizer & Status
# ------------------------------------------------------------

center_col = ctk.CTkFrame(main_grid, fg_color="transparent")
center_col.grid(row=0, column=1, sticky="nsew", padx=6, pady=0)

# Top Neural Node Sub-Header
center_title = ctk.CTkLabel(
    center_col,
    text="◈  J . A . R . V . I . S .  ◈",
    font=("Consolas", 18, "bold"),
    text_color=CYAN_BRIGHT
)
center_title.pack(side="top", pady=(4, 0))

center_sub = ctk.CTkLabel(
    center_col,
    text="NEURAL CORE ARCHITECTURE // ONLINE",
    font=FONT_SMALL,
    text_color=TEXT_MUTED
)
center_sub.pack(side="top", pady=(0, 4))

# Combined Centerpiece Canvas (Arc Reactor + Radar Compass)
CENTER_WIDTH = 480
CENTER_HEIGHT = 330

hud_canvas = tk.Canvas(
    center_col,
    width=CENTER_WIDTH,
    height=CENTER_HEIGHT,
    bg=HUD_BG,
    highlightthickness=0
)
hud_canvas.pack(fill="both", expand=True, pady=2)

def on_arc_reactor_click(event):
    try:
        from wake_word import trigger_wake_word
        from voice_engine.sound_effects import play_fx
        play_fx("wake")
        trigger_wake_word()
        add_notification("Arc Reactor tapped: Listening mode activated.")
    except Exception as e:
        print("[ARC REACTOR CLICK ERROR]:", e)

hud_canvas.bind("<Button-1>", on_arc_reactor_click)

# Audio Waveform Equalizer Canvas
WAVE_WIDTH = 480
WAVE_HEIGHT = 44

wave_canvas = tk.Canvas(
    center_col,
    width=WAVE_WIDTH,
    height=WAVE_HEIGHT,
    bg="#030c1a",
    highlightthickness=1,
    highlightbackground=PANEL_BORDER_DIM
)
wave_canvas.pack(fill="x", padx=12, pady=(2, 4))

# Status readout
status_readout = ctk.CTkLabel(
    center_col,
    text="STATUS: LISTENING",
    font=("Consolas", 13, "bold"),
    text_color=CYAN_BRIGHT
)
status_readout.pack(side="top", pady=(0, 2))

def trigger_interrupt():
    try:
        from voice_engine.voice import stop_speaking
        stop_speaking()
    except Exception as e:
        print("[GUI INTERRUPT ERROR]:", e)

interrupt_btn = ctk.CTkButton(
    center_col,
    text="■ INTERRUPT [ESC]",
    font=("Consolas", 11, "bold"),
    fg_color="#1a1f2c",
    hover_color="#801b1b",
    border_color="#2a354a",
    border_width=1,
    text_color="#6e82a0",
    height=24,
    width=160,
    corner_radius=6,
    command=trigger_interrupt
)

interrupt_btn.pack(side="top", pady=(0, 4))
app.bind("<Escape>", lambda event: trigger_interrupt())


# ------------------------------------------------------------
# RIGHT COLUMN: Environment, Quick Controls, Notifications
# ------------------------------------------------------------

right_col = ctk.CTkFrame(main_grid, fg_color="transparent")
right_col.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=0)

# PANEL 1: LIVE ENVIRONMENT
env_panel = create_hud_panel(right_col, "LIVE ENVIRONMENT", icon="⛅")
env_panel.pack(fill="x", pady=(0, 8))

env_header = ctk.CTkFrame(env_panel, fg_color="transparent")
env_header.pack(fill="x", padx=12, pady=(0, 2))

env_location = ctk.CTkLabel(env_header, text="Vadodara, India", font=FONT_SMALL, text_color=TEXT_MUTED)
env_location.pack(side="left")

live_clock_lbl = ctk.CTkLabel(env_header, text="--:--:--", font=FONT_VALUE, text_color=CYAN_BRIGHT)
live_clock_lbl.pack(side="right")

env_content = ctk.CTkFrame(env_panel, fg_color="transparent")
env_content.pack(fill="x", padx=12, pady=(4, 8))

env_temp_lbl = ctk.CTkLabel(
    env_content,
    text="29°C",
    font=("Consolas", 24, "bold"),
    text_color=TEXT_WHITE
)
env_temp_lbl.pack(side="left", padx=(0, 10))

env_details = ctk.CTkFrame(env_content, fg_color="transparent")
env_details.pack(side="right", anchor="e")

env_cond_lbl = ctk.CTkLabel(env_details, text="Condition: Clear", font=FONT_SMALL, text_color=TEXT_CYAN)
env_cond_lbl.pack(anchor="e")

env_hum_lbl = ctk.CTkLabel(env_details, text="Humidity: 70%", font=FONT_SMALL, text_color=TEXT_CYAN)
env_hum_lbl.pack(anchor="e")

env_wind_lbl = ctk.CTkLabel(env_details, text="Wind: 0.1 km/h", font=FONT_SMALL, text_color=TEXT_CYAN)
env_wind_lbl.pack(anchor="e")

# PANEL 2: QUICK CONTROLS
ctrl_panel = create_hud_panel(right_col, "QUICK CONTROLS", icon="🎛")
ctrl_panel.pack(fill="x", pady=(0, 8))

ctrl_content = ctk.CTkFrame(ctrl_panel, fg_color="transparent")
ctrl_content.pack(fill="x", padx=12, pady=(4, 8))

# Volume Slider
vol_frame = ctk.CTkFrame(ctrl_content, fg_color="transparent")
vol_frame.pack(fill="x", pady=2)

vol_head = ctk.CTkFrame(vol_frame, fg_color="transparent")
vol_head.pack(fill="x")
ctk.CTkLabel(vol_head, text="🔊 Volume", font=FONT_SMALL, text_color=TEXT_CYAN).pack(side="left")
vol_val_lbl = ctk.CTkLabel(vol_head, text="70%", font=FONT_SMALL, text_color=TEXT_WHITE)
vol_val_lbl.pack(side="right")

def on_volume_change(val):
    val_int = int(val)
    vol_val_lbl.configure(text=f"{val_int}%")
    if HAS_PYCAW:
        try:
            sp = AudioUtilities.GetSpeakers()
            sp.EndpointVolume.SetMasterVolumeLevelScalar(val_int / 100.0, None)
        except Exception:
            pass

vol_slider = ctk.CTkSlider(
    vol_frame,
    from_=0,
    to=100,
    number_of_steps=100,
    progress_color=CYAN_BRIGHT,
    button_color=CYAN_BRIGHT,
    button_hover_color=TEXT_WHITE,
    height=14,
    command=on_volume_change
)
vol_slider.pack(fill="x", pady=(2, 4))
vol_slider.set(70)

# Brightness Slider
bright_frame = ctk.CTkFrame(ctrl_content, fg_color="transparent")
bright_frame.pack(fill="x", pady=2)

bright_head = ctk.CTkFrame(bright_frame, fg_color="transparent")
bright_head.pack(fill="x")
ctk.CTkLabel(bright_head, text="☀ Brightness", font=FONT_SMALL, text_color=TEXT_CYAN).pack(side="left")
bright_val_lbl = ctk.CTkLabel(bright_head, text="75%", font=FONT_SMALL, text_color=TEXT_WHITE)
bright_val_lbl.pack(side="right")

def on_brightness_change(val):
    val_int = int(val)
    bright_val_lbl.configure(text=f"{val_int}%")
    if HAS_SBC:
        try:
            sbc.set_brightness(val_int)
        except Exception:
            pass

bright_slider = ctk.CTkSlider(
    bright_frame,
    from_=0,
    to=100,
    number_of_steps=100,
    progress_color=CYAN_BRIGHT,
    button_color=CYAN_BRIGHT,
    button_hover_color=TEXT_WHITE,
    height=14,
    command=on_brightness_change
)
bright_slider.pack(fill="x", pady=(2, 4))
bright_slider.set(75)

# Toggles Row: Wi-Fi, Bluetooth, Power Mode
toggles_row = ctk.CTkFrame(ctrl_content, fg_color="transparent")
toggles_row.pack(fill="x", pady=(4, 0))

wifi_state = [True]
def toggle_wifi():
    wifi_state[0] = not wifi_state[0]
    wifi_btn.configure(
        text=f"Wi-Fi: {'On' if wifi_state[0] else 'Off'}",
        fg_color="#062238" if wifi_state[0] else "#2a0a14"
    )
    add_notification(f"Wi-Fi state changed to {'Online' if wifi_state[0] else 'Offline'}")

wifi_btn = ctk.CTkButton(
    toggles_row,
    text="Wi-Fi: On",
    width=72,
    height=24,
    font=FONT_SMALL,
    fg_color="#062238",
    border_color="#0088ff",
    border_width=1,
    command=toggle_wifi
)
wifi_btn.pack(side="left", padx=2)

bt_state = [True]
def toggle_bt():
    bt_state[0] = not bt_state[0]
    bt_btn.configure(
        text=f"BT: {'On' if bt_state[0] else 'Off'}",
        fg_color="#062238" if bt_state[0] else "#2a0a14"
    )
    add_notification(f"Bluetooth state changed to {'Online' if bt_state[0] else 'Offline'}")

bt_btn = ctk.CTkButton(
    toggles_row,
    text="BT: On",
    width=60,
    height=24,
    font=FONT_SMALL,
    fg_color="#062238",
    border_color="#0088ff",
    border_width=1,
    command=toggle_bt
)
bt_btn.pack(side="left", padx=2)

power_modes = ["Balanced", "Performance", "Eco", "Turbo"]
power_idx = [0]
def cycle_power():
    power_idx[0] = (power_idx[0] + 1) % len(power_modes)
    power_btn.configure(text=power_modes[power_idx[0]])
    add_notification(f"Power profile switched to {power_modes[power_idx[0]]}")

power_btn = ctk.CTkButton(
    toggles_row,
    text="Balanced",
    width=76,
    height=24,
    font=FONT_SMALL,
    fg_color="#062238",
    border_color="#0088ff",
    border_width=1,
    command=cycle_power
)
power_btn.pack(side="left", padx=2)

# Vision Actions Row
vision_actions_row = ctk.CTkFrame(ctrl_content, fg_color="transparent")
vision_actions_row.pack(fill="x", pady=(6, 0))

def on_gui_scan_screen():
    def worker():
        try:
            update_display("Scanning active display buffer with Gemma3 Vision...")
            set_status("blue")
            from vision import analyze_screen
            result = analyze_screen("Describe what is currently visible on the screen in 2 to 3 concise sentences.")
            update_display(result)
            set_status("green")
            from voice_engine.voice import speak
            speak(result)
            set_status("yellow")
        except Exception as e:
            update_display(f"Vision Scan Error: {e}")
            set_status("yellow")

    threading.Thread(target=worker, daemon=True).start()

def on_gui_screenshot():
    def worker():
        try:
            from vision import save_screenshot
            res = save_screenshot()
            add_notification(res)
            update_display(res)
            from voice_engine.voice import speak
            speak(res)
        except Exception as e:
            add_notification(f"Screenshot Error: {e}")

    threading.Thread(target=worker, daemon=True).start()

scan_screen_btn = ctk.CTkButton(
    vision_actions_row,
    text="👁 SCAN SCREEN",
    font=FONT_SMALL,
    fg_color="#0d2644",
    hover_color="#184b80",
    border_color=CYAN_BRIGHT,
    border_width=1,
    text_color=CYAN_BRIGHT,
    height=24,
    command=on_gui_scan_screen
)
scan_screen_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

screenshot_btn = ctk.CTkButton(
    vision_actions_row,
    text="📸 CAPTURE",
    font=FONT_SMALL,
    fg_color="#0d2644",
    hover_color="#184b80",
    border_color="#0088ff",
    border_width=1,
    text_color=TEXT_WHITE,
    height=24,
    width=80,
    command=on_gui_screenshot
)
screenshot_btn.pack(side="right", padx=(2, 0))

# Stark Telemetry & Briefing Actions Row
stark_actions_row = ctk.CTkFrame(ctrl_content, fg_color="transparent")
stark_actions_row.pack(fill="x", pady=(4, 0))

def on_gui_diagnostics():
    def worker():
        try:
            from system_layer.diagnostics_controller import format_spoken_diagnostics
            res = format_spoken_diagnostics()
            add_notification(res)
            update_display(res)
            from voice_engine.voice import speak
            speak(res)
        except Exception as e:
            add_notification(f"Diagnostics Error: {e}")
    threading.Thread(target=worker, daemon=True).start()

def on_gui_briefing():
    def worker():
        try:
            from system_layer.briefing_controller import generate_executive_briefing
            res = generate_executive_briefing()
            add_notification(res)
            update_display(res)
            from voice_engine.voice import speak
            speak(res)
        except Exception as e:
            add_notification(f"Briefing Error: {e}")
    threading.Thread(target=worker, daemon=True).start()

diag_btn = ctk.CTkButton(
    stark_actions_row,
    text="⚡ DIAGNOSTICS",
    font=FONT_SMALL,
    fg_color="#0d2644",
    hover_color="#184b80",
    border_color=CYAN_BRIGHT,
    border_width=1,
    text_color=CYAN_BRIGHT,
    height=24,
    command=on_gui_diagnostics
)
diag_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

briefing_btn = ctk.CTkButton(
    stark_actions_row,
    text="🌅 BRIEFING",
    font=FONT_SMALL,
    fg_color="#0d2644",
    hover_color="#184b80",
    border_color="#0088ff",
    border_width=1,
    text_color=TEXT_WHITE,
    height=24,
    command=on_gui_briefing
)
briefing_btn.pack(side="right", fill="x", expand=True, padx=(2, 0))


# PANEL: LIVE MEDIA HUD
media_panel = create_hud_panel(right_col, "MEDIA CONTROLLER", icon="🎵")
media_panel.pack(fill="x", pady=(0, 8))

media_info_frame = ctk.CTkFrame(media_panel, fg_color="transparent")
media_info_frame.pack(fill="x", padx=10, pady=(2, 4))

media_header_row = ctk.CTkFrame(media_info_frame, fg_color="transparent")
media_header_row.pack(fill="x")

media_title_lbl = ctk.CTkLabel(
    media_header_row,
    text="No Media Active",
    font=("Consolas", 11, "bold"),
    text_color=CYAN_BRIGHT
)
media_title_lbl.pack(side="left")

media_status_lbl = ctk.CTkLabel(
    media_header_row,
    text="● IDLE",
    font=FONT_SMALL,
    text_color=TEXT_MUTED
)
media_status_lbl.pack(side="right")

media_artist_lbl = ctk.CTkLabel(
    media_info_frame,
    text="Spotify / Windows Media",
    font=FONT_SMALL,
    text_color=TEXT_MUTED
)
media_artist_lbl.pack(anchor="w")

# Media Control Buttons
media_btn_row = ctk.CTkFrame(media_panel, fg_color="transparent")
media_btn_row.pack(fill="x", padx=10, pady=(2, 6))

def on_gui_media_prev():
    def worker():
        try:
            from system_layer.spotify_controller import media_previous
            res = media_previous()
            add_notification(res)
        except Exception as e:
            add_notification(f"Media Error: {e}")
    threading.Thread(target=worker, daemon=True).start()

def on_gui_media_playpause():
    def worker():
        try:
            from system_layer.spotify_controller import toggle_play_pause
            res = toggle_play_pause()
            add_notification(res)
        except Exception as e:
            add_notification(f"Media Error: {e}")
    threading.Thread(target=worker, daemon=True).start()

def on_gui_media_next():
    def worker():
        try:
            from system_layer.spotify_controller import media_next
            res = media_next()
            add_notification(res)
        except Exception as e:
            add_notification(f"Media Error: {e}")
    threading.Thread(target=worker, daemon=True).start()

media_prev_btn = ctk.CTkButton(
    media_btn_row,
    text="⏮ PREV",
    font=FONT_SMALL,
    fg_color="#0a1a2e",
    hover_color="#133055",
    border_color="#0088ff",
    border_width=1,
    text_color=TEXT_CYAN,
    height=22,
    width=60,
    command=on_gui_media_prev
)
media_prev_btn.pack(side="left", padx=(0, 2), expand=True, fill="x")

media_play_btn = ctk.CTkButton(
    media_btn_row,
    text="⏯ PLAY/PAUSE",
    font=FONT_SMALL,
    fg_color="#0d2644",
    hover_color="#184b80",
    border_color=CYAN_BRIGHT,
    border_width=1,
    text_color=CYAN_BRIGHT,
    height=22,
    width=90,
    command=on_gui_media_playpause
)
media_play_btn.pack(side="left", padx=2, expand=True, fill="x")

media_next_btn = ctk.CTkButton(
    media_btn_row,
    text="⏭ NEXT",
    font=FONT_SMALL,
    fg_color="#0a1a2e",
    hover_color="#133055",
    border_color="#0088ff",
    border_width=1,
    text_color=TEXT_CYAN,
    height=22,
    width=60,
    command=on_gui_media_next
)
media_next_btn.pack(side="left", padx=(2, 0), expand=True, fill="x")


# PANEL: TASK DIRECTIVES (STARK TASKMASTER)
todo_panel = create_hud_panel(right_col, "TASK DIRECTIVES", icon="📋")
todo_panel.pack(fill="x", pady=(0, 8))

todo_header_row = ctk.CTkFrame(todo_panel, fg_color="transparent")
todo_header_row.pack(fill="x", padx=10, pady=(2, 2))

todo_count_lbl = ctk.CTkLabel(
    todo_header_row,
    text="ACTIVE DIRECTIVES: 0",
    font=FONT_SMALL,
    text_color=CYAN_BRIGHT
)
todo_count_lbl.pack(side="left")

todo_items_frame = ctk.CTkFrame(todo_panel, fg_color="transparent")
todo_items_frame.pack(fill="x", padx=8, pady=(0, 6))

def refresh_todo_hud():
    try:
        from system_layer.todo_controller import get_active_tasks
        tasks = get_active_tasks(limit=3)

        for w in todo_items_frame.winfo_children():
            w.destroy()

        if not tasks:
            todo_count_lbl.configure(text="ALL DIRECTIVES COMPLETE ●", text_color=GREEN_ACCENT)
            empty_lbl = ctk.CTkLabel(
                todo_items_frame,
                text="No pending directives. Voice: 'add task ...'",
                font=FONT_SMALL,
                text_color=TEXT_MUTED
            )
            empty_lbl.pack(anchor="w", padx=4, pady=2)
        else:
            todo_count_lbl.configure(text=f"PENDING DIRECTIVES ({len(tasks)})", text_color=CYAN_BRIGHT)
            for t in tasks:
                t_id = t["id"]
                t_text = t["task"]
                row = ctk.CTkFrame(todo_items_frame, fg_color="#041426", corner_radius=4, height=22)
                row.pack(fill="x", pady=1)

                def make_done_cmd(tid=t_id):
                    def _done():
                        try:
                            from system_layer.todo_controller import complete_task
                            res = complete_task(str(tid))
                            add_notification(res)
                            refresh_todo_hud()
                        except Exception as e:
                            print(f"[TODO CLICK ERROR]: {e}")
                    return _done

                check_btn = ctk.CTkButton(
                    row,
                    text="✔",
                    width=22,
                    height=20,
                    font=("Consolas", 10, "bold"),
                    fg_color="#062238",
                    hover_color="#00aa88",
                    border_color=CYAN_BRIGHT,
                    border_width=1,
                    text_color=GREEN_ACCENT,
                    command=make_done_cmd(t_id)
                )
                check_btn.pack(side="left", padx=2, pady=1)

                display_t = (t_text[:24] + "...") if len(t_text) > 26 else t_text
                lbl = ctk.CTkLabel(
                    row,
                    text=f"#{t_id} {display_t}",
                    font=FONT_SMALL,
                    text_color=TEXT_CYAN
                )
                lbl.pack(side="left", padx=4)
    except Exception:
        pass
    app.after(3000, refresh_todo_hud)

app.after(1000, refresh_todo_hud)


# PANEL 3: SYSTEM NOTIFICATIONS
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
notif_box.insert("end", "• JARVIS: 24 Skills loaded successfully. [10:41]\n")
notif_box.insert("end", "• JARVIS: Ready for your command. [10:40]\n")
notif_box.configure(state="disabled")

def add_notification(text):
    now_str = datetime.now().strftime("%H:%M")
    notif_box.configure(state="normal")
    notif_box.insert("0.0", f"• JARVIS: {text} [{now_str}]\n")
    notif_box.configure(state="disabled")

# ============================================================
# 3. BOTTOM SECTION: TERMINAL CONSOLE & COMMAND INPUT DOCK
# ============================================================

bottom_section = ctk.CTkFrame(root_frame, fg_color="transparent")
bottom_section.pack(fill="x", side="bottom", pady=(6, 0))

# TERMINAL CONSOLE
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

# TYPEWRITER ENGINE
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

# COMMAND INPUT DOCK ROW
dock_row = ctk.CTkFrame(bottom_section, fg_color="transparent")
dock_row.pack(fill="x")

# Voice Toggle Button & Mini Wave
voice_active = [True]
def toggle_voice_btn():
    voice_active[0] = not voice_active[0]
    if voice_active[0]:
        mic_btn.configure(fg_color="#062f48", border_color=CYAN_BRIGHT, text_color=CYAN_BRIGHT)
        mic_lbl.configure(text="Voice Active", text_color=CYAN_BRIGHT)
        status_readout.configure(text="STATUS: LISTENING", text_color=CYAN_BRIGHT)
        add_notification("Voice recognition activated.")
    else:
        mic_btn.configure(fg_color="#360a14", border_color="#ff4444", text_color="#ff4444")
        mic_lbl.configure(text="Voice Muted", text_color="#ff4444")
        status_readout.configure(text="STATUS: STANDBY", text_color=TEXT_MUTED)
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

# Command Input Entry
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
    placeholder_text="Enter a command... (e.g., 'weather', 'scan', 'time', '2+4', 'open chrome')",
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

# Branding (Bottom Right)
brand_lbl = ctk.CTkLabel(
    dock_row,
    text="J.A.R.V.I.S. PROTOCOL",
    font=("Consolas", 9, "bold"),
    text_color=CYAN_BRIGHT
)
brand_lbl.pack(side="right")

# ============================================================
# 4. CENTER CANVAS ANIMATIONS: ARC REACTOR & RADAR COMPASS
# ============================================================

radar_angle = 0
pulse_factor = 0
pulse_dir = 1
scan_arc_angle = 0

def animate_center_hud():
    global radar_angle, pulse_factor, pulse_dir, scan_arc_angle
    try:
        w = hud_canvas.winfo_width()
        h = hud_canvas.winfo_height()
        if w < 50 or h < 50:
            w, h = CENTER_WIDTH, CENTER_HEIGHT

        hud_canvas.delete("all")

        # Layout division: Arc Reactor (Top) & Radar Compass (Bottom)
        cx = w / 2
        reactor_cy = h * 0.28
        radar_cy = h * 0.72

        # ---------------- 1. ARC REACTOR ----------------
        pulse_factor += 0.08 * pulse_dir
        if pulse_factor > 1.0:
            pulse_dir = -1
        elif pulse_factor < 0.0:
            pulse_dir = 1

        is_spk = False
        try:
            is_spk = speaking_status() if callable(speaking_status) else bool(speaking_status)
        except Exception:
            pass

        # Audio-reactive pulse boost
        audio_boost = 0.0
        if is_spk:
            audio_boost = 6.0 + 8.0 * (0.5 + 0.5 * math.sin(time.time() * 14.0))
        elif audio_level > 85:
            audio_boost = min(12.0, (audio_level / 220.0) * 8.0)

        r_base = 40 + pulse_factor * 4 + audio_boost
        # Outer glow ring
        hud_canvas.create_oval(
            cx - r_base - 12, reactor_cy - r_base - 12,
            cx + r_base + 12, reactor_cy + r_base + 12,
            outline="#034d66", width=1
        )
        # Primary outer ring
        hud_canvas.create_oval(
            cx - r_base, reactor_cy - r_base,
            cx + r_base, reactor_cy + r_base,
            outline=CYAN_BRIGHT, width=2
        )
        # Middle ring
        hud_canvas.create_oval(
            cx - r_base * 0.65, reactor_cy - r_base * 0.65,
            cx + r_base * 0.65, reactor_cy + r_base * 0.65,
            outline=BLUE_ACCENT, width=2
        )
        # Inner pulsing core
        core_r = 12 + pulse_factor * 3 + (audio_boost * 0.5)
        hud_canvas.create_oval(
            cx - core_r, reactor_cy - core_r,
            cx + core_r, reactor_cy + core_r,
            fill="#dffbff", outline=CYAN_BRIGHT, width=1
        )

        # Radiating energy arms
        for i in range(6):
            ang = math.radians(i * 60 + radar_angle * 0.5)
            x1 = cx + (r_base * 0.65) * math.cos(ang)
            y1 = reactor_cy + (r_base * 0.65) * math.sin(ang)
            x2 = cx + r_base * math.cos(ang)
            y2 = reactor_cy + r_base * math.sin(ang)
            hud_canvas.create_line(x1, y1, x2, y2, fill=CYAN_BRIGHT, width=2)

        # ---------------- 2. RADAR COMPASS HUD ----------------
        radar_r = min(68, h * 0.24)

        # Outer dashed circle & solid ring
        hud_canvas.create_oval(
            cx - radar_r, radar_cy - radar_r,
            cx + radar_r, radar_cy + radar_r,
            outline="#0a4366", width=1
        )
        hud_canvas.create_oval(
            cx - radar_r * 0.72, radar_cy - radar_r * 0.72,
            cx + radar_r * 0.72, radar_cy + radar_r * 0.72,
            outline="#00a3cc", width=1
        )
        hud_canvas.create_oval(
            cx - radar_r * 0.38, radar_cy - radar_r * 0.38,
            cx + radar_r * 0.38, radar_cy + radar_r * 0.38,
            outline=CYAN_BRIGHT, width=1
        )

        # Crosshairs
        hud_canvas.create_line(cx - radar_r - 6, radar_cy, cx + radar_r + 6, radar_cy, fill="#073a52", width=1)
        hud_canvas.create_line(cx, radar_cy - radar_r - 6, cx, radar_cy + radar_r + 6, fill="#073a52", width=1)

        # Radar Sweep Line (360 degrees)
        radar_angle = (radar_angle + 3) % 360
        sweep_rad = math.radians(radar_angle)
        sx = cx + radar_r * math.cos(sweep_rad)
        sy = radar_cy + radar_r * math.sin(sweep_rad)
        hud_canvas.create_line(cx, radar_cy, sx, sy, fill=CYAN_BRIGHT, width=2)

        # Cardinal Points (N, S, E, W)
        hud_canvas.create_text(cx, radar_cy - radar_r - 12, text="N", fill=CYAN_BRIGHT, font=("Consolas", 9, "bold"))
        hud_canvas.create_text(cx, radar_cy + radar_r + 12, text="S", fill=CYAN_BRIGHT, font=("Consolas", 9, "bold"))
        hud_canvas.create_text(cx - radar_r - 12, radar_cy, text="W", fill=CYAN_BRIGHT, font=("Consolas", 9, "bold"))
        hud_canvas.create_text(cx + radar_r + 12, radar_cy, text="E", fill=CYAN_BRIGHT, font=("Consolas", 9, "bold"))

        # Center dot
        hud_canvas.create_oval(cx - 3, radar_cy - 3, cx + 3, radar_cy + 3, fill=CYAN_BRIGHT, outline="")

    except Exception:
        pass

    app.after(40, animate_center_hud)

animate_center_hud()

# ============================================================
# 5. AUDIO EQUALIZER: TRUE FFT FREQUENCY SPECTRUM ANALYZER
# ============================================================

NUM_WAVE_BARS = 36
wave_bars = []
audio_level = 0
thinking_active = False

# Frequency Analysis Setup
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

freq_bins = np.fft.rfftfreq(CHUNK, 1.0 / RATE)
log_edges = np.logspace(np.log10(60), np.log10(8500), num=NUM_WAVE_BARS + 1)
band_masks = []
for i in range(NUM_WAVE_BARS):
    mask = (freq_bins >= log_edges[i]) & (freq_bins < log_edges[i + 1])
    band_masks.append(mask)

hanning_window = np.hanning(CHUNK)
fft_spectrum_levels = np.zeros(NUM_WAVE_BARS)
current_display_heights = np.zeros(NUM_WAVE_BARS)

def init_wave_bars():
    wave_canvas.delete("all")
    w = wave_canvas.winfo_width()
    if w < 50:
        w = WAVE_WIDTH
    bar_width = w / (NUM_WAVE_BARS + 2)
    wave_bars.clear()

    for i in range(NUM_WAVE_BARS):
        x = (i + 1) * bar_width
        # Sub-bass & Bass: cyan-blue, Mid voice: neon cyan, Treble: electric aqua
        if i < 10:
            color = "#00d0ff"
        elif i < 26:
            color = CYAN_BRIGHT
        else:
            color = "#38bdf8"

        line = wave_canvas.create_line(x, 22, x, 22, fill=color, width=3)
        wave_bars.append((line, x))

def animate_equalizer():
    global audio_level
    try:
        if not wave_bars:
            init_wave_bars()

        center_y = 22

        is_spk = False
        try:
            is_spk = speaking_status() if callable(speaking_status) else bool(speaking_status)
        except Exception:
            pass

        for i in range(NUM_WAVE_BARS):
            target_h = fft_spectrum_levels[i]

            if audio_level > 85:
                # Real sound/speech detected: fast attack, smooth exponential decay
                if target_h > current_display_heights[i]:
                    current_display_heights[i] = target_h
                else:
                    current_display_heights[i] = max(2.0, current_display_heights[i] * 0.78)
            elif is_spk:
                # Live dynamic speech visualization wave!
                speech_h = 3.5 + 14.0 * abs(math.sin(time.time() * 9.5 + i * 0.38))
                current_display_heights[i] = max(current_display_heights[i] * 0.76, speech_h)
            else:
                # Gentle ambient idle breathing wave when quiet
                current_display_heights[i] = max(2.0, current_display_heights[i] * 0.82)
                ambient_h = 2.5 + 3.0 * math.sin(time.time() * 2.8 + i * 0.35)
                current_display_heights[i] = max(current_display_heights[i], ambient_h)

            h = int(current_display_heights[i])
            line, x = wave_bars[i]
            wave_canvas.coords(line, x, center_y - h, x, center_y + h)

    except Exception:
        pass

    app.after(35, animate_equalizer)

animate_equalizer()

# Real Microphone Listener Thread with Fast Fourier Transform
def mic_listener():
    global audio_level, fft_spectrum_levels
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        while True:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                audio_level = float(np.abs(audio_data).mean())

                # Compute Fast Fourier Transform
                windowed = audio_data * hanning_window
                fft_mag = np.abs(np.fft.rfft(windowed))

                # Bin into logarithmic frequency bands
                raw_bands = np.zeros(NUM_WAVE_BARS)
                for i in range(NUM_WAVE_BARS):
                    m = band_masks[i]
                    if np.any(m):
                        raw_bands[i] = np.mean(fft_mag[m])

                # Logarithmic perception scaling
                scaled_bands = np.log10(1.0 + raw_bands / 45.0)
                fft_spectrum_levels = np.clip(scaled_bands * 7.5, 0.0, 19.0)

            except Exception:
                time.sleep(0.02)
    except Exception:
        pass

threading.Thread(target=mic_listener, daemon=True).start()

# ============================================================
# 6. TELEMETRY, CLOCK & HARDWARE CONTROLLER LOOPS
# ============================================================

def update_clock():
    now = datetime.now()
    live_clock_lbl.configure(text=now.strftime("%I:%M:%S %p"))
    app.after(1000, update_clock)

update_clock()

last_net_bytes = [None, None, 0.0]

def update_system_stats():
    global last_net_bytes
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        ram = mem.percent
        batt = psutil.sensors_battery()
        batt_val = batt.percent if batt else 100
        batt_plugged = batt.power_plugged if batt else True

        # 1. Update CPU Radial Gauge
        cpu_extent = -max(1.0, min(240.0, 240.0 * (cpu / 100.0)))
        if cpu < 50:
            cpu_color = CYAN_BRIGHT
        elif cpu < 80:
            cpu_color = "#f59e0b"
        else:
            cpu_color = "#ff3b30"
        telemetry_canvas.itemconfigure(cpu_gauge_arc, extent=cpu_extent, outline=cpu_color)
        telemetry_canvas.itemconfigure(cpu_gauge_text, text=f"{cpu:.0f}%", fill=cpu_color)

        # 2. Update RAM Radial Gauge
        ram_extent = -max(1.0, min(240.0, 240.0 * (ram / 100.0)))
        if ram < 60:
            ram_color = CYAN_BRIGHT
        elif ram < 85:
            ram_color = "#38bdf8"
        else:
            ram_color = "#ff3b30"
        telemetry_canvas.itemconfigure(ram_gauge_arc, extent=ram_extent, outline=ram_color)
        telemetry_canvas.itemconfigure(ram_gauge_text, text=f"{ram:.0f}%", fill=ram_color)

        # 3. Update RAM Detailed Readout
        used_gb = mem.used / (1024**3)
        total_gb = mem.total / (1024**3)
        ram_detail_lbl.configure(text=f"MEM ALLOC: {used_gb:.1f} / {total_gb:.1f} GB")

        # 4. Live Network Speedometer
        now = time.time()
        net_io = psutil.net_io_counters()
        if last_net_bytes[0] is not None and (now - last_net_bytes[2]) > 0:
            dt = now - last_net_bytes[2]
            down_rate = (net_io.bytes_recv - last_net_bytes[0]) / dt
            up_rate = (net_io.bytes_sent - last_net_bytes[1]) / dt

            def fmt_rate(rate):
                kb = max(0.0, rate / 1024.0)
                if kb < 1024:
                    return f"{kb:.1f} KB/s"
                else:
                    return f"{kb / 1024.0:.2f} MB/s"

            net_down_lbl.configure(text=f"↓ {fmt_rate(down_rate)}")
            net_up_lbl.configure(text=f"↑ {fmt_rate(up_rate)}")

        last_net_bytes[0] = net_io.bytes_recv
        last_net_bytes[1] = net_io.bytes_sent
        last_net_bytes[2] = now

        # 5. Battery & Power
        batt_val_lbl.configure(text=f"{batt_val:.0f}% {'⚡' if batt_plugged else ''}")
        batt_title_lbl.configure(text=f"⚡ BATTERY ({'AC' if batt_plugged else 'DC'})")
        batt_bar.set(batt_val / 100.0)
        if batt_plugged:
            batt_bar.configure(progress_color=GREEN_ACCENT)
        elif batt_val > 30:
            batt_bar.configure(progress_color=CYAN_BRIGHT)
        elif batt_val > 15:
            batt_bar.configure(progress_color="#f59e0b")
        else:
            batt_bar.configure(progress_color="#ff3b30")

        # 6. Check network
        net_online = False
        try:
            for _, info in psutil.net_if_stats().items():
                if info.isup and not info.name.startswith("Loopback"):
                    net_online = True
                    break
        except Exception:
            pass

        net_badge_lbl.configure(
            text=f"NET: {'ONLINE' if net_online else 'OFFLINE'}",
            text_color=GREEN_ACCENT if net_online else "#ff4444"
        )

        voice_busy = False
        try:
            voice_busy = speaking_status() if callable(speaking_status) else bool(speaking_status)
        except Exception:
            pass

        is_priv = False
        try:
            from wake_word import is_privacy_muted
            is_priv = is_privacy_muted()
        except Exception:
            pass

        if is_priv:
            voice_badge_lbl.configure(
                text="MIC: MUTED [PRIVACY]",
                text_color="#ff3b30"
            )
        else:
            voice_badge_lbl.configure(
                text=f"VOICE: {'SPEAKING' if voice_busy else 'READY'}",
                text_color=GREEN_ACCENT if voice_busy else CYAN_BRIGHT
            )

        try:
            from background_tasks.focus_guard import get_focus_status
            f_stat = get_focus_status()
            if f_stat.get("active"):
                focus_badge_lbl.configure(
                    text=f"FOCUS: {f_stat.get('remaining_str')} [ACTIVE]",
                    text_color=CYAN_BRIGHT
                )
            else:
                focus_badge_lbl.configure(
                    text="FOCUS GUARD: STANDBY",
                    text_color=TEXT_MUTED
                )
        except Exception:
            pass

        try:
            from background_tasks.sentry_guard import is_sentry_active
            if is_sentry_active():
                sentry_badge_lbl.configure(text="SENTRY: ARMED 👁", text_color=GREEN_ACCENT)
            else:
                sentry_badge_lbl.configure(text="SENTRY GUARD: STANDBY", text_color=TEXT_MUTED)
        except Exception:
            pass

        try:
            from background_tasks.wellness_monitor import get_wellness_summary
            w_sum = get_wellness_summary()
            if w_sum.get("active"):
                wellness_badge_lbl.configure(
                    text=f"WELLNESS: {w_sum.get('badge_text', 'ACTIVE')}",
                    text_color=CYAN_BRIGHT
                )
            else:
                wellness_badge_lbl.configure(
                    text="WELLNESS: STANDBY",
                    text_color=TEXT_MUTED
                )
        except Exception:
            pass

    except Exception:
        pass


    app.after(1500, update_system_stats)

update_system_stats()

# Live Weather Fetcher
def fetch_weather():
    def worker():
        try:
            data = get_weather_data("Vadodara")
            if data:
                temp = data.get("temperature", 29)
                hum = data.get("humidity", 70)
                wind = data.get("wind", 0.1)

                app.after(0, lambda: env_temp_lbl.configure(text=f"{temp:.0f}°C"))
                app.after(0, lambda: env_hum_lbl.configure(text=f"Humidity: {hum}%"))
                app.after(0, lambda: env_wind_lbl.configure(text=f"Wind: {wind} km/h"))
        except Exception:
            pass
        finally:
            app.after(10 * 60 * 1000, fetch_weather)

    threading.Thread(target=worker, daemon=True).start()

fetch_weather()

# Live Media HUD Poller
_media_cache = {"title": "No Media Active", "artist": "Spotify / Windows Media", "playing": False}

def _media_poll_worker():
    while True:
        try:
            from system_layer.spotify_controller import get_current_track_info
            info = get_current_track_info()
            if info and info.get("title"):
                _media_cache["title"] = info["title"]
                _media_cache["artist"] = info.get("artist", "")
                _media_cache["playing"] = info.get("playing", False)
            else:
                _media_cache["title"] = "No Media Active"
                _media_cache["artist"] = "Spotify / Windows Media"
                _media_cache["playing"] = False
        except Exception:
            pass
        time.sleep(2.5)

threading.Thread(target=_media_poll_worker, daemon=True, name="MediaPoller").start()

def update_media_display():
    try:
        title = _media_cache.get("title", "No Media Active")
        artist = _media_cache.get("artist", "")
        playing = _media_cache.get("playing", False)

        display_title = (title[:22] + "...") if len(title) > 24 else title
        media_title_lbl.configure(text=display_title)
        media_artist_lbl.configure(text=artist[:26] if artist else "Media Standby")

        if playing:
            media_status_lbl.configure(text="● PLAYING", text_color=GREEN_ACCENT)
        else:
            media_status_lbl.configure(text="● IDLE", text_color=TEXT_MUTED)
    except Exception:
        pass
    app.after(1500, update_media_display)

update_media_display()

# Sync initial volume and brightness
if HAS_PYCAW:
    try:
        sp = AudioUtilities.GetSpeakers()
        v = int(sp.EndpointVolume.GetMasterVolumeLevelScalar() * 100)
        vol_slider.set(v)
        vol_val_lbl.configure(text=f"{v}%")
    except Exception:
        pass

if HAS_SBC:
    try:
        b = sbc.get_brightness()[0]
        bright_slider.set(b)
        bright_val_lbl.configure(text=f"{b}%")
    except Exception:
        pass

# ============================================================
# 7. ASSISTANT CORE STATUS & BOOTSTRAP CALLBACKS
# ============================================================

def set_status(color_or_name):
    color_map = {
        "yellow": ("STATUS: LISTENING", CYAN_BRIGHT),
        "blue": ("STATUS: PROCESSING", BLUE_ACCENT),
        "green": ("STATUS: SPEAKING", GREEN_ACCENT),
        "red": ("STATUS: STANDBY", "#ff4444"),
        "gray": ("STATUS: IDLE", TEXT_MUTED)
    }
    c_str = str(color_or_name).lower()
    text, col = color_map.get(c_str, (f"STATUS: {str(color_or_name).upper()}", CYAN_BRIGHT))
    status_readout.configure(text=text, text_color=col)

    try:
        if c_str in ("green", "speaking"):
            interrupt_btn.configure(
                fg_color="#801b1b",
                hover_color="#b32424",
                border_color="#ff4444",
                text_color="#ffffff"
            )
        else:
            interrupt_btn.configure(
                fg_color="#1a1f2c",
                hover_color="#801b1b",
                border_color="#2a354a",
                text_color="#6e82a0"
            )
    except Exception:
        pass


def thinking_animation():
    dots = ["Thinking.", "Thinking..", "Thinking..."]
    def animate(idx=0):
        if getattr(assistant_core, "thinking_active", False):
            status_readout.configure(text=f"STATUS: {dots[idx % 3]}", text_color=BLUE_ACCENT)
            app.after(350, lambda: animate(idx + 1))
    animate()

def startup_sequence():
    messages = [
        "Initializing core neural architecture...",
        "Calibrating radar and audio interfaces...",
        "Loaded 24 modular skills...",
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
# 8. GLOBAL HOTKEY (CTRL + SPACE) SYSTEM-WIDE LISTENER
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
# 9. WINDOWS SYSTEM TRAY NOTIFICATION AREA INTEGRATION
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

