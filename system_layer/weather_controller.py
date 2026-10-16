import os
import requests
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
print("Loading:", env_path)

load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("TOMORROW_API_KEY")


def get_weather_data(city):
    """
    Fetch structured realtime weather data.

    Returns:
        dict containing city, temperature, humidity and wind
        or None if the request fails.
    """

    url = "https://api.tomorrow.io/v4/weather/realtime"

    params = {
        "location": city,
        "apikey": API_KEY
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print("Weather Status Code:", response.status_code)

        if response.status_code != 200:
            print("Weather Response:", response.text)
            return None

        data = response.json()
        values = data["data"]["values"]

        temperature = values.get("temperature")
        humidity = values.get("humidity")
        wind = values.get("windSpeed")

        return {
            "city": city,
            "temperature": temperature,
            "humidity": humidity,
            "wind": wind
        }

    except Exception as e:
        print("[WEATHER ERROR]:", e)
        return None


def get_weather(city):
    """
    Existing JARVIS voice/text weather response.
    Kept compatible with the existing weather skill.
    """

    weather = get_weather_data(city)

    if weather is None:
        return "Sorry sir, I couldn't fetch the weather."

    return (
        f"The current temperature in {city} is "
        f"{weather['temperature']} degrees Celsius. "
        f"Humidity is {weather['humidity']} percent "
        f"and wind speed is {weather['wind']} kilometers per hour."
    )