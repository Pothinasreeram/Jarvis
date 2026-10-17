"""
Media Controller Panel for J.A.R.V.I.S. Sci-Fi HUD
Handles track metadata polling, play/pause, previous/next, and visual playback status.
"""

import time
import threading
import customtkinter as ctk

CYAN_BRIGHT = "#00f0ff"
GREEN_ACCENT = "#00ff88"
TEXT_WHITE = "#ffffff"
TEXT_CYAN = "#80d8ff"
TEXT_MUTED = "#607d8b"
FONT_SMALL = ("Consolas", 10)


class MediaPanel:
    def __init__(self, parent, panel_factory, notif_callback=None):
        self.notif_cb = notif_callback
        self.panel = panel_factory(parent, "MEDIA CONTROLLER", icon="🎵")
        self.panel.pack(fill="x", pady=(0, 8))

        self.info_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=10, pady=(2, 4))

        self.header_row = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.header_row.pack(fill="x")

        self.title_lbl = ctk.CTkLabel(
            self.header_row,
            text="No Media Active",
            font=("Consolas", 11, "bold"),
            text_color=CYAN_BRIGHT
        )
        self.title_lbl.pack(side="left")

        self.status_lbl = ctk.CTkLabel(
            self.header_row,
            text="● IDLE",
            font=FONT_SMALL,
            text_color=TEXT_MUTED
        )
        self.status_lbl.pack(side="right")

        self.artist_lbl = ctk.CTkLabel(
            self.info_frame,
            text="Spotify / Windows Media",
            font=FONT_SMALL,
            text_color=TEXT_MUTED
        )
        self.artist_lbl.pack(anchor="w")

        # Media Control Buttons Row
        self.btn_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.btn_row.pack(fill="x", padx=10, pady=(2, 6))

        self.prev_btn = ctk.CTkButton(
            self.btn_row,
            text="⏮ PREV",
            font=FONT_SMALL,
            fg_color="#0a1a2e",
            hover_color="#133055",
            border_color="#0088ff",
            border_width=1,
            text_color=TEXT_CYAN,
            height=22,
            width=60,
            command=self._on_prev
        )
        self.prev_btn.pack(side="left", padx=(0, 2), expand=True, fill="x")

        self.play_btn = ctk.CTkButton(
            self.btn_row,
            text="⏯ PLAY/PAUSE",
            font=FONT_SMALL,
            fg_color="#0d2644",
            hover_color="#184b80",
            border_color=CYAN_BRIGHT,
            border_width=1,
            text_color=CYAN_BRIGHT,
            height=22,
            width=90,
            command=self._on_playpause
        )
        self.play_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.next_btn = ctk.CTkButton(
            self.btn_row,
            text="⏭ NEXT",
            font=FONT_SMALL,
            fg_color="#0a1a2e",
            hover_color="#133055",
            border_color="#0088ff",
            border_width=1,
            text_color=TEXT_CYAN,
            height=22,
            width=60,
            command=self._on_next
        )
        self.next_btn.pack(side="left", padx=(2, 0), expand=True, fill="x")

        self.cache = {"title": "No Media Active", "artist": "Spotify / Windows Media", "playing": False}
        self._start_poller()

    def _notify(self, text):
        if self.notif_cb:
            try:
                self.notif_cb(text)
            except Exception:
                pass

    def _on_prev(self):
        def worker():
            try:
                from system_layer.spotify_controller import media_previous
                res = media_previous()
                self._notify(res)
            except Exception as e:
                self._notify(f"Media Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _on_playpause(self):
        def worker():
            try:
                from system_layer.spotify_controller import toggle_play_pause
                res = toggle_play_pause()
                self._notify(res)
            except Exception as e:
                self._notify(f"Media Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _on_next(self):
        def worker():
            try:
                from system_layer.spotify_controller import media_next
                res = media_next()
                self._notify(res)
            except Exception as e:
                self._notify(f"Media Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _start_poller(self):
        def poll():
            while True:
                try:
                    from system_layer.spotify_controller import get_current_track_info
                    info = get_current_track_info()
                    if info and info.get("title"):
                        self.cache["title"] = info["title"]
                        self.cache["artist"] = info.get("artist", "")
                        self.cache["playing"] = info.get("playing", False)
                    else:
                        self.cache["title"] = "No Media Active"
                        self.cache["artist"] = "Spotify / Windows Media"
                        self.cache["playing"] = False
                except Exception:
                    pass
                time.sleep(2.5)
        threading.Thread(target=poll, daemon=True, name="MediaPollerThread").start()

    def update_display(self):
        """Update media labels based on cached track info."""
        try:
            title = self.cache.get("title", "No Media Active")
            artist = self.cache.get("artist", "")
            playing = self.cache.get("playing", False)

            display_title = (title[:22] + "...") if len(title) > 24 else title
            self.title_lbl.configure(text=display_title)
            self.artist_lbl.configure(text=artist[:26] if artist else "Media Standby")

            if playing:
                self.status_lbl.configure(text="● PLAYING", text_color=GREEN_ACCENT)
            else:
                self.status_lbl.configure(text="● IDLE", text_color=TEXT_MUTED)
        except Exception:
            pass
