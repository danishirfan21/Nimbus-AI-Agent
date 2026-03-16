import os
import pytz
import requests
import json
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

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
        # 1. Geocode
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=10)
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
    print(f"User: {user_prompt}")
    print("☁️ Nimbus is thinking...")
    
    messages = [{"role": "user", "content": user_prompt}]
    
    tools = [{
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
                        "description": "The city and country (e.g., 'London, UK', 'Karachi, Pakistan')."
                    }
                }
            }
        }
    }]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        messages.append(response_message)
        
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            location = args.get("location")
            
            print(f"🛠️ Nimbus executing: {name} for {location}...")
            
            if name == "get_current_time":
                result = get_current_time(location)
            else:
                result = get_weather(location)
                
            print(f"📥 Result: {result}")
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": name,
                "content": result,
            })
        
        second_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )
        print(f"☁️ Nimbus: {second_response.choices[0].message.content}")
    else:
        print(f"☁️ Nimbus: {response_message.content}")

if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            break
        run_agent(user_input)