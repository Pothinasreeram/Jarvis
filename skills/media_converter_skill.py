"""
Media Converter Voice Skill for J.A.R.V.I.S.
Handles voice requests to convert video to audio, convert/compress images,
and extract/summarize PDF documents completely offline.
"""

import re
from system_layer.media_converter_controller import (
    extract_audio_from_video,
    convert_image,
    extract_pdf_summary,
)

skill = {
    "name": "Media Converter Skill",
    "priority": 27,
}

TRIGGER_KEYWORDS = [
    "extract audio",
    "convert video to audio",
    "convert video to mp3",
    "extract mp3",
    "convert image",
    "convert this image",
    "compress image",
    "summarize pdf",
    "summarize this pdf",
    "read this pdf",
    "summarize latest pdf",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "audio" in cmd and ("video" in cmd or "extract" in cmd or "mp3" in cmd):
        return True
    if "convert" in cmd and any(fmt in cmd for fmt in ["png", "jpg", "jpeg", "webp", "image", "mp3"]):
        return True
    if "pdf" in cmd and any(action in cmd for action in ["summarize", "read", "explain"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. PDF Summarization / Extraction
    if "pdf" in cmd:
        return extract_pdf_summary()

    # 2. Video to Audio Extraction
    if "audio" in cmd or "video to" in cmd or "mp3" in cmd:
        target_fmt = "mp3"
        if "wav" in cmd:
            target_fmt = "wav"
        return extract_audio_from_video(output_format=target_fmt)

    # 3. Image Conversion / Compression
    if "image" in cmd or "photo" in cmd or "picture" in cmd or any(fmt in cmd for fmt in ["png", "jpg", "jpeg", "webp"]):
        target_fmt = "png"
        if "jpg" in cmd or "jpeg" in cmd:
            target_fmt = "jpg"
        elif "webp" in cmd:
            target_fmt = "webp"
        return convert_image(target_format=target_fmt)

    return "Media conversion command received, Sir."
