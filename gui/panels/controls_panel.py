"""
Quick Controls Panel for J.A.R.V.I.S. Sci-Fi HUD
Manages system volume, screen brightness, connectivity toggles, vision scans,
and Stark telemetry/briefing trigger buttons.
"""

import time
import threading
import customtkinter as ctk

CYAN_BRIGHT = "#00f0ff"
TEXT_WHITE = "#ffffff"
TEXT_CYAN = "#80d8ff"
FONT_SMALL = ("Consolas", 10)

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


class ControlsPanel:
    def __init__(self, parent, panel_factory, notif_callback=None, display_callback=None, status_callback=None):
        self.notif_cb = notif_callback
        self.display_cb = display_callback
        self.status_cb = status_callback

        self.panel = panel_factory(parent, "QUICK CONTROLS", icon="🎛")
        self.panel.pack(fill="x", pady=(0, 4))

        self.content = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.content.pack(fill="x", padx=12, pady=(2, 4))

        # Volume Slider
        self.vol_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.vol_frame.pack(fill="x", pady=2)

        self.vol_head = ctk.CTkFrame(self.vol_frame, fg_color="transparent")
        self.vol_head.pack(fill="x")
        ctk.CTkLabel(self.vol_head, text="🔊 Volume", font=FONT_SMALL, text_color=TEXT_CYAN).pack(side="left")
        self.vol_val_lbl = ctk.CTkLabel(self.vol_head, text="70%", font=FONT_SMALL, text_color=TEXT_WHITE)
        self.vol_val_lbl.pack(side="right")

        self.vol_slider = ctk.CTkSlider(
            self.vol_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            progress_color=CYAN_BRIGHT,
            button_color=CYAN_BRIGHT,
            button_hover_color=TEXT_WHITE,
            height=14,
            command=self._on_volume_change
        )
        self.vol_slider.pack(fill="x", pady=(2, 4))
        self.vol_slider.set(70)

        # Brightness Slider
        self.bright_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.bright_frame.pack(fill="x", pady=2)

        self.bright_head = ctk.CTkFrame(self.bright_frame, fg_color="transparent")
        self.bright_head.pack(fill="x")
        ctk.CTkLabel(self.bright_head, text="☀ Brightness", font=FONT_SMALL, text_color=TEXT_CYAN).pack(side="left")
        self.bright_val_lbl = ctk.CTkLabel(self.bright_head, text="75%", font=FONT_SMALL, text_color=TEXT_WHITE)
        self.bright_val_lbl.pack(side="right")

        self.bright_slider = ctk.CTkSlider(
            self.bright_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            progress_color=CYAN_BRIGHT,
            button_color=CYAN_BRIGHT,
            button_hover_color=TEXT_WHITE,
            height=14,
            command=self._on_brightness_change
        )
        self.bright_slider.pack(fill="x", pady=(2, 4))
        self.bright_slider.set(75)

        # Toggles Row
        self.toggles_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.toggles_row.pack(fill="x", pady=(4, 0))

        self.wifi_state = [True]
        self.wifi_btn = ctk.CTkButton(
            self.toggles_row,
            text="Wi-Fi: On",
            width=72,
            height=24,
            font=FONT_SMALL,
            fg_color="#062238",
            border_color="#0088ff",
            border_width=1,
            command=self._toggle_wifi
        )
        self.wifi_btn.pack(side="left", padx=2)

        self.bt_state = [True]
        self.bt_btn = ctk.CTkButton(
            self.toggles_row,
            text="BT: On",
            width=60,
            height=24,
            font=FONT_SMALL,
            fg_color="#062238",
            border_color="#0088ff",
            border_width=1,
            command=self._toggle_bt
        )
        self.bt_btn.pack(side="left", padx=2)

        self.power_modes = ["Balanced", "Performance", "Eco", "Turbo"]
        self.power_idx = [0]
        self.power_btn = ctk.CTkButton(
            self.toggles_row,
            text="Balanced",
            width=76,
            height=24,
            font=FONT_SMALL,
            fg_color="#062238",
            border_color="#0088ff",
            border_width=1,
            command=self._cycle_power
        )
        self.power_btn.pack(side="left", padx=2)

        # Vision Actions Row
        self.vision_actions_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.vision_actions_row.pack(fill="x", pady=(4, 0))

        self.scan_screen_btn = ctk.CTkButton(
            self.vision_actions_row,
            text="👁 SCAN SCREEN",
            font=FONT_SMALL,
            fg_color="#0d2644",
            hover_color="#184b80",
            border_color=CYAN_BRIGHT,
            border_width=1,
            text_color=CYAN_BRIGHT,
            height=24,
            command=self._on_scan_screen
        )
        self.scan_screen_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.screenshot_btn = ctk.CTkButton(
            self.vision_actions_row,
            text="📸 CAPTURE",
            font=FONT_SMALL,
            fg_color="#0d2644",
            hover_color="#184b80",
            border_color="#0088ff",
            border_width=1,
            text_color=TEXT_WHITE,
            height=24,
            width=80,
            command=self._on_screenshot
        )
        self.screenshot_btn.pack(side="right", padx=(2, 0))

        # Stark Telemetry, Briefing & RAM Purge Actions Row
        self.stark_actions_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.stark_actions_row.pack(fill="x", pady=(4, 0))

        self.diag_btn = ctk.CTkButton(
            self.stark_actions_row,
            text="⚡ DIAG",
            font=FONT_SMALL,
            fg_color="#0d2644",
            hover_color="#184b80",
            border_color=CYAN_BRIGHT,
            border_width=1,
            text_color=CYAN_BRIGHT,
            height=24,
            command=self._on_diagnostics
        )
        self.diag_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.briefing_btn = ctk.CTkButton(
            self.stark_actions_row,
            text="🌅 BRIEF",
            font=FONT_SMALL,
            fg_color="#0d2644",
            hover_color="#184b80",
            border_color="#0088ff",
            border_width=1,
            text_color=TEXT_WHITE,
            height=24,
            command=self._on_briefing
        )
        self.briefing_btn.pack(side="left", fill="x", expand=True, padx=2)

        self.purge_btn = ctk.CTkButton(
            self.stark_actions_row,
            text="🧹 PURGE",
            font=FONT_SMALL,
            fg_color="#0d2644",
            hover_color="#184b80",
            border_color=CYAN_BRIGHT,
            border_width=1,
            text_color=CYAN_BRIGHT,
            height=24,
            command=self._on_purge_ram
        )
        self.purge_btn.pack(side="right", fill="x", expand=True, padx=(2, 0))

        # Hand Gesture Control Action Row
        self.gesture_actions_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.gesture_actions_row.pack(fill="x", pady=(4, 0))

        self.gesture_btn = ctk.CTkButton(
            self.gesture_actions_row,
            text="🖐 GESTURES: OFF",
            font=FONT_SMALL,
            fg_color="#0a1f33",
            hover_color="#123a5e",
            border_color="#0088ff",
            border_width=1,
            text_color="#80d8ff",
            height=24,
            command=self._on_toggle_gestures
        )
        self.gesture_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.gesture_cam_btn = ctk.CTkButton(
            self.gesture_actions_row,
            text="👁 HUD VIEW",
            font=FONT_SMALL,
            fg_color="#0a1f33",
            hover_color="#123a5e",
            border_color="#0088ff",
            border_width=1,
            text_color="#80d8ff",
            height=24,
            width=90,
            command=self._on_toggle_camera_hud
        )
        self.gesture_cam_btn.pack(side="right", padx=(2, 0))

    def _notify(self, text):
        if self.notif_cb:
            try:
                self.notif_cb(text)
            except Exception:
                pass

    def _on_volume_change(self, val):
        val_int = int(val)
        self.vol_val_lbl.configure(text=f"{val_int}%")
        if HAS_PYCAW:
            try:
                sp = AudioUtilities.GetSpeakers()
                sp.EndpointVolume.SetMasterVolumeLevelScalar(val_int / 100.0, None)
            except Exception:
                pass

    def _on_brightness_change(self, val):
        val_int = int(val)
        self.bright_val_lbl.configure(text=f"{val_int}%")
        if HAS_SBC:
            try:
                sbc.set_brightness(val_int)
            except Exception:
                pass

    def _toggle_wifi(self):
        self.wifi_state[0] = not self.wifi_state[0]
        self.wifi_btn.configure(
            text=f"Wi-Fi: {'On' if self.wifi_state[0] else 'Off'}",
            fg_color="#062238" if self.wifi_state[0] else "#2a0a14"
        )
        self._notify(f"Wi-Fi state changed to {'Online' if self.wifi_state[0] else 'Offline'}")

    def _toggle_bt(self):
        self.bt_state[0] = not self.bt_state[0]
        self.bt_btn.configure(
            text=f"BT: {'On' if self.bt_state[0] else 'Off'}",
            fg_color="#062238" if self.bt_state[0] else "#2a0a14"
        )
        self._notify(f"Bluetooth state changed to {'Online' if self.bt_state[0] else 'Offline'}")

    def _cycle_power(self):
        self.power_idx[0] = (self.power_idx[0] + 1) % len(self.power_modes)
        mode = self.power_modes[self.power_idx[0]]
        self.power_btn.configure(text=mode)
        self._notify(f"Power profile switched to {mode}")

    def _on_scan_screen(self):
        def worker():
            try:
                if self.display_cb:
                    self.display_cb("Scanning active display buffer with Gemma3 Vision...")
                if self.status_cb:
                    self.status_cb("blue")
                from vision import analyze_screen
                result = analyze_screen("Describe what is currently visible on the screen in 2 to 3 concise sentences.")
                if self.display_cb:
                    self.display_cb(result)
                if self.status_cb:
                    self.status_cb("green")
                from voice_engine.voice import speak
                speak(result)
                if self.status_cb:
                    self.status_cb("yellow")
            except Exception as e:
                if self.display_cb:
                    self.display_cb(f"Vision Scan Error: {e}")
                if self.status_cb:
                    self.status_cb("yellow")
        threading.Thread(target=worker, daemon=True).start()

    def _on_screenshot(self):
        def worker():
            try:
                from vision import save_screenshot
                res = save_screenshot()
                self._notify(res)
                if self.display_cb:
                    self.display_cb(res)
                from voice_engine.voice import speak
                speak(res)
            except Exception as e:
                self._notify(f"Screenshot Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _on_diagnostics(self):
        def worker():
            try:
                from system_layer.diagnostics_controller import format_spoken_diagnostics
                res = format_spoken_diagnostics()
                self._notify(res)
                if self.display_cb:
                    self.display_cb(res)
                from voice_engine.voice import speak
                speak(res)
            except Exception as e:
                self._notify(f"Diagnostics Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _on_briefing(self):
        def worker():
            try:
                from system_layer.briefing_controller import generate_executive_briefing
                res = generate_executive_briefing()
                self._notify(res)
                if self.display_cb:
                    self.display_cb(res)
                from voice_engine.voice import speak
                speak(res)
            except Exception as e:
                self._notify(f"Briefing Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _on_purge_ram(self):
        def worker():
            try:
                self.purge_btn.configure(text="CLEANING...", state="disabled")
                from system_layer.system_control import purge_system_ram
                res = purge_system_ram()
                self._notify(f"RAM Purged: {res['freed_mb']}MB freed ({res['processes_trimmed']} procs).")
                if self.display_cb:
                    self.display_cb(
                        f"Memory optimization complete: {res['freed_mb']} MB reclaimed across "
                        f"{res['processes_trimmed']} processes. Current load: {res['percent_after']}%."
                    )
                self.purge_btn.configure(text="✓ PURGED", fg_color="#0d4422", border_color="#00ff88", text_color="#00ff88")
                time.sleep(2.0)
            except Exception as e:
                self._notify(f"Purge error: {str(e)[:30]}")
            finally:
                try:
                    self.purge_btn.configure(
                        text="🧹 PURGE",
                        fg_color="#0d2644",
                        border_color=CYAN_BRIGHT,
                        text_color=CYAN_BRIGHT,
                        state="normal"
                    )
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _on_toggle_gestures(self):
        try:
            from system_layer.gesture_controller import gesture_controller
            if gesture_controller.is_active():
                msg = gesture_controller.stop()
                self.gesture_btn.configure(
                    text="🖐 GESTURES: OFF",
                    fg_color="#0a1f33",
                    border_color="#0088ff",
                    text_color="#80d8ff"
                )
                self.gesture_cam_btn.configure(
                    fg_color="#0a1f33",
                    border_color="#0088ff",
                    text_color="#80d8ff"
                )
                self._notify(msg)
            else:
                msg = gesture_controller.start(notif_callback=self._notify, show_preview=True)
                self.gesture_btn.configure(
                    text="🖐 GESTURES: ON",
                    fg_color="#063828",
                    border_color="#00ff88",
                    text_color="#00ff88"
                )
                self.gesture_cam_btn.configure(
                    fg_color="#063828",
                    border_color="#00ff88",
                    text_color="#00ff88"
                )
                self._notify(msg)
        except Exception as e:
            self._notify(f"Gesture toggle error: {e}")

    def _on_toggle_camera_hud(self):
        try:
            from system_layer.gesture_controller import gesture_controller
            if not gesture_controller.is_active():
                self._notify("Activate gestures first before toggling camera view.")
                return
            is_vis = gesture_controller.toggle_preview()
            self.gesture_cam_btn.configure(
                fg_color="#063828" if is_vis else "#0a1f33",
                border_color="#00ff88" if is_vis else "#0088ff",
                text_color="#00ff88" if is_vis else "#80d8ff"
            )
            self._notify(f"Gesture Camera HUD: {'Shown' if is_vis else 'Hidden'}")
        except Exception as e:
            self._notify(f"HUD View error: {e}")

    def sync_hardware(self):
        """Initial sync for volume and brightness sliders."""
        if HAS_PYCAW:
            try:
                sp = AudioUtilities.GetSpeakers()
                v = int(sp.EndpointVolume.GetMasterVolumeLevelScalar() * 100)
                self.vol_slider.set(v)
                self.vol_val_lbl.configure(text=f"{v}%")
            except Exception:
                pass
        if HAS_SBC:
            try:
                b = sbc.get_brightness()[0]
                self.bright_slider.set(b)
                self.bright_val_lbl.configure(text=f"{b}%")
            except Exception:
                pass
