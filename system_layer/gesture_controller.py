"""
Hand Gesture Recognition Controller for J.A.R.V.I.S.
Powered by MediaPipe Hand Gesture Recognizer (21 3D landmarks + neural classification).

Supported Gestures:
- Open Palm:   Immediate speech halt / Voice interruption.
- Victory (✌): Triggers Tony Stark Executive Morning Briefing.
- Thumb Up:    Media Play / Resume playback.
- Thumb Down:  Media Pause playback.
- Pointing Up: Fast Volume Up (+5%).
- Pinch:       Vertical mid-air volume slider (pinch thumb + index and move up/down).
"""

import os
import time
import math
import threading
import cv2
import numpy as np

# MediaPipe Tasks Vision API
try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    HAS_MEDIAPIPE = True
except Exception:
    HAS_MEDIAPIPE = False

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "models", "gesture_recognizer.task")

# Optional pycaw for hardware volume
try:
    from pycaw.pycaw import AudioUtilities
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

# Sound effects
try:
    from voice_engine.sound_effects import play_fx
except Exception:
    def play_fx(name):
        pass

# Hand Skeleton Bone Connections for Visualization
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky & Palm
]


class GestureController:
    def __init__(self):
        self._running = False
        self._thread = None
        self._last_gesture = "NONE"
        self._last_score = 0.0
        self._last_trigger_time = 0.0
        self._cooldown_seconds = 1.8
        self._pinch_active = False
        self._last_pinch_y = None
        self._notif_cb = None
        self._status_cb = None
        self._show_preview = True
        self._action_banner = ""
        self._action_banner_time = 0.0

    def is_active(self) -> bool:
        return self._running

    def get_last_gesture(self) -> str:
        if self._last_gesture != "NONE" and self._last_score > 0:
            return f"{self._last_gesture} ({int(self._last_score * 100)}%)"
        return self._last_gesture

    def is_preview_visible(self) -> bool:
        return self._show_preview

    def set_preview(self, enable: bool):
        self._show_preview = enable
        if not enable:
            try:
                cv2.destroyWindow("J.A.R.V.I.S. // GESTURE HUD")
            except Exception:
                pass

    def toggle_preview(self) -> bool:
        self.set_preview(not self._show_preview)
        return self._show_preview

    def _notify(self, text: str):
        if self._notif_cb:
            try:
                self._notif_cb(text)
            except Exception:
                pass

    def _trigger_feedback(self, banner_text: str):
        self._action_banner = banner_text
        self._action_banner_time = time.time()
        try:
            play_fx("ack")
        except Exception:
            pass

    def _change_volume(self, delta: int):
        """Adjust system master volume by delta percent (-100 to +100)."""
        if not HAS_PYCAW:
            return
        try:
            sp = AudioUtilities.GetSpeakers()
            current = sp.EndpointVolume.GetMasterVolumeLevelScalar()
            new_vol = max(0.0, min(1.0, current + (delta / 100.0)))
            sp.EndpointVolume.SetMasterVolumeLevelScalar(new_vol, None)
            pct = int(new_vol * 100)
            self._trigger_feedback(f"VOLUME SET: {pct}%")
            self._notify(f"Gesture Volume: {pct}%")
        except Exception:
            pass

    def _handle_open_palm(self):
        """Open palm: Immediately halts speech."""
        from voice_engine.voice import speaking_status, stop_speaking
        if speaking_status():
            stop_speaking()
            self._trigger_feedback("HALT SPEECH")
            self._notify("🖐 Open Palm: Voice output interrupted.")
        else:
            self._trigger_feedback("OPEN PALM (STANDBY)")
            self._notify("🖐 Open Palm detected (Voice is idle).")

    def _handle_victory(self):
        """Victory (peace sign): Launches executive morning briefing."""
        def worker():
            try:
                self._trigger_feedback("EXECUTIVE BRIEFING")
                self._notify("✌ Victory sign: Launching Morning Briefing...")
                from system_layer.briefing_controller import generate_executive_briefing
                from voice_engine.voice import speak
                res = generate_executive_briefing()
                self._notify(res[:45] + "...")
                speak(res)
            except Exception as e:
                self._notify(f"Briefing error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _handle_thumb_up(self):
        """Thumbs up: Resume playback or next track."""
        def worker():
            try:
                from system_layer.spotify_controller import toggle_play_pause
                res = toggle_play_pause()
                self._trigger_feedback("RESUME PLAYBACK")
                self._notify(f"👍 Thumbs Up: {res}")
            except Exception as e:
                self._notify(f"Media error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _handle_thumb_down(self):
        """Thumbs down: Pause playback."""
        def worker():
            try:
                from system_layer.spotify_controller import toggle_play_pause
                res = toggle_play_pause()
                self._trigger_feedback("PAUSE MEDIA")
                self._notify(f"👎 Thumbs Down: Pausing media ({res})")
            except Exception as e:
                self._notify(f"Media error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _handle_pointing_up(self):
        """Pointing up: Quick volume boost."""
        self._change_volume(+5)

    def _process_pinch(self, landmarks):
        """Detect thumb-to-index pinch distance and vertical movement for air volume control."""
        thumb = landmarks[4]
        index = landmarks[8]

        dx = thumb.x - index.x
        dy = thumb.y - index.y
        dist = math.sqrt(dx * dx + dy * dy)

        # Pinch threshold (approx. 5.5% of frame width)
        if dist < 0.055:
            current_y = (thumb.y + index.y) / 2.0
            if self._pinch_active and self._last_pinch_y is not None:
                diff_y = self._last_pinch_y - current_y  # Moving UP is negative in screen coordinates
                if abs(diff_y) > 0.025:
                    delta = int(diff_y * 120)
                    self._change_volume(delta)
                    self._last_pinch_y = current_y
            else:
                self._pinch_active = True
                self._last_pinch_y = current_y
                self._trigger_feedback("PINCH VOLUME ENGAGED")
        else:
            self._pinch_active = False
            self._last_pinch_y = None

    def start(self, notif_callback=None, show_preview: bool = True) -> str:
        """Start the gesture recognition thread."""
        if not HAS_MEDIAPIPE:
            return "MediaPipe library not installed."
        if not os.path.exists(MODEL_PATH):
            return "Gesture recognizer model file missing."
        if self._running:
            return "Gesture recognition is already active."

        self._notif_cb = notif_callback
        self._show_preview = show_preview
        self._running = True

        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="GestureEngineThread")
        self._thread.start()
        return "Hand gesture control activated. Point camera at hand."

    def stop(self) -> str:
        """Stop the gesture recognition thread and release camera."""
        if not self._running:
            return "Gesture recognition is not running."
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.5)
            self._thread = None
        self._pinch_active = False
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        return "Hand gesture control deactivated."

    def _draw_hud_overlay(self, frame, landmarks_list, gesture_name, score):
        """Draws Iron Man holographic cyan landmarks and UI HUD overlay onto the camera frame."""
        h, w, _ = frame.shape

        # 1. Draw glowing hand skeleton
        if landmarks_list and len(landmarks_list) > 0:
            landmarks = landmarks_list[0]
            pts = []
            for lm in landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                pts.append((cx, cy))

            # Draw bones
            for p1, p2 in HAND_CONNECTIONS:
                if p1 < len(pts) and p2 < len(pts):
                    cv2.line(frame, pts[p1], pts[p2], (255, 240, 0), 2, cv2.LINE_AA) # Neon Cyan

            # Draw joints
            for cx, cy in pts:
                cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1, cv2.LINE_AA)    # Bright Yellow-Cyan
                cv2.circle(frame, (cx, cy), 6, (255, 200, 0), 1, cv2.LINE_AA)

            # Highlight pinch tips
            if len(pts) > 8:
                tx, ty = pts[4]
                ix, iy = pts[8]
                if self._pinch_active:
                    cv2.line(frame, (tx, ty), (ix, iy), (0, 255, 100), 3, cv2.LINE_AA) # Green active pinch line
                    cv2.circle(frame, ((tx + ix) // 2, (ty + iy) // 2), 7, (0, 255, 100), -1)
                else:
                    cv2.line(frame, (tx, ty), (ix, iy), (255, 150, 0), 1, cv2.LINE_AA)

        # 2. Top Header HUD Banner
        cv2.rectangle(frame, (0, 0), (w, 42), (10, 15, 25), -1)
        cv2.line(frame, (0, 42), (w, 42), (255, 240, 0), 1)
        cv2.putText(frame, "J.A.R.V.I.S. // NEURAL GESTURE HUD", (12, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 240, 0), 2, cv2.LINE_AA)

        # 3. Gesture Status Readout
        status_text = f"GESTURE: {gesture_name}"
        if score > 0:
            status_text += f" ({int(score * 100)}%)"

        text_color = (0, 255, 100) if gesture_name not in ["NONE", ""] else (150, 180, 200)
        cv2.putText(frame, status_text, (12, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, text_color, 2, cv2.LINE_AA)

        # 4. Action Banner / Feedback Cue
        now = time.time()
        if (now - self._action_banner_time) < 2.2 and self._action_banner:
            # Pulsing trigger feedback banner
            cv2.rectangle(frame, (10, h - 50), (w - 10, h - 10), (0, 40, 20), -1)
            cv2.rectangle(frame, (10, h - 50), (w - 10, h - 10), (0, 255, 100), 2)
            cv2.putText(frame, f"ACTION: {self._action_banner}", (20, h - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)

        # 5. Instructions footer
        cv2.putText(frame, "Open Palm: Stop | Peace: Briefing | Pinch: Volume | Thumbs: Play/Pause",
                    (10, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (140, 160, 180), 1, cv2.LINE_AA)

    def _run_loop(self):
        """Main webcam capture and neural gesture classification loop."""
        cap = None
        try:
            base_opts = BaseOptions(model_asset_path=MODEL_PATH)
            opts = vision.GestureRecognizerOptions(
                base_options=base_opts,
                running_mode=vision.RunningMode.IMAGE,
                num_hands=1,
                min_hand_detection_confidence=0.55,
                min_tracking_confidence=0.5
            )
            recognizer = vision.GestureRecognizer.create_from_options(opts)

            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                self._notify("Camera error: Could not access webcam.")
                self._running = False
                return

            self._notify("🖐 Gesture Sentinel: Online. Live HUD window opened.")

            window_name = "J.A.R.V.I.S. // GESTURE HUD"

            while self._running:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.04)
                    continue

                frame = cv2.flip(frame, 1) # Mirror for natural interaction
                h, w, _ = frame.shape
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

                result = recognizer.recognize(mp_image)

                gesture_name = "NONE"
                score = 0.0

                if result and result.gestures and len(result.gestures) > 0:
                    top = result.gestures[0][0]
                    gesture_name = top.category_name
                    score = top.score

                    if score >= 0.60:
                        self._last_gesture = gesture_name
                        self._last_score = score
                        now = time.time()

                        if (now - self._last_trigger_time) > self._cooldown_seconds:
                            if gesture_name == "Open_Palm":
                                self._handle_open_palm()
                                self._last_trigger_time = now
                            elif gesture_name == "Victory":
                                self._handle_victory()
                                self._last_trigger_time = now
                            elif gesture_name == "Thumb_Up":
                                self._handle_thumb_up()
                                self._last_trigger_time = now
                            elif gesture_name == "Thumb_Down":
                                self._handle_thumb_down()
                                self._last_trigger_time = now
                            elif gesture_name == "Pointing_Up":
                                self._handle_pointing_up()
                                self._last_trigger_time = now

                    # Air pinch continuous volume slider
                    if result.hand_landmarks and len(result.hand_landmarks) > 0:
                        self._process_pinch(result.hand_landmarks[0])
                else:
                    self._last_gesture = "NONE"
                    self._last_score = 0.0

                # Render Sci-Fi HUD Viewfinder Window
                if self._show_preview:
                    landmarks_list = result.hand_landmarks if (result and result.hand_landmarks) else None
                    self._draw_hud_overlay(frame, landmarks_list, gesture_name, score)

                    cv2.imshow(window_name, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key in [ord('q'), ord('Q'), 27]: # 'q' or ESC closes preview window
                        self._show_preview = False
                        cv2.destroyWindow(window_name)

                time.sleep(0.02)

        except Exception as e:
            print("[GESTURE CONTROLLER ERROR]:", e)
            self._notify(f"Gesture Controller Error: {e}")
        finally:
            self._running = False
            if cap:
                try:
                    cap.release()
                except Exception:
                    pass
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass


# Singleton instance
gesture_controller = GestureController()
