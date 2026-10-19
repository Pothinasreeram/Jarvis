"""
Telemetry & System Status Panel for J.A.R.V.I.S. Sci-Fi HUD
Builds radial CPU & RAM gauges, network speedometer, battery bar, and status badges.
"""

import time
import psutil
import tkinter as tk
import customtkinter as ctk

CYAN_BRIGHT = "#00f0ff"
GREEN_ACCENT = "#00ff88"
TEXT_WHITE = "#ffffff"
TEXT_CYAN = "#80d8ff"
TEXT_MUTED = "#607d8b"
TROUGH_BG = "#031020"
PANEL_BORDER_DIM = "#003355"
FONT_SMALL = ("Consolas", 10)


class TelemetryPanel:
    def __init__(self, parent, panel_factory):
        self.panel = panel_factory(parent, "SYSTEM STATUS", icon="⚡")
        self.panel.pack(fill="x", pady=(0, 8))

        self.content = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.content.pack(fill="x", padx=12, pady=(4, 10))

        # Canvas for CPU & RAM radial gauges
        self.width = 260
        self.height = 96
        self.canvas = tk.Canvas(
            self.content,
            width=self.width,
            height=self.height,
            bg="#030c1a",
            highlightthickness=1,
            highlightbackground=PANEL_BORDER_DIM
        )
        self.canvas.pack(fill="x", pady=(2, 6))

        # Static gauge tracks
        self._init_gauge_track(65, 44, r=32, label="CPU LOAD")
        self._init_gauge_track(195, 44, r=32, label="RAM ALLOC")

        # Dynamic gauge arcs & text
        self.cpu_arc = self.canvas.create_arc(33, 12, 97, 76, start=210, extent=-1, style="arc", width=5, outline=CYAN_BRIGHT)
        self.cpu_text = self.canvas.create_text(65, 40, text="0%", fill=TEXT_WHITE, font=("Consolas", 11, "bold"))

        self.ram_arc = self.canvas.create_arc(163, 12, 227, 76, start=210, extent=-1, style="arc", width=5, outline=CYAN_BRIGHT)
        self.ram_text = self.canvas.create_text(195, 40, text="0%", fill=TEXT_WHITE, font=("Consolas", 11, "bold"))

        # Detailed RAM readout
        self.ram_detail_lbl = ctk.CTkLabel(
            self.content,
            text="MEM ALLOC: 0.0 / 0.0 GB",
            font=FONT_SMALL,
            text_color=TEXT_CYAN
        )
        self.ram_detail_lbl.pack(fill="x", pady=(0, 2))

        # Live Network Speedometer
        self.net_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.net_frame.pack(fill="x", pady=2)

        self.net_down_lbl = ctk.CTkLabel(self.net_frame, text="↓ 0.0 KB/s", font=FONT_SMALL, text_color=GREEN_ACCENT)
        self.net_down_lbl.pack(side="left")

        self.net_up_lbl = ctk.CTkLabel(self.net_frame, text="↑ 0.0 KB/s", font=FONT_SMALL, text_color=CYAN_BRIGHT)
        self.net_up_lbl.pack(side="right")

        # Battery Row
        self.batt_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.batt_row.pack(fill="x", pady=2)

        self.batt_head = ctk.CTkFrame(self.batt_row, fg_color="transparent")
        self.batt_head.pack(fill="x")

        self.batt_title_lbl = ctk.CTkLabel(self.batt_head, text="⚡ BATTERY (AC)", font=FONT_SMALL, text_color=TEXT_CYAN)
        self.batt_title_lbl.pack(side="left")

        self.batt_val_lbl = ctk.CTkLabel(self.batt_head, text="100%", font=FONT_SMALL, text_color=TEXT_WHITE)
        self.batt_val_lbl.pack(side="right")

        self.batt_bar = ctk.CTkProgressBar(
            self.batt_row,
            fg_color=TROUGH_BG,
            progress_color=CYAN_BRIGHT,
            height=6,
            corner_radius=3
        )
        self.batt_bar.pack(fill="x", pady=(2, 0))
        self.batt_bar.set(1.0)

        # Status Badges
        self.status_badges = ctk.CTkFrame(self.content, fg_color="transparent")
        self.status_badges.pack(fill="x", pady=(6, 2))

        self.net_badge_lbl = ctk.CTkLabel(self.status_badges, text="NET: ONLINE", font=FONT_SMALL, text_color=GREEN_ACCENT)
        self.net_badge_lbl.pack(side="left")

        self.voice_badge_lbl = ctk.CTkLabel(self.status_badges, text="VOICE: READY", font=FONT_SMALL, text_color=CYAN_BRIGHT)
        self.voice_badge_lbl.pack(side="right")

        self.focus_badge_lbl = ctk.CTkLabel(self.content, text="FOCUS GUARD: STANDBY", font=FONT_SMALL, text_color=TEXT_MUTED)
        self.focus_badge_lbl.pack(fill="x", pady=(2, 1))

        self.sentry_badge_lbl = ctk.CTkLabel(self.content, text="SENTRY GUARD: STANDBY", font=FONT_SMALL, text_color=TEXT_MUTED)
        self.sentry_badge_lbl.pack(fill="x", pady=(1, 1))

        self.wellness_badge_lbl = ctk.CTkLabel(self.content, text="WELLNESS: ACTIVE (0m | 0/8 💧)", font=FONT_SMALL, text_color=CYAN_BRIGHT)
        self.wellness_badge_lbl.pack(fill="x", pady=(1, 1))

        self.gesture_badge_lbl = ctk.CTkLabel(self.content, text="GESTURES: STANDBY", font=FONT_SMALL, text_color=TEXT_MUTED)
        self.gesture_badge_lbl.pack(fill="x", pady=(1, 2))

        self.last_net_bytes = [None, None, 0.0]

    def _init_gauge_track(self, cx, cy, r=32, label="CPU LOAD"):
        self.canvas.create_oval(cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4, outline="#08182b", width=1)
        self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=210, extent=-240, style="arc", width=5, outline="#0d2238")
        self.canvas.create_oval(cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8, outline="#091a2e", width=1)
        self.canvas.create_text(cx, cy + 22, text=label, fill="#5a7090", font=("Consolas", 8, "bold"))

    def update_stats(self, speaking_status_fn=None):
        """Update telemetry metrics, gauges, and status badges."""
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            ram = mem.percent
            batt = psutil.sensors_battery()
            batt_val = batt.percent if batt else 100
            batt_plugged = batt.power_plugged if batt else True

            # 1. CPU Gauge
            cpu_extent = -max(1.0, min(240.0, 240.0 * (cpu / 100.0)))
            cpu_color = CYAN_BRIGHT if cpu < 50 else ("#f59e0b" if cpu < 80 else "#ff3b30")
            self.canvas.itemconfigure(self.cpu_arc, extent=cpu_extent, outline=cpu_color)
            self.canvas.itemconfigure(self.cpu_text, text=f"{cpu:.0f}%", fill=cpu_color)

            # 2. RAM Gauge
            ram_extent = -max(1.0, min(240.0, 240.0 * (ram / 100.0)))
            ram_color = CYAN_BRIGHT if ram < 60 else ("#38bdf8" if ram < 85 else "#ff3b30")
            self.canvas.itemconfigure(self.ram_arc, extent=ram_extent, outline=ram_color)
            self.canvas.itemconfigure(self.ram_text, text=f"{ram:.0f}%", fill=ram_color)

            # 3. RAM Detail
            used_gb = mem.used / (1024**3)
            total_gb = mem.total / (1024**3)
            self.ram_detail_lbl.configure(text=f"MEM ALLOC: {used_gb:.1f} / {total_gb:.1f} GB")

            # 4. Network Speedometer
            now = time.time()
            net_io = psutil.net_io_counters()
            if self.last_net_bytes[0] is not None and (now - self.last_net_bytes[2]) > 0:
                dt = now - self.last_net_bytes[2]
                down_rate = (net_io.bytes_recv - self.last_net_bytes[0]) / dt
                up_rate = (net_io.bytes_sent - self.last_net_bytes[1]) / dt

                def fmt(r):
                    kb = max(0.0, r / 1024.0)
                    return f"{kb:.1f} KB/s" if kb < 1024 else f"{kb / 1024.0:.2f} MB/s"

                self.net_down_lbl.configure(text=f"↓ {fmt(down_rate)}")
                self.net_up_lbl.configure(text=f"↑ {fmt(up_rate)}")

            self.last_net_bytes[0] = net_io.bytes_recv
            self.last_net_bytes[1] = net_io.bytes_sent
            self.last_net_bytes[2] = now

            # 5. Battery
            self.batt_val_lbl.configure(text=f"{batt_val:.0f}% {'⚡' if batt_plugged else ''}")
            self.batt_title_lbl.configure(text=f"⚡ BATTERY ({'AC' if batt_plugged else 'DC'})")
            self.batt_bar.set(batt_val / 100.0)
            if batt_plugged:
                self.batt_bar.configure(progress_color=GREEN_ACCENT)
            elif batt_val > 30:
                self.batt_bar.configure(progress_color=CYAN_BRIGHT)
            else:
                self.batt_bar.configure(progress_color="#ff3b30")

            # 6. Badges
            voice_busy = False
            if speaking_status_fn:
                try:
                    voice_busy = speaking_status_fn() if callable(speaking_status_fn) else bool(speaking_status_fn)
                except Exception:
                    pass

            is_priv = False
            try:
                from wake_word import is_privacy_muted
                is_priv = is_privacy_muted()
            except Exception:
                pass

            if is_priv:
                self.voice_badge_lbl.configure(text="MIC: MUTED [PRIVACY]", text_color="#ff3b30")
            else:
                self.voice_badge_lbl.configure(
                    text=f"VOICE: {'SPEAKING' if voice_busy else 'READY'}",
                    text_color=GREEN_ACCENT if voice_busy else CYAN_BRIGHT
                )

            # Focus Guard Badge
            try:
                from background_tasks.focus_guard import get_focus_status
                f_stat = get_focus_status()
                if f_stat.get("active"):
                    self.focus_badge_lbl.configure(text=f"FOCUS: {f_stat.get('remaining_str')} [ACTIVE]", text_color=CYAN_BRIGHT)
                else:
                    self.focus_badge_lbl.configure(text="FOCUS GUARD: STANDBY", text_color=TEXT_MUTED)
            except Exception:
                pass

            # Sentry Badge
            try:
                from background_tasks.sentry_guard import is_sentry_active
                if is_sentry_active():
                    self.sentry_badge_lbl.configure(text="SENTRY: ARMED 👁", text_color=GREEN_ACCENT)
                else:
                    self.sentry_badge_lbl.configure(text="SENTRY GUARD: STANDBY", text_color=TEXT_MUTED)
            except Exception:
                pass

            # Wellness Badge
            try:
                from background_tasks.wellness_monitor import get_wellness_summary
                w_sum = get_wellness_summary()
                if w_sum.get("active"):
                    self.wellness_badge_lbl.configure(text=f"WELLNESS: {w_sum.get('badge_text', 'ACTIVE')}", text_color=CYAN_BRIGHT)
                else:
                    self.wellness_badge_lbl.configure(text="WELLNESS: STANDBY", text_color=TEXT_MUTED)
            except Exception:
                pass

            # Gesture Recognition Badge
            try:
                from system_layer.gesture_controller import gesture_controller
                if gesture_controller.is_active():
                    last_g = gesture_controller.get_last_gesture()
                    self.gesture_badge_lbl.configure(text=f"GESTURES: ACTIVE [{last_g}] 🖐", text_color=GREEN_ACCENT)
                else:
                    self.gesture_badge_lbl.configure(text="GESTURES: STANDBY", text_color=TEXT_MUTED)
            except Exception:
                pass

        except Exception:
            pass
