"""
Comprehensive Automated Unit Tests for J.A.R.V.I.S. V2 Upgrades
Covers:
1. Real-time Audio Visualizer Bus (RMS, 36-band FFT, speech state sync)
2. Autonomous Protocol Studio (declarative JSON config, work/focus modes, zero-gaming guard)
3. Semantic Memory & FTS5 Conversation Search (BM25 ranking, cross-domain recall)
"""

import unittest
import numpy as np
import time

from voice_engine.audio_visualizer import (
    push_audio_chunk,
    get_visualizer_levels,
    set_speaking_state,
    NUM_BANDS,
)
from system_layer.protocol_controller import (
    load_protocols_config,
    list_protocols,
    activate_gaming_protocol,
    get_protocol_status,
)
import skills.protocol_skill as protocol_skill
from memory_layer.sqlite_memory import (
    store_fact,
    log_conversation,
    search_memory,
    search_conversations,
    search_all_memory,
    parse_memory_command,
)
import skills.memory_skill as memory_skill


class TestAudioVisualizer(unittest.TestCase):
    """Test Real-Time Audio Visualizer Bus."""

    def test_push_audio_chunk_rms_and_bands(self):
        # Generate synthetic 440Hz sine wave
        t = np.linspace(0, 1280 / 16000, 1280, endpoint=False)
        tone = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16)

        push_audio_chunk(tone)
        rms, bands, spk = get_visualizer_levels()

        self.assertGreater(rms, 5000.0, "RMS should capture audible tone energy.")
        self.assertEqual(len(bands), NUM_BANDS, "Spectrum must contain 36 frequency bands.")
        self.assertTrue(np.any(bands > 0.0), "FFT bands should register audio energy.")

    def test_speaking_state_sync(self):
        set_speaking_state(True)
        _, _, spk = get_visualizer_levels()
        self.assertTrue(spk, "Speaking state must be True when engaged.")

        set_speaking_state(False)
        _, _, spk = get_visualizer_levels()
        self.assertFalse(spk, "Speaking state must be False when disengaged.")


class TestProtocolStudio(unittest.TestCase):
    """Test Autonomous Protocol Studio & Workstation Macros."""

    def test_protocols_config_loaded(self):
        cfg = load_protocols_config()
        self.assertIn("work", cfg, "Work protocol must exist in config.")
        self.assertIn("deep_focus", cfg, "Deep Focus protocol must exist in config.")
        self.assertIn("night_coding", cfg, "Night Coding protocol must exist in config.")
        self.assertIn("clean_desk", cfg, "Clean Desk protocol must exist in config.")

    def test_list_protocols_output(self):
        listing = list_protocols()
        self.assertIn("Work Protocol", listing)
        self.assertIn("Deep Focus Protocol", listing)
        self.assertIn("Clean Desk Protocol", listing)

    def test_gaming_protocol_redirect(self):
        res = activate_gaming_protocol()
        self.assertIn("Gaming mode is inactive", res, "Gaming protocol must be disabled per user directive.")

    def test_protocol_skill_routing(self):
        self.assertTrue(protocol_skill.can_handle("activate work protocol"))
        self.assertTrue(protocol_skill.can_handle("start deep focus"))
        self.assertTrue(protocol_skill.can_handle("clean desk protocol"))
        self.assertTrue(protocol_skill.can_handle("list protocols"))

        res = protocol_skill.execute("list protocols")
        self.assertIn("Available Stark Protocols", res)


class TestSemanticMemorySearch(unittest.TestCase):
    """Test SQLite FTS5 Semantic Memory & Conversation History."""

    def setUp(self):
        store_fact("test_ide_preference", "Visual Studio Code", category="test")
        log_conversation(
            user_prompt="how do I scrape financial websites in Python?",
            assistant_response="You can use Beautiful Soup or Playwright with async request handling.",
            intent="coding"
        )

    def test_fts5_fact_search(self):
        results = search_memory("Visual Studio", limit=5)
        self.assertTrue(len(results) > 0, "FTS5 should match 'Visual Studio'.")
        self.assertEqual(results[0]["key"], "test_ide_preference")

    def test_fts5_conversation_search(self):
        convos = search_conversations("financial scrape", limit=5)
        self.assertTrue(len(convos) > 0, "FTS5 should match archived conversation query.")
        self.assertIn("financial", convos[0]["user_prompt"])

    def test_search_all_memory(self):
        all_res = search_all_memory("scrape")
        self.assertIn("conversations", all_res)
        self.assertTrue(len(all_res["conversations"]) > 0)

    def test_memory_skill_search_query(self):
        parsed = parse_memory_command("search memory for financial")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed[0], "search")

        reply = memory_skill.execute("search memory for financial")
        self.assertIn("financial", reply)


if __name__ == "__main__":
    unittest.main()
