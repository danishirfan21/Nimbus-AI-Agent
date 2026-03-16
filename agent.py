import os
import pytz
import requests
import json
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client (Native SDK)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_current_time(location=None):
    try:
        if location:
            tz = pytz.timezone(location)
            now = datetime.now(tz)
            return f"{now.strftime('%I:%M %p')} ({location})"
        else:
            now = datetime.now()
            return f"{now.strftime('%I:%M %p')} (Local Server Time)"
    except Exception:
        now = datetime.now()
        return f"{now.strftime('%I:%M %p')} (Local Server Time)"

def get_weather(location):
    """Nimbus weather tool using Open-Meteo"""
    try:
        # 1. Geocode using params for proper encoding
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        geo_res = requests.get(geo_url, params=geo_params, timeout=10)
        geo_data = geo_res.json()

        if not geo_data.get("results"):
            # Fallback: Try the first word of the location if comma-separated
            if "," in location:
                simple_location = location.split(",")[0].strip()
                geo_params["name"] = simple_location
                geo_res = requests.get(geo_url, params=geo_params, timeout=10)
                geo_data = geo_res.json()
            
            if not geo_data.get("results"):
                return f"Could not find coordinates for {location}."

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        city_name = geo_data["results"][0]["name"]
        
        # 2. Extract Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url, timeout=10)
        weather_data = weather_res.json()

        if "current_weather" in weather_data:
            current = weather_data["current_weather"]
            temp = current["temperature"]
            code = current["weathercode"]
            
            conditions = {
                0: "clear skies", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
                45: "foggy", 48: "rime fog", 51: "light drizzle", 53: "moderate drizzle",
                55: "dense drizzle", 61: "slight rain", 63: "moderate rain", 65: "heavy rain",
                71: "slight snow", 73: "moderate snow", 75: "heavy snow", 95: "thunderstorm",
            }
            condition = conditions.get(code, "current conditions")
            return f"Weather in {city_name}: {temp}°C, {condition}"
        else:
            return "Could not retrieve weather data."
    except Exception as e:
        return f"Weather service error: {str(e)}"

def run_agent(user_prompt):
    print(f"\n[*] User: {user_prompt}")
    print("[Nimbus] calculating...")
    
    # 1. Detect if tools are needed
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": user_prompt}],
        tools=[{
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Get the current time for a specific location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location/timezone (e.g., 'Europe/London', 'Asia/Karachi')."
                        }
                    }
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a specific location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city name (e.g., 'London', 'Karachi', 'New York')."
                        }
                    }
                }
            }
        }]
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        tool_results = []
        
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            location = args.get("location")
            
            print(f"[Nimbus] calling {name} for {location}...")
            
            if name == "get_current_time":
                result = get_current_time(location)
            else:
                result = get_weather(location)
                
            print(f"[Result] {result}")
            tool_results.append(result)
        
        # 2. Naturalise response
        raw_data = "\n".join(tool_results)
        naturalize_prompt = [
            {"role": "system", "content": """
                You convert tool results into a clear, natural response.
                
                Rules:
                - Use ONLY the exact data provided in the tool results. Do not add, infer, or interpret anything beyond it.
                - Do not describe or characterize the weather (e.g. do not say "chilly", "warm", "pleasant", "mix of conditions", "great day"). Only state what was explicitly given.
                - Do not invent information. This includes weather conditions like "cloudy", "sunny", "rainy" — do NOT mention them unless the tool result string explicitly contains that word.
                - Do NOT mention the absence of data. If weather was not fetched for a location, say nothing about it.
                - Only report what was actually retrieved.
                - Keep the answer concise (1–2 sentences).
                - Combine multiple locations into one natural response.

                Weather fields to include: temperature and weather condition ONLY IF explicitly present in the tool result string.
                Weather fields to EXCLUDE: wind speed, humidity, pressure, visibility, UV index, or any other metric not listed above.

                Formatting rules:
                - Time must use 12-hour format with AM/PM (example: 10:29 PM).
                - Temperature must use Celsius format like 27°C.
                - If a weather condition word (e.g. "cloudy", "rain", "sunny") does not appear in the tool result, do NOT mention any condition at all.
            """},
            {"role": "user", "content": f"User's Question: {user_prompt}\n\nTool Data:\n{raw_data}"}
        ]
        
        second_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=naturalize_prompt
        )
        print(f"\n[Nimbus] {second_response.choices[0].message.content}")
    else:
        print(f"\n[Nimbus] {response_message.content}")

if __name__ == "__main__":
    print("--- Nimbus AI Agent (CLI) ---")
    print("Type 'exit' to quit.")
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                break
            if not user_input.strip():
                continue
            run_agent(user_input)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Error] {e}")