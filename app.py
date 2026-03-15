import streamlit as st
import os
import pytz
from groq import Groq
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- 1. SETUP ---
st.set_page_config(page_title="AI Agent", page_icon="🤖")
st.title("🤖 AI Agent")
st.caption("Powered by Groq & Llama 3.1")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- 2. THE TOOL ---
def get_current_time(location=None):
    try:
        if location:
            # Simple mapping for common cities/locations if needed, 
            # but pytz handles many standard ones.
            tz = pytz.timezone(location)
            now = datetime.now(tz)
            return f"{now.strftime('%I:%M %p')} ({location})"
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
        url = f"https://wttr.in/{location}?format=3"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Could not retrieve weather."
    except Exception:
        return "Weather service currently unavailable."

# --- 3. THE UI LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me about time or weather... e.g. 'What time is it in London and what's the weather in Tokyo?'"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.status("Agent is thinking...", expanded=True) as status:
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

                    if tool_call.function.name == "get_current_time":
                        status.update(
                            label=f"🕒 Checking system clock for {location or 'local'}...",
                            state="running"
                        )
                        time_now = get_current_time(location)
                        tool_results.append(
                            f"The current time in {location or 'your area'} is {time_now}."
                        )
                    elif tool_call.function.name == "get_weather":
                        status.update(
                            label=f"🌤 Fetching weather data for {location}...",
                            state="running"
                        )
                        weather_info = get_weather(location)
                        tool_results.append(
                            f"The weather in {location} is {weather_info}."
                        )
                status.update(
                    label="✔ Response ready",
                    state="complete",
                    expanded=False
                )
                final_answer = "\n\n".join(tool_results)
            else:
                status.update(label="Thinking complete", state="complete", expanded=False)
                final_answer = response_message.content
        
        st.markdown(final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

