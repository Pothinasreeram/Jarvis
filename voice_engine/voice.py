import pyttsx3
import speech_recognition as sr
import threading
import time
import asyncio
import io
import os
import pygame
import edge_tts

import edge_tts
from .piper_engine import is_piper_available, synthesize_piper_audio

# Iconic British JARVIS Neural Voice
JARVIS_VOICE = "en-GB-RyanNeural"
VOICE_MODE = "auto"  # 'auto', 'offline', 'online'
pygame_initialized = False

def set_voice_mode(mode: str) -> str:
    """Set TTS engine mode: 'auto', 'offline' (Piper), or 'online' (Edge-TTS)."""
    global VOICE_MODE
    mode_clean = mode.lower().strip()
    if mode_clean in ["offline", "piper", "local"]:
        VOICE_MODE = "offline"
        return "Offline Paul Bettany neural voice activated."
    elif mode_clean in ["online", "edge"]:
        VOICE_MODE = "online"
        return "Online British neural voice activated."
    else:
        VOICE_MODE = "auto"
        return "Automatic voice routing activated."

def get_voice_mode() -> str:
    return VOICE_MODE

def init_audio_mixer():
    global pygame_initialized
    if not pygame_initialized:
        try:
            pygame.mixer.init()
            pygame_initialized = True
        except Exception as e:
            print("[AUDIO MIXER INIT ERROR]:", e)

async def _synthesize_edge_audio(text):
    communicate = edge_tts.Communicate(text, JARVIS_VOICE, rate="+5%", pitch="+0Hz")
    audio_buffer = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer += chunk["data"]
    return audio_buffer

_interrupted = False

def is_interrupted():
    return _interrupted

def reset_interruption():
    global _interrupted
    _interrupted = False

def stop_speaking():
    """Immediately halts audio playback and sets interrupted state."""
    global _interrupted
    _interrupted = True
    print("[INTERRUPT] stop_speaking() triggered! Halting playback.")
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception as e:
        print("[STOP ERROR]:", e)

BARGE_IN_THRESHOLD = 0.75

def _barge_in_listener():
    """
    Background listener active while JARVIS is speaking.
    Uses high threshold (0.75) and grace delay to prevent speaker self-echo.
    """
    global _interrupted
    # Grace period: allow initial audio playback to stabilize
    time.sleep(0.6)
    if not is_speaking or _interrupted:
        return

    stream = None
    p = None
    try:
        from wake_word import get_wake_model
        import pyaudio
        import numpy as np

        model = get_wake_model()
        if not model:
            return

        CHUNK = 1280
        RATE = 16000
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        while is_speaking and not _interrupted:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_frame = np.frombuffer(data, dtype=np.int16)
            preds = model.predict(audio_frame)
            for mdl, score in preds.items():
                if score >= BARGE_IN_THRESHOLD:
                    print(f"[VOICE BARGE-IN] Wake word detected during speech! (Confidence: {score:.2f})")
                    model.reset()
                    stop_speaking()
                    return

    except Exception:
        pass
    finally:
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        if p:
            try:
                p.terminate()
            except Exception:
                pass

def _play_audio_bytes(audio_bytes):
    global _interrupted
    init_audio_mixer()
    sound_stream = io.BytesIO(audio_bytes)
    pygame.mixer.music.load(sound_stream)
    pygame.mixer.music.play()

    barge_thread = threading.Thread(target=_barge_in_listener, daemon=True)
    barge_thread.start()

    while pygame.mixer.music.get_busy():
        if _interrupted:
            pygame.mixer.music.stop()
            break
        time.sleep(0.03)

_sapi_engine = None

def _get_sapi_engine():
    global _sapi_engine
    if _sapi_engine is None:
        try:
            _sapi_engine = pyttsx3.init(driverName="sapi5")
            _sapi_engine.setProperty("rate", 175)
            voices = _sapi_engine.getProperty("voices")
            if voices:
                _sapi_engine.setProperty("voice", voices[0].id)
        except Exception as e:
            print("[SAPI5 INIT ERROR]:", e)
    return _sapi_engine

def _fallback_sapi_speak(speech_text):
    try:
        engine = _get_sapi_engine()
        if engine:
            engine.say(speech_text)
            engine.runAndWait()
    except Exception as e:
        print("[SAPI5 TTS ERROR]", e)

is_speaking = False
is_processing = False

speech_lock = threading.Lock()
voice_lock = threading.Lock()

def wait_until_ready():
    while is_speaking:
        time.sleep(0.1)
def make_speech_friendly(text):
    if not text:
        return ""

    text = str(text)

    text = text.replace("_", " ")
    text = text.replace("-", " ")

    return " ".join(text.split())

def prepare_speech_text(text):
    if not text:
        return text

    speech_text = str(text)

    # Python identifiers
    speech_text = speech_text.replace("_", " ")

    # Common programming symbols
    speech_text = speech_text.replace("()", "")
    speech_text = speech_text.replace(".py", "")

    return speech_text

def speak(text):
    global is_speaking, _interrupted

    if not text or not str(text).strip():
        return

    # ALWAYS reset interrupted state on each new speech request
    _interrupted = False

    speech_text = prepare_speech_text(text)
    print("Speaking:", text)

    with speech_lock:
        is_speaking = True
        audio_played = False
        try:
            # 1. Direct Offline Mode
            if VOICE_MODE == "offline":
                if is_piper_available():
                    print("[TTS] Synthesizing Offline Paul Bettany Neural JARVIS voice...")
                    audio_bytes = synthesize_piper_audio(speech_text)
                    if audio_bytes and not _interrupted:
                        print("[TTS] Playing local neural speech...")
                        _play_audio_bytes(audio_bytes)
                        audio_played = True

            # 2. Online Mode or Auto Routing
            if not audio_played and VOICE_MODE in ["auto", "online"]:
                try:
                    print("[TTS] Synthesizing British Neural JARVIS voice...")
                    audio_bytes = asyncio.run(_synthesize_edge_audio(speech_text))
                    if _interrupted:
                        print("[TTS] Playback skipped due to interruption.")
                        return

                    if audio_bytes:
                        print("[TTS] Playing neural speech...")
                        _play_audio_bytes(audio_bytes)
                        audio_played = True
                except Exception as net_err:
                    print(f"[EDGE-TTS UNAVAILABLE] ({net_err}) -> Routing to offline neural engine...")

            # 3. Fallback to Piper Neural if online failed
            if not audio_played and not _interrupted and is_piper_available():
                try:
                    print("[TTS] Synthesizing Offline Paul Bettany Neural JARVIS voice (Fallback)...")
                    audio_bytes = synthesize_piper_audio(speech_text)
                    if audio_bytes and not _interrupted:
                        print("[TTS] Playing local neural speech...")
                        _play_audio_bytes(audio_bytes)
                        audio_played = True
                except Exception as piper_err:
                    print(f"[PIPER FALLBACK ERROR]: {piper_err}")

            # 4. Final SAPI5 emergency fallback
            if not audio_played and not _interrupted:
                print("[TTS] Falling back to local Windows SAPI5 voice...")
                _fallback_sapi_speak(speech_text)

        except Exception as e:
            if not _interrupted:
                print(f"[TTS GENERAL ERROR] ({e}) -> Using local SAPI5")
                _fallback_sapi_speak(speech_text)
        finally:
            is_speaking = False
            print("[TTS] Finished speaking. Microphone can resume.")




def speaking_status():
    return is_speaking


recognizer = sr.Recognizer()
microphone = sr.Microphone()

def wait_until_ready():

    while is_speaking:
        time.sleep(0.1)

def normalize_speech_command(command):
    if not command:
        return ""

    command = command.lower().strip()

    # --------------------------------------------------
    # SYMBOL PHRASES
    # --------------------------------------------------

    replacements = {
        " under score ": "_",
        " dot ": ".",
        " period ": ".",
        " slash ": "/",
        " backslash ": "\\",
        " hyphen ": "-",
        " dash ": "-",
        " colon ": ":",
        " semicolon ": ";",
        " open parenthesis ": "(",
        " close parenthesis ": ")",
        " open bracket ": "[",
        " close bracket ": "]",
        " open brace ": "{",
        " close brace ": "}",
    }

    padded = f" {command} "

    for spoken, symbol in replacements.items():
        padded = padded.replace(spoken, symbol)

    command = " ".join(padded.split()).strip()


    # --------------------------------------------------
    # UNDERSCORE INTELLIGENCE
    # --------------------------------------------------

    words = command.split()

    if "underscore" in words:

        # Keep "underscore" as an English word when it is
        # clearly being discussed as a concept.
        conceptual_patterns = [
            ["what", "is", "an", "underscore"],
            ["what", "is", "underscore"],
            ["define", "underscore"],
            ["meaning", "of", "underscore"],
            ["explain", "underscore"],
        ]

        if words not in conceptual_patterns:

            # Convert standalone "underscore" to "_"
            # when it appears between identifier words.
            result = []

            for i, word in enumerate(words):

                if word == "underscore":

                    previous_word = words[i - 1] if i > 0 else ""
                    next_word = words[i + 1] if i + 1 < len(words) else ""

                    if previous_word and next_word:
                        result.append("_")
                    else:
                        result.append(word)

                else:
                    result.append(word)

            command = " ".join(result)

    # --------------------------------------------------
    # CLEAN SPACING AROUND SYMBOLS
    # --------------------------------------------------

    command = command.replace(" _ ", "_")
    command = command.replace(" . ", ".")
    command = command.replace(" / ", "/")
    command = command.replace(" \\ ", "\\")
    command = command.replace(" - ", "-")
    command = command.replace(" : ", ":")
    command = command.replace(" ; ", ";")
    command = command.replace("( ", "(")
    command = command.replace(" )", ")")
    command = command.replace("[ ", "[")
    command = command.replace(" ]", "]")
    command = command.replace("{ ", "{")
    command = command.replace(" }", "}")

    return " ".join(command.split()).strip()

def listen( timeout=5, phrase_time_limit=8):

    wait_until_ready()
    with microphone as source:
        print("Listening...")

        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )

        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return ""

    try:
        command = recognizer.recognize_google(audio)
        print("You said:", command)
        command = normalize_speech_command(command)
        print("Normalized command:", command)
        return command

    except sr.UnknownValueError:
        print("Could not understand.")
        return ""

    except sr.RequestError as e:
        print("Speech Recognition Error:", e)
        return ""

    except Exception as e:
        print("Unexpected Error:", e)
        return ""