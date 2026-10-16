"""
Voice Biometric Identification & Voiceprint Security Protocol for J.A.R.V.I.S.
Extracts acoustic MFCCs and spectral timbre to enroll and verify authorized user voice.
Zero external cloud dependencies, 100% local mathematical verification.
"""

import os
import json
import time
import pyaudio
import numpy as np
from scipy import signal
from scipy.fftpack import dct
from typing import Tuple, Dict, Any, Optional

from voice_engine.sound_effects import play_fx
from voice_engine.voice import speak

SECURITY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "security")
os.makedirs(SECURITY_DIR, exist_ok=True)

VOICEPRINT_FILE = os.path.join(SECURITY_DIR, "user_voiceprint.npy")
CONFIG_FILE = os.path.join(SECURITY_DIR, "voiceprint_config.json")

DEFAULT_THRESHOLD = 0.72


def _load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"enabled": False, "threshold": DEFAULT_THRESHOLD, "enrolled_at": None}


def _save_config(cfg: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[VOICEPRINT CONFIG ERROR]: {e}")


def is_voice_security_enabled() -> bool:
    cfg = _load_config()
    return bool(cfg.get("enabled", False))


def has_enrolled_voiceprint() -> bool:
    return os.path.exists(VOICEPRINT_FILE)


def extract_features(audio: np.ndarray, sample_rate: int = 16000) -> Optional[np.ndarray]:
    """Compute acoustic timbre feature vector from audio buffer."""
    if len(audio) < sample_rate * 0.5:
        return None

    # STFT
    f, t_spec, Zxx = signal.stft(audio, fs=sample_rate, nperseg=512, noverlap=256)
    mag = np.abs(Zxx)

    # Voice activity detection (ignore silent/ambient frames)
    energy = np.sum(mag, axis=0)
    thresh = np.percentile(energy, 25)
    active_idx = energy > thresh
    if np.sum(active_idx) < 5:
        active_frames = mag
    else:
        active_frames = mag[:, active_idx]

    # Spectral centroid
    denom = np.sum(active_frames, axis=0) + 1e-9
    centroid = np.sum(f[:, None] * active_frames, axis=0) / denom
    mean_centroid = float(np.mean(centroid))

    # Log Mel Filterbank
    num_filters = 20
    mel_low = 1125 * np.log(1 + 100 / 700)
    mel_high = 1125 * np.log(1 + 7500 / 700)
    mel_points = np.linspace(mel_low, mel_high, num_filters + 2)
    hz_points = 700 * (np.exp(mel_points / 1125) - 1)
    bin_points = np.floor((512 + 1) * hz_points / sample_rate).astype(int)

    fbank = np.zeros((num_filters, 257))
    for m in range(1, num_filters + 1):
        f_m_minus = bin_points[m - 1]
        f_m = bin_points[m]
        f_m_plus = bin_points[m + 1]
        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - bin_points[m - 1]) / (bin_points[m] - bin_points[m - 1] + 1e-9)
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (bin_points[m + 1] - k) / (bin_points[m + 1] - bin_points[m] + 1e-9)

    filter_banks = np.dot(fbank, active_frames)
    filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)
    log_mel = 20 * np.log10(filter_banks)
    mfccs = dct(log_mel, type=2, axis=0, norm='ortho')[:13]
    mean_mfcc = np.mean(mfccs, axis=1)

    feature_vec = np.concatenate([mean_mfcc, [mean_centroid / 1000.0]])
    norm_vec = feature_vec / (np.linalg.norm(feature_vec) + 1e-9)
    return norm_vec


def record_sample(duration_sec: float = 3.5, sample_rate: int = 16000) -> Optional[np.ndarray]:
    """Capture raw microphone buffer via PyAudio."""
    p = pyaudio.PyAudio()
    stream = None
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=1024
        )

        frames = []
        total_frames = int(sample_rate / 1024 * duration_sec)
        for _ in range(total_frames):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)

        raw = b''.join(frames)
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        return audio
    except Exception as e:
        print(f"[VOICEPRINT RECORD ERROR]: {e}")
        return None
    finally:
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        p.terminate()


def enroll_user_voiceprint() -> str:
    """Enroll the authorized user voiceprint profile."""
    play_fx("wake")
    speak("Voice calibration initiated. Please speak continuously for three seconds after the chime.")
    time.sleep(1.2)
    play_fx("ack")

    audio = record_sample(duration_sec=3.5)
    if audio is None or len(audio) == 0:
        return "Voice calibration failed. Microphone input could not be acquired, Sir."

    feat = extract_features(audio)
    if feat is None:
        return "Audio signal was insufficient for feature extraction. Please speak closer to the microphone."

    np.save(VOICEPRINT_FILE, feat)
    cfg = _load_config()
    cfg["enrolled_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _save_config(cfg)

    play_fx("complete")
    return "Voiceprint enrollment complete, Sir. Your acoustic timbre vector has been securely registered to the core."


def verify_speaker() -> Tuple[bool, float, str]:
    """Verify incoming speaker against registered template."""
    if not has_enrolled_voiceprint():
        return True, 1.0, "No voiceprint enrolled. Security protocol is open."

    enrolled = np.load(VOICEPRINT_FILE)

    play_fx("ack")
    speak("Voice biometric check. Speak your identity phrase.")
    time.sleep(0.8)
    play_fx("wake")

    audio = record_sample(duration_sec=3.0)
    if audio is None:
        return False, 0.0, "Microphone capture failed."

    feat = extract_features(audio)
    if feat is None:
        return False, 0.0, "Insufficient speech energy detected."

    # Cosine similarity
    similarity = float(np.dot(enrolled, feat))
    cfg = _load_config()
    thresh = cfg.get("threshold", DEFAULT_THRESHOLD)

    if similarity >= thresh:
        play_fx("complete")
        return True, similarity, f"Voiceprint confirmed ({int(similarity * 100)}% match). Access granted, Sir."
    else:
        play_fx("alert")
        return False, similarity, f"Voiceprint mismatch ({int(similarity * 100)}% match). Access denied to unauthorized voice."


def enable_voice_security() -> str:
    if not has_enrolled_voiceprint():
        return "Cannot engage voice security without an enrolled voiceprint. Please say 'enroll voiceprint' first, Sir."
    cfg = _load_config()
    cfg["enabled"] = True
    _save_config(cfg)
    play_fx("complete")
    return "Voiceprint Security Protocol engaged, Sir. Sensitive directives are now guarded by your biometric voiceprint."


def disable_voice_security() -> str:
    cfg = _load_config()
    cfg["enabled"] = False
    _save_config(cfg)
    play_fx("standby")
    return "Voiceprint Security Protocol disengaged. Standard voice access restored, Sir."


def get_voiceprint_status() -> Dict[str, Any]:
    cfg = _load_config()
    enrolled = has_enrolled_voiceprint()
    return {
        "enrolled": enrolled,
        "enabled": cfg.get("enabled", False),
        "threshold": cfg.get("threshold", DEFAULT_THRESHOLD),
        "enrolled_at": cfg.get("enrolled_at")
    }
