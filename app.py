import streamlit as st
import os
import pytz
from groq import Groq
import requests
from datetime import datetime
from dotenv import load_dotenv
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

print("🚀 App Refresh: Script starting...", flush=True)
logger.info("🚀 App Refresh: Script starting...")


# --- 1. SETUP ---
st.set_page_config(page_title="Nimbus", page_icon="☁️")
st.title("☁️ Nimbus")
st.caption("Your Personal Weather & Time Agent | Powered by Groq")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- 2. THE TOOL ---
def get_current_time(location=None):
    try:
        if location:
            # Simple mapping for common cities/locations if needed, 
            # but pytz handles many standard ones.
            tz = pytz.timezone(location)
            now = datetime.now(tz)
            return now.strftime('%I:%M %p')
        else:
            # Default to UTC or a specific local time
            now = datetime.now()
            return f"{now.strftime('%I:%M %p')} (Local Server Time)"
    except Exception:
        # Fallback if timezone is not found
        now = datetime.now()
        return f"{now.strftime('%I:%M %p')} (Local Server Time)"

def get_weather(location):
    try:
        print(f"📡 Geocoding location: {location}", flush=True)
        # 1. Geocode location to lat/long using params for proper encoding
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
            print(f"❌ Geocoding failed for: {location}", flush=True)
            return f"Could not find coordinates for {location}."

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        city_name = geo_data["results"][0]["name"]
        
        print(f"📍 Found {city_name} at {lat}, {lon}. Fetching weather...", flush=True)

        # 2. Get weather for these coordinates
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url, timeout=10)
        weather_data = weather_res.json()

        if "current_weather" in weather_data:
            current = weather_data["current_weather"]
            temp = current["temperature"]
            code = current["weathercode"]
            
            # Simple mapping for WMO weather codes
            # Reference: https://open-meteo.com/en/docs
            conditions = {
                0: "clear skies",
                1: "mainly clear", 2: "partly cloudy", 3: "overcast",
                45: "foggy", 48: "depositing rime fog",
                51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
                61: "slight rain", 63: "moderate rain", 65: "heavy rain",
                71: "slight snow", 73: "moderate snow", 75: "heavy snow",
                77: "snow grains",
                80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
                95: "thunderstorm",
            }
            condition = conditions.get(code, "current conditions")
            
            return f"Weather in {city_name}: {temp}°C, {condition}"
        else:
            return "Could not retrieve current weather data."

    except Exception as e:
        print(f"💥 Weather function crashed: {str(e)}", flush=True)
        logger.error(f"Weather function exception: {e}")
        return "Weather service currently unavailable."

# --- 3. THE UI LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask Nimbus about time or weather..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    print(f"📝 User Prompt: {prompt}", flush=True)
    logger.info(f"📝 User Prompt: {prompt}")
    with st.chat_message("assistant"):
        with st.status("Nimbus is calculating...", expanded=True) as status:
            print("☁️ Nimbus is calling LLM...", flush=True)
            logger.info("☁️ Nimbus is calling LLM...")
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
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
                                    "description": "The location or timezone (e.g., 'America/New_York', 'Europe/London', 'Asia/Karachi')."
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
            )
            
            response_message = response.choices[0].message
            
            if response_message.tool_calls:
                import json
                tool_results = []
                for tool_call in response_message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    location = args.get("location")
                    print(f"🛠️ Executing tool: {tool_call.function.name} for {location}", flush=True)
                    logger.info(f"🛠️ Executing tool: {tool_call.function.name} for {location}")
                    st.write(f"🔍 DEBUG: Calling `{tool_call.function.name}` for `{location}`")


                    if tool_call.function.name == "get_current_time":
                        status.update(
                            label=f"🕒 Checking system clock for {location or 'local'}...",
                            state="running"
                        )
                        time_now = get_current_time(location)
                        print(f"🕒 Tool Result (Time): {time_now}", flush=True)
                        logger.info(f"🕒 Tool Result (Time): {time_now}")
                        st.write(f"🕒 Tool Result (Time): `{time_now}`")
                        st.toast(f"Time fetched: {time_now}")
                        tool_results.append(
                            f"The current time in {location or 'your area'} is {time_now}."
                        )
                    elif tool_call.function.name == "get_weather":
                        status.update(
                            label=f"🌤 Fetching weather data for {location}...",
                            state="running"
                        )
                        weather_info = get_weather(location)
                        print(f"🌤 Tool Result (Weather): {weather_info}", flush=True)
                        logger.info(f"🌤 Tool Result (Weather): {weather_info}")
                        st.write(f"🌤 Tool Result (Weather): `{weather_info}`")
                        st.toast(f"Weather fetched: {weather_info}")
                        tool_results.append(f"Weather: {weather_info}")
                status.update(
                    label="Response ready",
                    state="complete",
                    expanded=False
                )
                raw_data = "\n".join(tool_results)
                naturalise = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        { "role": "system", "content": 
                        """
                        You convert tool results into a clear, natural response.

                        Rules:
                        - Use ONLY the exact data provided in the tool results. Do not add, infer, or interpret anything beyond it.
                        - Do not describe or characterize the weather (e.g. do not say "chilly", "warm", "pleasant", "mix of conditions", "great day"). Only state what was explicitly given.
                        - Do not invent information. This includes weather conditions like "cloudy", "sunny", "rainy" — do NOT mention them unless the tool result string explicitly contains that word.
                        - Do NOT mention the absence of data. If weather was not fetched for a location, say nothing about it — do not say "no weather available" or "weather information is unavailable".
                        - Only report what was actually retrieved. Each location should only be described using the data that was fetched for it.
                        - Keep the answer concise (1–2 sentences).
                        - Combine multiple locations into one natural response.

                        Weather fields to include: temperature and weather condition ONLY IF explicitly present in the tool result string.
                        Weather fields to EXCLUDE: wind speed, humidity, pressure, visibility, UV index, or any other metric not listed above.

                        Formatting rules:
                        - Time must use 12-hour format with AM/PM (example: 10:29 PM).
                        - Temperature must use Celsius format like 27°C.
                        - If a weather condition word (e.g. "cloudy", "rain", "sunny") does not appear in the tool result, do NOT mention any condition at all.
                        """
                        },
                        { "role": "user", "content": f"Original question: {prompt}\n\nTool results:\n{raw_data}" }
                    ]
                )
                final_answer = naturalise.choices[0].message.content
                print(f"✅ Final Answer Generated: {final_answer}")
            else:
                status.update(label="Thinking complete", state="complete", expanded=False)
                final_answer = response_message.content
        
        st.markdown(final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

