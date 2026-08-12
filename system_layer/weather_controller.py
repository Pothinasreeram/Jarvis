import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
print("Loading:", env_path)

load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("TOMORROW_API_KEY")


def get_weather(city):

    url = "https://api.tomorrow.io/v4/weather/realtime"

    params = {
        "location": city,
        "apikey": API_KEY
    }

    response = requests.get(url, params=params)

    print("Status Code:", response.status_code)
    print("Response:", response.text)
 
    if response.status_code != 200:
        return "Sorry sir, I couldn't fetch the weather."

    data = response.json()

    values = data["data"]["values"]

    temperature = values["temperature"]
    humidity = values["humidity"]
    wind = values["windSpeed"]

    return (
        f"The current temperature in {city} is "
        f"{temperature} degrees Celsius. "
        f"Humidity is {humidity} percent "
        f"and wind speed is {wind} kilometers per hour."
    )