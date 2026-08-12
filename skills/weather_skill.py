from system_layer.weather_controller import get_weather

skill = {
    "name": "Weather",
    "priority": 30
}


def can_handle(command):
    return "weather" in command


def execute(command):

    command = command.lower()

    city = command.replace("weather", "")
    city = city.replace("in", "").strip()

    if city == "":
        city = "Vadodara"

    return get_weather(city)