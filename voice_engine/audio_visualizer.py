"""
Real-Time Audio Visualizer Bus for J.A.R.V.I.S. HUD
Calculates instantaneous RMS amplitude and 36 logarithmic FFT frequency bands
from live microphone input and speech output without device contention.
"""

import time
import math
import threading
import numpy as np

NUM_BANDS = 36
CHUNK = 1280
RATE = 16000

# Precompute FFT frequency bins and logarithmic edges (60 Hz to 8500 Hz)
_freq_bins = np.fft.rfftfreq(CHUNK, 1.0 / RATE)
_log_edges = np.logspace(np.log10(60), np.log10(8500), num=NUM_BANDS + 1)
_band_masks = [
    (_freq_bins >= _log_edges[i]) & (_freq_bins < _log_edges[i + 1])
    for i in range(NUM_BANDS)
]
_hanning_window = np.hanning(CHUNK)

_lock = threading.Lock()
_current_rms = 0.0
_current_bands = np.zeros(NUM_BANDS, dtype=np.float32)
_last_update = 0.0
_is_speaking = False


def set_speaking_state(speaking: bool):
    """Set whether Jarvis TTS speech output is actively playing."""
    global _is_speaking
    with _lock:
        _is_speaking = bool(speaking)


def push_audio_chunk(data):
    """
    Push raw PCM audio bytes or numpy array from mic stream into visualizer bus.
    Calculates RMS amplitude and logarithmic FFT frequency spectrum.
    """
    global _current_rms, _current_bands, _last_update
    if data is None:
        return

    try:
        if isinstance(data, (bytes, bytearray)):
            audio = np.frombuffer(data, dtype=np.int16)
        elif isinstance(data, np.ndarray):
            audio = data
        else:
            return

        if len(audio) == 0:
            return

        # Calculate RMS energy level
        rms = float(np.abs(audio).mean())

        # If audio chunk size does not match CHUNK, pad or slice
        if len(audio) < CHUNK:
            padded = np.zeros(CHUNK, dtype=np.float32)
            padded[:len(audio)] = audio
            audio = padded
        elif len(audio) > CHUNK:
            audio = audio[:CHUNK]

        # Apply Hanning window & compute FFT magnitude
        windowed = audio.astype(np.float32) * _hanning_window
        fft_mag = np.abs(np.fft.rfft(windowed))

        # Calculate logarithmic frequency bands
        bands = np.zeros(NUM_BANDS, dtype=np.float32)
        for i in range(NUM_BANDS):
            mask = _band_masks[i]
            if np.any(mask):
                bands[i] = float(np.mean(fft_mag[mask]))

        # Dynamic logarithmic scale (clip to 0 - 22 px height)
        scaled = np.log10(1.0 + bands / 45.0)
        spectrum = np.clip(scaled * 8.0, 0.0, 22.0)

        with _lock:
            _current_rms = rms
            _current_bands = spectrum
            _last_update = time.time()

    except Exception:
        pass


def get_visualizer_levels():
    """
    Get (rms_level, fft_bands_array, is_speaking).
    If no live audio frame has arrived within 0.3s, provides ambient breathing values.
    """
    with _lock:
        rms = _current_rms
        bands = _current_bands.copy()
        last_t = _last_update
        spk = _is_speaking

    now = time.time()
    # If live input is stale (> 350ms) and not speaking, decay to gentle ambient oscillation
    if (now - last_t) > 0.35 and not spk:
        rms = max(0.0, rms * 0.7)
        # Generate organic ambient breathing wave
        ambient = np.zeros(NUM_BANDS, dtype=np.float32)
        for i in range(NUM_BANDS):
            ambient[i] = max(2.0, 2.5 + 3.0 * math.sin(now * 2.8 + i * 0.35))
        return rms, ambient, spk

    return rms, bands, spk
