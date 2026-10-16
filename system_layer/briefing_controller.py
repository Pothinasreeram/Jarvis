"""
Stark Executive Morning Briefing Controller for J.A.R.V.I.S.
Synthesizes date, local weather, taskmaster directives, hardware diagnostics,
wellness tracking, and top tech headlines into a seamless audio-visual intelligence briefing.
"""

from datetime import datetime
from voice_engine.sound_effects import play_fx
from system_layer.weather_controller import get_weather_data
from system_layer.todo_controller import get_active_tasks
from system_layer.diagnostics_controller import get_hardware_telemetry
from system_layer.web_agent import get_top_tech_news
from background_tasks.wellness_monitor import get_hydration_count


def generate_executive_briefing() -> str:
    """Generate comprehensive Tony Stark executive day briefing."""
    play_fx("wake")

    now = datetime.now()
    hour = now.hour

    if hour < 12:
        greeting = "Good morning, Sir."
    elif 12 <= hour < 17:
        greeting = "Good afternoon, Sir."
    else:
        greeting = "Good evening, Sir."

    date_str = now.strftime("%A, %B %d")
    time_str = now.strftime("%I:%M %p")

    # 1. Weather
    weather_summary = "Weather data is currently updating"
    try:
        w_data = get_weather_data("Vadodara")
        if w_data:
            temp = int(w_data.get("temperature", 29))
            cond = w_data.get("condition", "Clear")
            hum = w_data.get("humidity", 70)
            weather_summary = f"The atmospheric conditions in Vadodara are currently {cond} at {temp} degrees Celsius, with {hum} percent humidity"
    except Exception:
        pass

    # 2. Taskmaster Directives
    todo_summary = "You currently have zero pending task directives"
    try:
        active_todos = get_active_tasks(limit=3)
        if active_todos:
            tasks_text = ", ".join([f"Directive {t['id']}: {t['task']}" for t in active_todos])
            todo_summary = f"You have {len(active_todos)} priority directives awaiting execution: {tasks_text}"
        else:
            todo_summary = "All task objectives are currently cleared"
    except Exception:
        pass

    # 3. Hardware & Power
    diag_summary = "Hardware envelopes nominal"
    try:
        diag = get_hardware_telemetry()
        cpu_load = diag.get("cpu_pct", 10)
        batt_pct = diag.get("batt_pct", 100)
        plugged = diag.get("is_plugged", True)
        power_str = "on AC mains" if plugged else f"on battery power at {batt_pct}%"
        diag_summary = f"Processor load is at {cpu_load} percent, and the workstation is {power_str}"
    except Exception:
        pass

    # 4. Top Tech Headline
    headline_summary = ""
    try:
        news = get_top_tech_news(limit=1)
        if news:
            h = news[0]['title'].replace("&quot;", '"').replace("&amp;", "&")
            headline_summary = f"In global technology news: {h}."
    except Exception:
        pass

    # 5. Hydration
    water_count = get_hydration_count()
    water_summary = f"You have logged {water_count} of 8 glasses of water today."

    # Assemble speech
    briefing = (
        f"{greeting} The time is {time_str} on {date_str}. "
        f"{weather_summary}. "
        f"{todo_summary}. "
        f"{diag_summary}. "
        f"{headline_summary} "
        f"{water_summary} "
        f"All J.A.R.V.I.S. neural subsystems are fully operational, Sir. What is your directive?"
    )

    return briefing
