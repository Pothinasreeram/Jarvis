"""
Unit tests for J.A.R.V.I.S. Voice Engine speech normalization and preparation.
"""

import unittest
from voice_engine.voice import (
    normalize_speech_command,
    prepare_speech_text,
    make_speech_friendly,
    is_speaking,
    speaking_status
)


class TestVoiceEngine(unittest.TestCase):
    def test_normalize_symbols(self):
        """Ensure spoken symbol phrases are mapped to punctuation."""
        self.assertEqual(normalize_speech_command("open file dot txt"), "open file.txt")
        self.assertEqual(normalize_speech_command("search python dash script"), "search python-script")
        self.assertEqual(normalize_speech_command("function open parenthesis close parenthesis"), "function()")

    def test_underscore_intelligence(self):
        """Ensure 'underscore' between words becomes '_' but remains conceptual when asked."""
        self.assertEqual(normalize_speech_command("user underscore name"), "user_name")
        self.assertEqual(normalize_speech_command("what is an underscore"), "what is an underscore")

    def test_prepare_speech_text(self):
        """Ensure programming symbols and extensions are stripped for clean TTS audio."""
        cleaned = prepare_speech_text("running test_script.py now")
        self.assertNotIn(".py", cleaned)
        self.assertNotIn("_", cleaned)

    def test_speaking_status(self):
        """Ensure speaking status defaults to boolean False when quiet."""
        self.assertFalse(speaking_status())


if __name__ == "__main__":
    unittest.main()
