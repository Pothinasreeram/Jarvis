"""
Local Zero-Latency Wake-Word Detection for J.A.R.V.I.S.
Powered by OpenWakeWord (ONNX Runtime) with Pronunciation Tolerance & Persistent Audio Streaming.
"""

import os
import sys
import time
import threading
import numpy as np
import pyaudio

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

WAKE_WORD = "jarvis"

# Pronunciation-tolerant thresholds
# 0.22 captures accented or soft "Hey Jarvis" and "Jarvis" reliably
PRIMARY_THRESHOLD = 0.22
ACCUMULATOR_THRESHOLD = 0.16

# Manual trigger event (from HUD Arc Reactor click or global hotkey)
_manual_trigger_event = threading.Event()
_privacy_muted = False

def set_privacy_mute(muted: bool):
    """Enable or disable hardware/software privacy mute."""
    global _privacy_muted
    _privacy_muted = bool(muted)
    if _privacy_muted:
        release_wake_word_stream()
        print("[PRIVACY GUARD] Microphone is physically disengaged. Wake engine paused.")
    else:
        print("[PRIVACY GUARD] Microphone restored. Wake engine operational.")

def is_privacy_muted() -> bool:
    """Return whether privacy mute is currently engaged."""
    return _privacy_muted

def trigger_wake_word():
    """Manually trigger wake-word event from HUD Arc Reactor or hotkey."""
    global _privacy_muted
    if _privacy_muted:
        set_privacy_mute(False)
    _manual_trigger_event.set()

# Initialize OpenWakeWord model
_oww_model = None
_oww_model_name = "hey_jarvis_v0.1.onnx"

def get_wake_model():
    global _oww_model
    if _oww_model is None:
        try:
            from openwakeword.model import Model
            _oww_model = Model(
                wakeword_models=[_oww_model_name],
                inference_framework="onnx"
            )
            print("[WAKE ENGINE] Local ONNX Wake-Word Model loaded successfully!")
        except Exception as e:
            print(f"[WAKE ENGINE ERROR]: {e}")
            _oww_model = False
    return _oww_model


# Persistent audio stream to eliminate 5-second audio drop gaps
_pyaudio_instance = None
_audio_stream = None
_stream_lock = threading.Lock()

CHUNK = 1280
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


def _get_persistent_stream():
    """Get or initialize persistent PyAudio stream."""
    global _pyaudio_instance, _audio_stream
    with _stream_lock:
        try:
            if _pyaudio_instance is None:
                _pyaudio_instance = pyaudio.PyAudio()

            if _audio_stream is None:
                _audio_stream = _pyaudio_instance.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK
                )
            elif _audio_stream.is_stopped():
                _audio_stream.start_stream()

            return _audio_stream
        except Exception as e:
            print(f"[WAKE STREAM INIT ERROR]: {e}")
            return None


def release_wake_word_stream():
    """Completely release audio device so speech recognition has exclusive access."""
    global _audio_stream
    with _stream_lock:
        if _audio_stream:
            try:
                _audio_stream.stop_stream()
                _audio_stream.close()
            except Exception:
                pass
            _audio_stream = None


def close_wake_word_stream():
    """Cleanly close persistent PyAudio stream on shutdown."""
    global _pyaudio_instance, _audio_stream
    release_wake_word_stream()
    with _stream_lock:
        if _pyaudio_instance:
            try:
                _pyaudio_instance.terminate()
            except Exception:
                pass
            _pyaudio_instance = None


def listen_for_wake_word(timeout=5.0):
    """
    Fast local wake-word listener with persistent streaming,
    pronunciation tolerance, and manual trigger support.
    """
    # Check privacy mute mode
    if _privacy_muted:
        if _manual_trigger_event.is_set():
            _manual_trigger_event.clear()
            set_privacy_mute(False)
            print(">> [MANUAL WAKE] Restoring microphone via Arc Reactor / Hotkey!")
            release_wake_word_stream()
            return True
        time.sleep(0.2)
        return False

    # 1. Check manual trigger (Arc Reactor click or Hotkey)
    if _manual_trigger_event.is_set():
        _manual_trigger_event.clear()
        print(">> [MANUAL WAKE] Triggered via Arc Reactor / Hotkey!")
        release_wake_word_stream()
        return True

    model = get_wake_model()
    if not model:
        return _fallback_listen_for_wake_word(timeout)

    stream = _get_persistent_stream()
    if not stream:
        return _fallback_listen_for_wake_word(timeout)

    start_time = time.time()
    consecutive_hits = 0

    try:
        while True:
            # Check manual trigger within loop
            if _manual_trigger_event.is_set():
                _manual_trigger_event.clear()
                print(">> [MANUAL WAKE] Triggered via Arc Reactor / Hotkey!")
                release_wake_word_stream()
                return True

            if timeout and (time.time() - start_time) > timeout:
                return False

            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
            except Exception:
                time.sleep(0.01)
                continue

            audio_frame = np.frombuffer(data, dtype=np.int16)
            prediction = model.predict(audio_frame)

            for mdl, score in prediction.items():
                # Single-frame primary trigger
                if score >= PRIMARY_THRESHOLD:
                    print(f">> [WAKE DETECTED] Wake-word '{WAKE_WORD}' triggered! (Confidence: {score:.2f})")
                    model.reset()
                    release_wake_word_stream()
                    return True

                # Accumulator trigger for softer or regional pronunciations
                elif score >= ACCUMULATOR_THRESHOLD:
                    consecutive_hits += 1
                    if consecutive_hits >= 2:
                        print(f">> [WAKE DETECTED] Wake-word '{WAKE_WORD}' triggered via accumulation! (Confidence: {score:.2f})")
                        model.reset()
                        consecutive_hits = 0
                        release_wake_word_stream()
                        return True
                else:
                    consecutive_hits = 0

    except Exception as e:
        print("[WAKE LISTENER ERROR]:", e)
        return False


def _fallback_listen_for_wake_word(timeout=3.0):
    """Fallback using standard speech recognizer if ONNX model is unavailable."""
    from voice_engine.voice import listen
    command = listen(timeout=int(timeout), phrase_time_limit=4)
    if command and any(w in command.lower() for w in ["jarvis", "service", "travis", "harvis"]):
        print(">> [FALLBACK WAKE] Wake word detected!")
        return True
    return False


if __name__ == "__main__":
    print("Testing pronunciation-tolerant wake word engine. Say 'Jarvis' or 'Hey Jarvis'...")
    detected = listen_for_wake_word(timeout=10)
    print("Result:", detected)