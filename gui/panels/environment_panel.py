"""
Live Environment Panel for J.A.R.V.I.S. Sci-Fi HUD
Displays real-time clock, local weather (temperature, condition, humidity, wind).
"""

import threading
from datetime import datetime
import customtkinter as ctk
from system_layer.weather_controller import get_weather_data

CYAN_BRIGHT = "#00f0ff"
TEXT_WHITE = "#ffffff"
TEXT_CYAN = "#80d8ff"
TEXT_MUTED = "#607d8b"
FONT_SMALL = ("Consolas", 10)
FONT_VALUE = ("Consolas", 14, "bold")


class EnvironmentPanel:
    def __init__(self, parent, panel_factory, city="Vadodara"):
        self.city = city
        self.panel = panel_factory(parent, "LIVE ENVIRONMENT", icon="⛅")
        self.panel.pack(fill="x", pady=(0, 8))

        self.header = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.header.pack(fill="x", padx=12, pady=(0, 2))

        self.location_lbl = ctk.CTkLabel(self.header, text=f"{city}, India", font=FONT_SMALL, text_color=TEXT_MUTED)
        self.location_lbl.pack(side="left")

        self.clock_lbl = ctk.CTkLabel(self.header, text="--:--:--", font=FONT_VALUE, text_color=CYAN_BRIGHT)
        self.clock_lbl.pack(side="right")

        self.content = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.content.pack(fill="x", padx=12, pady=(4, 8))

        self.temp_lbl = ctk.CTkLabel(
            self.content,
            text="29°C",
            font=("Consolas", 24, "bold"),
            text_color=TEXT_WHITE
        )
        self.temp_lbl.pack(side="left", padx=(0, 10))

        self.details = ctk.CTkFrame(self.content, fg_color="transparent")
        self.details.pack(side="right", anchor="e")

        self.cond_lbl = ctk.CTkLabel(self.details, text="Condition: Clear", font=FONT_SMALL, text_color=TEXT_CYAN)
        self.cond_lbl.pack(anchor="e")

        self.hum_lbl = ctk.CTkLabel(self.details, text="Humidity: 60%", font=FONT_SMALL, text_color=TEXT_CYAN)
        self.hum_lbl.pack(anchor="e")

        self.wind_lbl = ctk.CTkLabel(self.details, text="Wind: 5.0 km/h", font=FONT_SMALL, text_color=TEXT_CYAN)
        self.wind_lbl.pack(anchor="e")

    def update_clock(self):
        """Update live clock string."""
        now = datetime.now()
        self.clock_lbl.configure(text=now.strftime("%I:%M:%S %p"))

    def fetch_weather(self, tk_root):
        """Asynchronously fetch weather without blocking UI."""
        def worker():
            try:
                data = get_weather_data(self.city)
                if data:
                    temp = data.get("temperature", 29)
                    hum = data.get("humidity", 60)
                    wind = data.get("wind", 5.0)
                    cond = data.get("condition", "Clear")

                    tk_root.after(0, lambda: self.temp_lbl.configure(text=f"{temp:.0f}°C"))
                    tk_root.after(0, lambda: self.cond_lbl.configure(text=f"Condition: {cond}"))
                    tk_root.after(0, lambda: self.hum_lbl.configure(text=f"Humidity: {hum}%"))
                    tk_root.after(0, lambda: self.wind_lbl.configure(text=f"Wind: {wind} km/h"))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True, name="WeatherFetchThread").start()
