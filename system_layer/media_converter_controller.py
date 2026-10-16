"""
Local Media & File Converter Swiss Army Knife for J.A.R.V.I.S.
100% offline file transformations powered by local FFmpeg, Pillow, and pypdf:
- Extract audio from video (.mp4/.mkv -> .mp3)
- Convert & compress images (.png/.jpg/.webp)
- Extract text and merge PDF documents
"""

import os
import subprocess
from typing import Optional, List
from PIL import Image
import imageio_ffmpeg

from voice_engine.sound_effects import play_fx

USER_DIR = os.environ.get("USERPROFILE", "")
DOWNLOADS_DIR = os.path.join(USER_DIR, "Downloads")
DESKTOP_DIR = os.path.join(USER_DIR, "OneDrive", "Desktop") if os.path.exists(os.path.join(USER_DIR, "OneDrive", "Desktop")) else os.path.join(USER_DIR, "Desktop")

VIDEO_EXTENSIONS = [".mp4", ".mkv", ".mov", ".avi", ".flv", ".webm"]
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]


def _get_latest_file(extensions: List[str], search_folders: Optional[List[str]] = None) -> Optional[str]:
    """Find the most recently modified file matching given extensions."""
    if search_folders is None:
        search_folders = [DOWNLOADS_DIR, DESKTOP_DIR]

    candidates = []
    for folder in search_folders:
        if not os.path.exists(folder):
            continue
        try:
            for entry in os.scandir(folder):
                if entry.is_file():
                    _, ext = os.path.splitext(entry.name.lower())
                    if ext in extensions:
                        candidates.append((entry.path, entry.stat().st_mtime))
        except Exception:
            continue

    if not candidates:
        return None
    # Sort by mtime descending
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def extract_audio_from_video(video_path: Optional[str] = None, output_format: str = "mp3") -> str:
    """
    Extract high-quality audio stream from a video file into Downloads/ as MP3 or WAV.
    """
    if not video_path:
        video_path = _get_latest_file(VIDEO_EXTENSIONS)

    if not video_path or not os.path.exists(video_path):
        return "I could not locate a video file in your Downloads or Desktop to extract audio from, Sir."

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    base_name, _ = os.path.splitext(os.path.basename(video_path))
    output_filename = f"{base_name}_audio.{output_format}"
    output_path = os.path.join(DOWNLOADS_DIR, output_filename)

    cmd = [
        ffmpeg_exe,
        "-y",               # Overwrite if exists
        "-i", video_path,
        "-vn",              # Disable video recording
        "-acodec", "libmp3lame" if output_format == "mp3" else "pcm_s16le",
        "-q:a", "2",
        output_path
    ]

    try:
        print(f"[MEDIA CONVERTER] Extracting audio: {video_path} -> {output_path}")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        play_fx("complete")
        return f"Audio extracted successfully, Sir. Saved as {output_filename} in your Downloads folder."
    except Exception as e:
        print(f"[MEDIA CONVERT ERROR]: {e}")
        return f"Failed to extract audio from video, Sir: {e}"


def convert_image(image_path: Optional[str] = None, target_format: str = "png", quality: int = 85) -> str:
    """
    Convert or compress an image into target format (.png, .jpg, .webp).
    """
    target_format = target_format.lower().replace(".", "").strip()
    if target_format == "jpeg":
        target_format = "jpg"

    if not image_path:
        image_path = _get_latest_file(IMAGE_EXTENSIONS)

    if not image_path or not os.path.exists(image_path):
        return "I could not find an image file in your Downloads or Desktop to convert, Sir."

    base_name, _ = os.path.splitext(os.path.basename(image_path))
    output_filename = f"{base_name}_converted.{target_format}"
    output_path = os.path.join(DOWNLOADS_DIR, output_filename)

    try:
        with Image.open(image_path) as img:
            # Handle RGBA to RGB if saving to JPG
            if target_format == "jpg" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            save_kwargs = {}
            if target_format in ["jpg", "webp"]:
                save_kwargs["quality"] = quality

            img.save(output_path, **save_kwargs)

        orig_kb = os.path.getsize(image_path) / 1024.0
        new_kb = os.path.getsize(output_path) / 1024.0

        play_fx("complete")
        return f"Image converted to {target_format.upper()} ({new_kb:.1f} KB) and saved to your Downloads, Sir."
    except Exception as e:
        print(f"[IMAGE CONVERT ERROR]: {e}")
        return f"Failed to convert image, Sir: {e}"


def extract_pdf_summary(pdf_path: Optional[str] = None) -> str:
    """Extract and summarize the text of a PDF document."""
    if not pdf_path:
        pdf_path = _get_latest_file([".pdf"])

    if not pdf_path or not os.path.exists(pdf_path):
        return "I could not find a PDF document in your Downloads or Desktop, Sir."

    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        extracted_text = ""

        for page in reader.pages[:5]:  # Read first 5 pages max for overview
            t = page.extract_text()
            if t:
                extracted_text += t + "\n"

        if not extracted_text.strip():
            return f"The PDF has {total_pages} pages, but contains scanned images rather than extractable text, Sir."

        # Pass to LLaMA 3.1:8b for executive summary
        from ai_brain.ai_brain import ask_ai
        prompt = (
            f"Provide a concise 2 to 3 sentence executive summary of the following PDF text from '{os.path.basename(pdf_path)}':\n\n"
            f"{extracted_text[:3000]}"
        )
        summary = ask_ai(prompt)
        play_fx("complete")
        return f"PDF summary of {os.path.basename(pdf_path)} ({total_pages} pages): {summary}"

    except Exception as e:
        print(f"[PDF READ ERROR]: {e}")
        return f"Unable to process PDF: {e}"
