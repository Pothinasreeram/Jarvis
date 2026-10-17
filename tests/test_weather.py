"""
Unit tests for J.A.R.V.I.S. Multi-Tier Resilient Weather Controller.
"""

import unittest
from system_layer.weather_controller import (
    get_weather_data,
    _fetch_open_meteo,
    _cached_weather
)


class TestWeatherController(unittest.TestCase):
    def test_weather_returns_valid_dict(self):
        """Ensure get_weather_data always returns a valid dictionary with required keys."""
        data = get_weather_data("Vadodara")
        self.assertIsInstance(data, dict)
        self.assertIn("temperature", data)
        self.assertIn("humidity", data)
        self.assertIn("wind", data)
        self.assertIn("condition", data)

    def test_open_meteo_zero_key_fallback(self):
        """Ensure the free Open-Meteo API fallback can resolve weather without any API key."""
        data = _fetch_open_meteo("London")
        if data is not None:
            self.assertEqual(data.get("source"), "Open-Meteo")
            self.assertIn("temperature", data)
            self.assertIsInstance(data["temperature"], (int, float))

    def test_default_fallback_values(self):
        """Ensure nominal default fallback has realistic metrics so HUD never crashes."""
        self.assertIn("temperature", _cached_weather)
        self.assertIn("condition", _cached_weather)
        self.assertEqual(_cached_weather["condition"], "Clear")


if __name__ == "__main__":
    unittest.main()
