"""
J.A.R.V.I.S. System Vision Controller Adapter
Routes high-level vision and screen analysis requests to the vision.py engine.
"""

from vision import (
    analyze_screen,
    read_screen_text,
    save_screenshot,
    capture_screen
)

def take_screenshot():
    """Captures and archives screenshot to screenshots directory."""
    return save_screenshot()

def read_screen():
    """Extracts all visible text on screen via local OCR."""
    return read_screen_text()

def describe_screen():
    """Generates a concise 2-3 sentence overview of active screen contents."""
    return analyze_screen("Describe what is visible on the user's screen in 2 to 3 concise sentences.")

def explain_error():
    """Diagnoses programming or runtime errors visible on the screen."""
    return analyze_screen("Identify the error or exception shown on the screen and explain how to fix it in 2 to 3 concise sentences.")

def explain_code():
    """Explains source code visible on the screen."""
    return analyze_screen("Explain the code visible on the screen concisely in 2 to 3 sentences.")

def find_bugs():
    """Performs static code review on visible on-screen code."""
    return analyze_screen("Find any bugs, syntax mistakes, or issues in the code shown on the screen.")

def optimize_code():
    """Suggests performance and style optimizations for visible code."""
    return analyze_screen("Suggest optimizations for the code shown on the screen.")

def fix_code():
    """Provides bugfixes and corrected code for visible code issues."""
    return analyze_screen("Provide the corrected version of the code or bug shown on the screen.")

def add_comments():
    """Generates commented code based on on-screen code."""
    return analyze_screen("Provide the code shown on the screen with clear professional comments added.")

def generate_documentation():
    """Generates Markdown documentation for on-screen modules or functions."""
    return analyze_screen("Generate concise documentation for the code shown on the screen.")

# Safe backward-compatibility helpers
def capture_code_window():
    """Legacy helper fallback."""
    return capture_screen()

def capture_code():
    """Non-destructive OCR code capture fallback."""
    return read_screen_text()
