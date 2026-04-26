"""weather.py — Get weather using Open-Meteo (100% free, no API key)"""
import json
import threading


def weather_action(parameters: dict, player=None) -> str:
    city         = parameters.get("city", "Delhi")
    show_anim    = parameters.get("show_animation", True)

    try:
        import requests
    except ImportError:
        return "requests not installed."

    # Step 1: Geocode city → lat/lon
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=8,
        ).json()
        loc = geo["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        city_name = loc.get("name", city)
        country   = loc.get("country", "")
    except Exception as e:
        return f"Could not locate city '{city}': {e}"

    # Step 2: Fetch weather
    try:
        wdata = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "hourly": "relativehumidity_2m",
                "timezone": "auto",
            },
            timeout=8,
        ).json()
        cw      = wdata["current_weather"]
        temp    = cw["temperature"]
        wind    = cw["windspeed"]
        wcode   = cw["weathercode"]
        humidity = wdata.get("hourly", {}).get("relativehumidity_2m", [50])[0]
    except Exception as e:
        return f"Weather fetch error: {e}"

    # Map WMO code to condition
    cond_map = {
        0:"Clear", 1:"Clear", 2:"Partly Cloudy", 3:"Overcast",
        45:"Fog", 48:"Fog", 51:"Drizzle", 53:"Drizzle", 55:"Drizzle",
        61:"Rain", 63:"Rain", 65:"Heavy Rain",
        71:"Snow", 73:"Snow", 75:"Heavy Snow",
        80:"Showers", 81:"Showers", 82:"Heavy Showers",
        95:"Thunderstorm", 96:"Thunderstorm", 99:"Thunderstorm",
    }
    cond = cond_map.get(wcode, "Clear")

    result = (f"Weather in {city_name}, {country}:\n"
              f"Temperature: {temp}°C\n"
              f"Condition: {cond}\n"
              f"Wind: {wind} km/h\n"
              f"Humidity: {humidity}%")

    if show_anim and player and hasattr(player, "anim"):
        anim_data = json.dumps({
            "temp": temp, "condition": cond,
            "city": f"{city_name}, {country}",
            "humidity": humidity, "wind": wind,
        })
        def _show():
            player.anim.show(
                anim_type="weather",
                title=city_name,
                content=anim_data,
                color="#00d4ff",
                duration=10,
            )
        threading.Thread(target=_show, daemon=True).start()

    return result
