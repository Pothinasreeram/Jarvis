"""
Stark Industries Futuristic Sound FX Engine for J.A.R.V.I.S.
Synthesizes and plays high-fidelity sci-fi chimes, wake cues, and UI audio
using pure mathematical FM synthesis and pygame.mixer.
Zero external assets required.
"""

import os
import wave
import struct
import math
import numpy as np
import threading

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sounds")
os.makedirs(SOUNDS_DIR, exist_ok=True)

SAMPLE_RATE = 44100

def _generate_wav(filename: str, samples: np.ndarray):
    """Write normalized float samples (-1.0 to 1.0) into 16-bit PCM WAV."""
    path = os.path.join(SOUNDS_DIR, filename)
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)

    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_samples.tobytes())
    return path


def generate_all_sound_effects():
    """Synthesize high-tech Stark UI sound assets if they do not exist."""
    wake_path = os.path.join(SOUNDS_DIR, "wake.wav")
    ack_path = os.path.join(SOUNDS_DIR, "ack.wav")
    complete_path = os.path.join(SOUNDS_DIR, "complete.wav")
    standby_path = os.path.join(SOUNDS_DIR, "standby.wav")
    alert_path = os.path.join(SOUNDS_DIR, "alert.wav")

    # 1. WAKE REPLULSOR / ARC REACTOR CHIME (Harmonic bell + upward sweep)
    if not os.path.exists(wake_path):
        dur = 0.45
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        # Rising resonant carrier + bell harmonics
        carrier_freq = 660 + 540 * (t / dur) ** 2
        carrier = np.sin(2 * np.pi * carrier_freq * t)
        h1 = 0.45 * np.sin(2 * np.pi * carrier_freq * 1.5 * t)
        h2 = 0.25 * np.sin(2 * np.pi * carrier_freq * 2.0 * t)
        # Soft shimmer
        shimmer = 0.15 * np.sin(2 * np.pi * 1760 * t) * np.exp(-t * 6.0)
        envelope = np.exp(-t * 5.0) * (1.0 - np.exp(-t * 80.0))
        samples = (carrier + h1 + h2 + shimmer) * envelope
        _generate_wav("wake.wav", samples)

    # 2. ACKNOWLEDGMENT CHIRP (Dual high-frequency micro pulse)
    if not os.path.exists(ack_path):
        dur = 0.10
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        f1 = 1350
        f2 = 2020
        carrier = 0.6 * np.sin(2 * np.pi * f1 * t) + 0.4 * np.sin(2 * np.pi * f2 * t)
        envelope = np.exp(-t * 35.0)
        samples = carrier * envelope
        _generate_wav("ack.wav", samples)

    # 3. COMPLETE / SUCCESS CHIME (Stark Two-Tone Ascending Bell: 1046Hz -> 1318Hz)
    if not os.path.exists(complete_path):
        dur = 0.40
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        t_half = dur / 2.0
        # Note 1: 1046 Hz (C6)
        n1 = np.where(t < t_half, np.sin(2 * np.pi * 1046.5 * t) * np.exp(-t * 12.0), 0)
        # Note 2: 1318 Hz (E6)
        t2 = t - t_half
        n2 = np.where(t >= t_half, np.sin(2 * np.pi * 1318.5 * t2) * np.exp(-t2 * 10.0), 0)
        harmonic = 0.2 * np.sin(2 * np.pi * 2637.0 * t) * np.exp(-t * 8.0)
        samples = (n1 + n2 + harmonic) * 0.8
        _generate_wav("complete.wav", samples)

    # 4. STANDBY / SLEEP SWEEP (Gentle descending resonant sweep: 520Hz -> 220Hz)
    if not os.path.exists(standby_path):
        dur = 0.50
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        freq = 520 - 300 * (t / dur) ** 0.8
        carrier = np.sin(2 * np.pi * freq * t)
        sub = 0.3 * np.sin(2 * np.pi * (freq * 0.5) * t)
        envelope = np.exp(-t * 4.5) * (1.0 - np.exp(-t * 40.0))
        samples = (carrier + sub) * envelope * 0.75
        _generate_wav("standby.wav", samples)

    # 5. ALERT / CAUTION TONE (Pulsed warning tone)
    if not os.path.exists(alert_path):
        dur = 0.35
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        mod = np.sin(2 * np.pi * 24 * t)
        carrier = np.sin(2 * np.pi * 580 * t + mod * 2.0)
        envelope = np.exp(-t * 6.0)
        samples = carrier * envelope * 0.85
        _generate_wav("alert.wav", samples)


# Cache of loaded pygame.mixer.Sound objects
_cached_sounds = {}
_sound_lock = threading.Lock()
_sound_enabled = True

def init_sound_fx():
    """Ensure sound assets exist and initialize mixer."""
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        generate_all_sound_effects()
    except Exception as e:
        print("[SOUND FX INIT ERROR]:", e)


def play_fx(fx_name: str, volume: float = 0.65):
    """
    Play a synthesized sci-fi sound effect asynchronously on a separate audio channel.
    Supported fx: 'wake', 'ack', 'complete', 'standby', 'alert'
    """
    if not _sound_enabled:
        return

    def _async_play():
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            wav_path = os.path.join(SOUNDS_DIR, f"{fx_name}.wav")
            if not os.path.exists(wav_path):
                generate_all_sound_effects()

            with _sound_lock:
                if fx_name not in _cached_sounds:
                    if os.path.exists(wav_path):
                        _cached_sounds[fx_name] = pygame.mixer.Sound(wav_path)

                sound = _cached_sounds.get(fx_name)

            if sound:
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
        except Exception as e:
            # Non-blocking audio play
            pass

    threading.Thread(target=_async_play, daemon=True).start()


def set_sound_fx_enabled(enabled: bool):
    global _sound_enabled
    _sound_enabled = bool(enabled)
