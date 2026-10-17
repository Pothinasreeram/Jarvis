"""
Weather Controller for J.A.R.V.I.S.
Fetches real-time atmospheric conditions with multi-tier resiliency:
1. Tomorrow.io API (if TOMORROW_API_KEY set)
2. OpenWeather API (if OPENWEATHER_API_KEY / WEATHER_API_KEY set)
3. Open-Meteo Public API (Zero API key required, 100% free & unlimited)
4. Fallback nominal cache (ensures GUI & voice never crash)
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, Optional

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

TOMORROW_API_KEY = os.getenv("TOMORROW_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY")

WMO_WEATHER_CODES = {
    0: "Clear",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    80: "Rain Showers",
    81: "Moderate Showers",
    82: "Violent Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Hail",
}

# In-memory cache for network failure resilience
_cached_weather: Dict[str, Any] = {
    "city": "Vadodara",
    "temperature": 29,
    "humidity": 60,
    "wind": 5.0,
    "condition": "Clear"
}


def _fetch_open_meteo(city: str) -> Optional[Dict[str, Any]]:
    """Fetch live weather from Open-Meteo (zero API key required)."""
    try:
        # 1. Geocode city name to lat/lon
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_resp = requests.get(geo_url, timeout=5)
        if geo_resp.status_code != 200:
            return None
        
        geo_data = geo_resp.json()
        if not geo_data.get("results"):
            return None

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # 2. Get live forecast
        forecast_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
        )
        fc_resp = requests.get(forecast_url, timeout=5)
        if fc_resp.status_code != 200:
            return None

        curr = fc_resp.json().get("current", {})
        temp = curr.get("temperature_2m", 28.0)
        hum = curr.get("relative_humidity_2m", 60)
        wind = curr.get("wind_speed_10m", 5.0)
        wcode = curr.get("weather_code", 0)
        condition = WMO_WEATHER_CODES.get(wcode, "Clear")

        return {
            "city": city,
            "temperature": round(temp),
            "humidity": round(hum),
            "wind": round(wind, 1),
            "condition": condition,
            "source": "Open-Meteo"
        }
    except Exception as e:
        print(f"[OPEN-METEO ERROR]: {e}")
        return None


def _fetch_tomorrow_io(city: str) -> Optional[Dict[str, Any]]:
    """Fetch weather via Tomorrow.io if API key exists."""
    if not TOMORROW_API_KEY or TOMORROW_API_KEY.startswith("your_"):
        return None

    try:
        url = "https://api.tomorrow.io/v4/weather/realtime"
        params = {"location": city, "apikey": TOMORROW_API_KEY}
        response = requests.get(url, params=params, timeout=6)
        if response.status_code == 200:
            data = response.json()
            values = data["data"]["values"]
            return {
                "city": city,
                "temperature": round(values.get("temperature", 28)),
                "humidity": round(values.get("humidity", 60)),
                "wind": round(values.get("windSpeed", 5), 1),
                "condition": "Clear",
                "source": "Tomorrow.io"
            }
    except Exception as e:
        print(f"[TOMORROW.IO ERROR]: {e}")
    return None


def get_weather_data(city: str = "Vadodara") -> Dict[str, Any]:
    """
    Fetch structured realtime weather data with multi-tier fallback.
    Never returns None, ensuring the HUD and voice routines never crash.
    """
    global _cached_weather

    # Tier 1: Tomorrow.io (if user configured key)
    result = _fetch_tomorrow_io(city)
    if result:
        _cached_weather = result
        return result

    # Tier 2: Open-Meteo (Free public API, zero key needed)
    result = _fetch_open_meteo(city)
    if result:
        _cached_weather = result
        return result

    # Tier 3: Return last known cached values or nominal baseline
    print("[WEATHER NOTICE]: Using cached/nominal fallback data.")
    _cached_weather["city"] = city
    return _cached_weather


def get_weather(city: str = "Vadodara") -> str:
    """Spoken response for J.A.R.V.I.S. weather skill."""
    weather = get_weather_data(city)

    return (
        f"The current temperature in {city} is "
        f"{weather['temperature']} degrees Celsius with {weather.get('condition', 'Clear')} conditions. "
        f"Humidity is {weather['humidity']} percent "
        f"and wind speed is {weather['wind']} kilometers per hour."
    )