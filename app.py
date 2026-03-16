import streamlit as st
import os
import pytz
from groq import Groq
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("🚀 App Refresh: Script starting...")


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

    print(f"📝 User Prompt: {prompt}")
    with st.chat_message("assistant"):
        with st.status("Agent is thinking...", expanded=True) as status:
            print("🤖 Calling LLM for tool detection...")
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
                    print(f"🛠️ Executing tool: {tool_call.function.name} for {location}")
                    st.write(f"🔍 DEBUG: Calling `{tool_call.function.name}` for `{location}`")


                    if tool_call.function.name == "get_current_time":
                        status.update(
                            label=f"🕒 Checking system clock for {location or 'local'}...",
                            state="running"
                        )
                        time_now = get_current_time(location)
                        print(f"🕒 Tool Result (Time): {time_now}")
                        st.write(f"🕒 Tool Result (Time): `{time_now}`")
                        tool_results.append(
                            f"The current time in {location or 'your area'} is {time_now}."
                        )
                    elif tool_call.function.name == "get_weather":
                        status.update(
                            label=f"🌤 Fetching weather data for {location}...",
                            state="running"
                        )
                        weather_info = get_weather(location)
                        print(f"🌤 Tool Result (Weather): {weather_info}")
                        st.write(f"🌤 Tool Result (Weather): `{weather_info}`")
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
                        - Do not invent information.
                        - Keep the answer concise (1–2 sentences).
                        - Combine multiple locations into one natural response.

                        Formatting rules:
                        - Time must use 12-hour format with AM/PM (example: 10:29 PM).
                        - Temperature must use Celsius format like 27°C.
                        - Report weather conditions and temperature exactly as returned by the tool, word for word.
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

