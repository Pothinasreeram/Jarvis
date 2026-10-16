"""
Offline Neural J.A.R.V.I.S. Voice Engine (Piper Neural TTS)
Powered by local ONNX Piper Voice with British English inflection,
zero internet dependency, and sub-100ms local synthesis.
"""

import os
import io
import wave
import threading
from typing import Optional

_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
_MODEL_PATH = os.path.join(_MODELS_DIR, "en_GB-alan-medium.onnx")
_CONFIG_PATH = os.path.join(_MODELS_DIR, "en_GB-alan-medium.onnx.json")

_piper_voice = None
_piper_lock = threading.Lock()
_piper_initialized = False


def is_piper_available() -> bool:
    """Check if Piper TTS package and model are present."""
    if not (os.path.exists(_MODEL_PATH) and os.path.exists(_CONFIG_PATH)):
        return False
    try:
        import piper
        return True
    except ImportError:
        return False


def get_piper_voice():
    """Lazy-load and cache the PiperVoice ONNX session."""
    global _piper_voice, _piper_initialized
    with _piper_lock:
        if _piper_voice is None:
            try:
                from piper import PiperVoice
                if os.path.exists(_MODEL_PATH):
                    print("[PIPER TTS] Loading local Paul Bettany / British Neural ONNX model...")
                    _piper_voice = PiperVoice.load(_MODEL_PATH, _CONFIG_PATH)
                    _piper_initialized = True
                    print("[PIPER TTS] Local Neural Voice Model loaded and ready!")
            except Exception as e:
                print(f"[PIPER TTS LOAD ERROR]: {e}")
                _piper_voice = False
    return _piper_voice if _piper_voice else None


def synthesize_piper_audio(text: str, length_scale: float = 0.95, volume: float = 1.0) -> Optional[bytes]:
    """
    Synthesize text into PCM WAV bytes using local ONNX Piper.
    - length_scale: 0.95 gives a crisp, measured British cadence.
    - volume: output gain multiplier.
    Returns: WAV bytes or None if unavailable.
    """
    voice = get_piper_voice()
    if not voice:
        return None

    try:
        from piper.config import SynthesisConfig

        syn_config = SynthesisConfig(
            length_scale=length_scale,
            volume=volume,
            normalize_audio=True
        )

        buf = io.BytesIO()
        wf = None
        first = True

        for chunk in voice.synthesize(text, syn_config=syn_config):
            if first:
                wf = wave.open(buf, 'wb')
                wf.setnchannels(chunk.sample_channels)
                wf.setsampwidth(chunk.sample_width)
                wf.setframerate(chunk.sample_rate)
                first = False
            wf.writeframes(chunk.audio_int16_bytes)

        if wf:
            wf.close()

        wav_bytes = buf.getvalue()
        return wav_bytes if len(wav_bytes) > 44 else None

    except Exception as e:
        print(f"[PIPER SYNTHESIS ERROR]: {e}")
        return None
