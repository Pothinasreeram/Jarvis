"""
Arc Reactor, Radar Compass & Waveform Equalizer Panel for J.A.R.V.I.S. Sci-Fi HUD
Combines the holographic Arc Reactor canvas, rotating 360-degree Radar Compass,
real-time FFT audio spectrum visualizer, mic listener thread, and status controls.
"""

import math
import time
import threading
import tkinter as tk
import customtkinter as ctk
import numpy as np
import pyaudio

from voice_engine.voice import speaking_status, stop_speaking

# Palette Constants
HUD_BG = "#020813"
PANEL_BORDER_DIM = "#0a3656"
CYAN_BRIGHT = "#00f0ff"
BLUE_ACCENT = "#0088ff"
GREEN_ACCENT = "#00ff66"
TEXT_WHITE = "#ffffff"
TEXT_CYAN = "#a5f3fc"
TEXT_MUTED = "#3a7a94"

CENTER_WIDTH = 480
CENTER_HEIGHT = 330
WAVE_WIDTH = 480
WAVE_HEIGHT = 44

NUM_WAVE_BARS = 36
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


class ReactorPanel:
    """
    Modular Center Panel:
    - Arc Reactor (pulsing core, outer energy glow, radiating energy arms)
    - Radar Compass (sweeping vector line, rings, cardinal points N/S/E/W)
    - Fast Fourier Transform (FFT) 36-band Audio Equalizer
    - Status readout banner & Interruption trigger
    """

    def __init__(self, parent, tk_root, notif_callback=None):
        self.parent = parent
        self.tk_root = tk_root
        self.notif_cb = notif_callback

        # Container Frame
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=0)

        # 1. Neural Node Sub-Header
        self.center_title = ctk.CTkLabel(
            self.frame,
            text="◈  J . A . R . V . I . S .  ◈",
            font=("Consolas", 18, "bold"),
            text_color=CYAN_BRIGHT
        )
        self.center_title.pack(side="top", pady=(4, 0))

        self.center_sub = ctk.CTkLabel(
            self.frame,
            text="NEURAL CORE ARCHITECTURE // ONLINE",
            font=("Consolas", 9),
            text_color=TEXT_MUTED
        )
        self.center_sub.pack(side="top", pady=(0, 4))

        # 2. Combined Centerpiece Canvas (Arc Reactor + Radar Compass)
        self.hud_canvas = tk.Canvas(
            self.frame,
            width=CENTER_WIDTH,
            height=CENTER_HEIGHT,
            bg=HUD_BG,
            highlightthickness=0
        )
        self.hud_canvas.pack(fill="both", expand=True, pady=2)
        self.hud_canvas.bind("<Button-1>", self._on_arc_reactor_click)

        # 3. Audio Waveform Equalizer Canvas
        self.wave_canvas = tk.Canvas(
            self.frame,
            width=WAVE_WIDTH,
            height=WAVE_HEIGHT,
            bg="#030c1a",
            highlightthickness=1,
            highlightbackground=PANEL_BORDER_DIM
        )
        self.wave_canvas.pack(fill="x", padx=12, pady=(2, 4))

        # 4. Status readout
        self.status_readout = ctk.CTkLabel(
            self.frame,
            text="STATUS: LISTENING",
            font=("Consolas", 13, "bold"),
            text_color=CYAN_BRIGHT
        )
        self.status_readout.pack(side="top", pady=(0, 2))

        # 5. Interrupt Button
        self.interrupt_btn = ctk.CTkButton(
            self.frame,
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
            command=self.trigger_interrupt
        )
        self.interrupt_btn.pack(side="top", pady=(0, 4))

        # Bind Escape key globally on root
        self.tk_root.bind("<Escape>", lambda event: self.trigger_interrupt())

        # State Variables for Animations
        self.radar_angle = 0
        self.pulse_factor = 0.0
        self.pulse_dir = 1
        self.audio_level = 0.0

        # FFT & Equalizer State
        self.freq_bins = np.fft.rfftfreq(CHUNK, 1.0 / RATE)
        self.log_edges = np.logspace(np.log10(60), np.log10(8500), num=NUM_WAVE_BARS + 1)
        self.band_masks = [
            (self.freq_bins >= self.log_edges[i]) & (self.freq_bins < self.log_edges[i + 1])
            for i in range(NUM_WAVE_BARS)
        ]
        self.hanning_window = np.hanning(CHUNK)
        self.fft_spectrum_levels = np.zeros(NUM_WAVE_BARS)
        self.current_display_heights = np.zeros(NUM_WAVE_BARS)
        self.wave_bars = []

        # Start Background Microphone FFT thread & Canvas Animation Loops
        self._start_mic_listener()
        self.animate_center_hud()
        self.animate_equalizer()

    def _notify(self, text):
        if self.notif_cb:
            try:
                self.notif_cb(text)
            except Exception:
                pass

    def _on_arc_reactor_click(self, event=None):
        try:
            from wake_word import trigger_wake_word
            from voice_engine.sound_effects import play_fx
            play_fx("wake")
            trigger_wake_word()
            self._notify("Arc Reactor tapped: Listening mode activated.")
        except Exception as e:
            print("[ARC REACTOR CLICK ERROR]:", e)

    def trigger_interrupt(self, event=None):
        try:
            stop_speaking()
        except Exception as e:
            print("[GUI INTERRUPT ERROR]:", e)

    def set_status(self, color_or_name):
        """Map status code to label text & colors, updating interrupt highlight."""
        color_map = {
            "yellow": ("STATUS: LISTENING", CYAN_BRIGHT),
            "blue": ("STATUS: PROCESSING", BLUE_ACCENT),
            "green": ("STATUS: SPEAKING", GREEN_ACCENT),
            "red": ("STATUS: STANDBY", "#ff4444"),
            "gray": ("STATUS: IDLE", TEXT_MUTED)
        }
        c_str = str(color_or_name).lower()
        text, col = color_map.get(c_str, (f"STATUS: {str(color_or_name).upper()}", CYAN_BRIGHT))
        self.status_readout.configure(text=text, text_color=col)

        try:
            if c_str in ("green", "speaking"):
                self.interrupt_btn.configure(
                    fg_color="#801b1b",
                    hover_color="#b32424",
                    border_color="#ff4444",
                    text_color="#ffffff"
                )
            else:
                self.interrupt_btn.configure(
                    fg_color="#1a1f2c",
                    hover_color="#801b1b",
                    border_color="#2a354a",
                    text_color="#6e82a0"
                )
        except Exception:
            pass

    def animate_center_hud(self):
        """Draws rotating holographic Arc Reactor and Radar Compass."""
        try:
            w = self.hud_canvas.winfo_width()
            h = self.hud_canvas.winfo_height()
            if w < 50 or h < 50:
                w, h = CENTER_WIDTH, CENTER_HEIGHT

            self.hud_canvas.delete("all")

            cx = w / 2
            reactor_cy = h * 0.28
            radar_cy = h * 0.72

            # ---------------- 1. ARC REACTOR ----------------
            self.pulse_factor += 0.08 * self.pulse_dir
            if self.pulse_factor > 1.0:
                self.pulse_dir = -1
            elif self.pulse_factor < 0.0:
                self.pulse_dir = 1

            is_spk = False
            try:
                is_spk = speaking_status() if callable(speaking_status) else bool(speaking_status)
            except Exception:
                pass

            audio_boost = 0.0
            if is_spk:
                audio_boost = 6.0 + 8.0 * (0.5 + 0.5 * math.sin(time.time() * 14.0))
            elif self.audio_level > 85:
                audio_boost = min(12.0, (self.audio_level / 220.0) * 8.0)

            r_base = 40 + self.pulse_factor * 4 + audio_boost

            # Outer glow ring
            self.hud_canvas.create_oval(
                cx - r_base - 12, reactor_cy - r_base - 12,
                cx + r_base + 12, reactor_cy + r_base + 12,
                outline="#034d66", width=1
            )
            # Primary outer ring
            self.hud_canvas.create_oval(
                cx - r_base, reactor_cy - r_base,
                cx + r_base, reactor_cy + r_base,
                outline=CYAN_BRIGHT, width=2
            )
            # Middle ring
            self.hud_canvas.create_oval(
                cx - r_base * 0.65, reactor_cy - r_base * 0.65,
                cx + r_base * 0.65, reactor_cy + r_base * 0.65,
                outline=BLUE_ACCENT, width=2
            )
            # Inner pulsing core
            core_r = 12 + self.pulse_factor * 3 + (audio_boost * 0.5)
            self.hud_canvas.create_oval(
                cx - core_r, reactor_cy - core_r,
                cx + core_r, reactor_cy + core_r,
                fill="#dffbff", outline=CYAN_BRIGHT, width=1
            )

            # Radiating energy arms
            for i in range(6):
                ang = math.radians(i * 60 + self.radar_angle * 0.5)
                x1 = cx + (r_base * 0.65) * math.cos(ang)
                y1 = reactor_cy + (r_base * 0.65) * math.sin(ang)
                x2 = cx + r_base * math.cos(ang)
                y2 = reactor_cy + r_base * math.sin(ang)
                self.hud_canvas.create_line(x1, y1, x2, y2, fill=CYAN_BRIGHT, width=2)

            # ---------------- 2. RADAR COMPASS HUD ----------------
            radar_r = min(68, h * 0.24)

            # Outer dashed & solid rings
            self.hud_canvas.create_oval(
                cx - radar_r, radar_cy - radar_r,
                cx + radar_r, radar_cy + radar_r,
                outline="#0a4366", width=1
            )
            self.hud_canvas.create_oval(
                cx - radar_r * 0.72, radar_cy - radar_r * 0.72,
                cx + radar_r * 0.72, radar_cy + radar_r * 0.72,
                outline="#00a3cc", width=1
            )
            self.hud_canvas.create_oval(
                cx - radar_r * 0.38, radar_cy - radar_r * 0.38,
                cx + radar_r * 0.38, radar_cy + radar_r * 0.38,
                outline=CYAN_BRIGHT, width=1
            )

            # Crosshairs
            self.hud_canvas.create_line(cx - radar_r - 6, radar_cy, cx + radar_r + 6, radar_cy, fill="#073a52", width=1)
            self.hud_canvas.create_line(cx, radar_cy - radar_r - 6, cx, radar_cy + radar_r + 6, fill="#073a52", width=1)

            # Radar Sweep Line (360 degrees)
            self.radar_angle = (self.radar_angle + 3) % 360
            sweep_rad = math.radians(self.radar_angle)
            sx = cx + radar_r * math.cos(sweep_rad)
            sy = radar_cy + radar_r * math.sin(sweep_rad)
            self.hud_canvas.create_line(cx, radar_cy, sx, sy, fill=CYAN_BRIGHT, width=2)

            # Cardinal Points
            self.hud_canvas.create_text(cx, radar_cy - radar_r - 12, text="N", fill=CYAN_BRIGHT, font=("Consolas", 9, "bold"))
            self.hud_canvas.create_text(cx, radar_cy + radar_r + 12, text="S", fill=CYAN_BRIGHT, font=("Consolas", 9, "bold"))
            self.hud_canvas.create_text(cx - radar_r - 12, radar_cy, text="W", fill=CYAN_BRIGHT, font=("Consolas", 9, "bold"))
            self.hud_canvas.create_text(cx + radar_r + 12, radar_cy, text="E", fill=CYAN_BRIGHT, font=("Consolas", 9, "bold"))

            # Center dot
            self.hud_canvas.create_oval(cx - 3, radar_cy - 3, cx + 3, radar_cy + 3, fill=CYAN_BRIGHT, outline="")

        except Exception:
            pass

        self.tk_root.after(40, self.animate_center_hud)

    def _init_wave_bars(self):
        self.wave_canvas.delete("all")
        w = self.wave_canvas.winfo_width()
        if w < 50:
            w = WAVE_WIDTH
        bar_width = w / (NUM_WAVE_BARS + 2)
        self.wave_bars.clear()

        for i in range(NUM_WAVE_BARS):
            x = (i + 1) * bar_width
            if i < 10:
                color = "#00d0ff"
            elif i < 26:
                color = CYAN_BRIGHT
            else:
                color = "#38bdf8"

            line = self.wave_canvas.create_line(x, 22, x, 22, fill=color, width=3)
            self.wave_bars.append((line, x))

    def animate_equalizer(self):
        """Animates 36 frequency spectrum bars with logarithmic dynamics."""
        try:
            if not self.wave_bars:
                self._init_wave_bars()

            center_y = 22
            is_spk = False
            try:
                is_spk = speaking_status() if callable(speaking_status) else bool(speaking_status)
            except Exception:
                pass

            for i in range(NUM_WAVE_BARS):
                target_h = self.fft_spectrum_levels[i]

                if self.audio_level > 85:
                    if target_h > self.current_display_heights[i]:
                        self.current_display_heights[i] = target_h
                    else:
                        self.current_display_heights[i] = max(2.0, self.current_display_heights[i] * 0.78)
                elif is_spk:
                    speech_h = 3.5 + 14.0 * abs(math.sin(time.time() * 9.5 + i * 0.38))
                    self.current_display_heights[i] = max(self.current_display_heights[i] * 0.76, speech_h)
                else:
                    self.current_display_heights[i] = max(2.0, self.current_display_heights[i] * 0.82)
                    ambient_h = 2.5 + 3.0 * math.sin(time.time() * 2.8 + i * 0.35)
                    self.current_display_heights[i] = max(self.current_display_heights[i], ambient_h)

                h = int(self.current_display_heights[i])
                line, x = self.wave_bars[i]
                self.wave_canvas.coords(line, x, center_y - h, x, center_y + h)

        except Exception:
            pass

        self.tk_root.after(35, self.animate_equalizer)

    def _start_mic_listener(self):
        """Background thread analyzing microphone input via Fast Fourier Transform."""
        def listener():
            try:
                p = pyaudio.PyAudio()
                stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
                while True:
                    try:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        self.audio_level = float(np.abs(audio_data).mean())

                        windowed = audio_data * self.hanning_window
                        fft_mag = np.abs(np.fft.rfft(windowed))

                        raw_bands = np.zeros(NUM_WAVE_BARS)
                        for i in range(NUM_WAVE_BARS):
                            m = self.band_masks[i]
                            if np.any(m):
                                raw_bands[i] = np.mean(fft_mag[m])

                        scaled_bands = np.log10(1.0 + raw_bands / 45.0)
                        self.fft_spectrum_levels = np.clip(scaled_bands * 7.5, 0.0, 19.0)

                    except Exception:
                        time.sleep(0.02)
            except Exception:
                pass

        threading.Thread(target=listener, daemon=True, name="FFTMicListener").start()
