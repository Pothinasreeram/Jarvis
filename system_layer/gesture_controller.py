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


class GestureController:
    def __init__(self):
        self._running = False
        self._thread = None
        self._last_gesture = "NONE"
        self._last_trigger_time = 0.0
        self._cooldown_seconds = 1.8
        self._pinch_active = False
        self._last_pinch_y = None
        self._notif_cb = None
        self._status_cb = None

    def is_active(self) -> bool:
        return self._running

    def get_last_gesture(self) -> str:
        return self._last_gesture

    def _notify(self, text: str):
        if self._notif_cb:
            try:
                self._notif_cb(text)
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
            self._notify(f"Gesture Volume: {pct}%")
        except Exception:
            pass

    def _handle_open_palm(self):
        """Open palm: Immediately halts speech."""
        from voice_engine.voice import speaking_status, stop_speaking
        if speaking_status():
            stop_speaking()
            self._notify("🖐 Open Palm: Voice output interrupted.")
        else:
            self._notify("🖐 Open Palm detected (Standby).")

    def _handle_victory(self):
        """Victory (peace sign): Launches executive morning briefing."""
        def worker():
            try:
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
                self._notify(f"👎 Thumbs Down: Pausing media ({res})")
            except Exception as e:
                self._notify(f"Media error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _handle_pointing_up(self):
        """Pointing up: Quick volume boost."""
        self._change_volume(+5)

    def _process_pinch(self, landmarks):
        """Detect thumb-to-index pinch distance and vertical movement for air volume control."""
        # Landmark 4: Thumb Tip, Landmark 8: Index Tip
        thumb = landmarks[4]
        index = landmarks[8]

        dx = thumb.x - index.x
        dy = thumb.y - index.y
        dist = math.sqrt(dx * dx + dy * dy)

        # Pinch threshold
        if dist < 0.055:
            current_y = (thumb.y + index.y) / 2.0
            if self._pinch_active and self._last_pinch_y is not None:
                diff_y = self._last_pinch_y - current_y # Moving UP is negative y in screen space
                if abs(diff_y) > 0.03:
                    delta = int(diff_y * 100)
                    self._change_volume(delta)
                    self._last_pinch_y = current_y
            else:
                self._pinch_active = True
                self._last_pinch_y = current_y
        else:
            self._pinch_active = False
            self._last_pinch_y = None

    def start(self, notif_callback=None, status_callback=None) -> str:
        """Start the gesture recognition thread."""
        if not HAS_MEDIAPIPE:
            return "MediaPipe library not installed."
        if not os.path.exists(MODEL_PATH):
            return "Gesture recognizer model file missing."
        if self._running:
            return "Gesture recognition is already active."

        self._notif_cb = notif_callback
        self._status_cb = status_callback
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
        return "Hand gesture control deactivated."

    def _run_loop(self):
        """Main webcam capture and neural gesture classification loop."""
        cap = None
        try:
            # Initialize MediaPipe Gesture Recognizer
            base_opts = BaseOptions(model_asset_path=MODEL_PATH)
            opts = vision.GestureRecognizerOptions(
                base_options=base_opts,
                running_mode=vision.RunningMode.IMAGE,
                num_hands=1,
                min_hand_detection_confidence=0.6,
                min_tracking_confidence=0.5
            )
            recognizer = vision.GestureRecognizer.create_from_options(opts)

            # Open primary webcam
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                self._notify("Camera error: Could not access webcam.")
                self._running = False
                return

            self._notify("🖐 Gesture Sentinel: Online & calibrating...")

            frame_count = 0
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.05)
                    continue

                frame_count += 1
                # Process every 2nd frame to minimize CPU usage
                if frame_count % 2 != 0:
                    time.sleep(0.02)
                    continue

                # Mirror frame & resize for fast detection
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

                # Neural inference
                result = recognizer.recognize(mp_image)

                now = time.time()

                if result and result.gestures and len(result.gestures) > 0:
                    top_gesture = result.gestures[0][0]
                    gesture_name = top_gesture.category_name
                    score = top_gesture.score

                    if score >= 0.65:
                        self._last_gesture = gesture_name

                        # Check discrete gesture triggers with cooldown
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

                    # Continuous pinch volume adjustment
                    if result.hand_landmarks and len(result.hand_landmarks) > 0:
                        self._process_pinch(result.hand_landmarks[0])

                time.sleep(0.03)

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


# Singleton instance
gesture_controller = GestureController()
