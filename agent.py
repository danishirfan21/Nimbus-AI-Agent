import os
import pytz
import requests
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

def get_current_time(location=None):
    try:
        if location:
            tz = pytz.timezone(location)
            now = datetime.now(tz)
            return f"The current time in {location} is {now.strftime('%I:%M %p')}."
        else:
            now = datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')} (Local Server Time)."
    except Exception:
        now = datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')} (Local Server Time)."

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

def run_agent(user_prompt):
    print(f"User: {user_prompt}")
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
            if tool_call.function.name == "get_current_time":
                import json
                args = json.loads(tool_call.function.arguments)
                location = args.get("location")

                time_info = get_current_time(location)
                print(f"Agent: Checked the clock for {location or 'local'}... it's {time_info}.")

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "get_current_time",
                    "content": time_info,
                })
            elif tool_call.function.name == "get_weather":
                import json
                args = json.loads(tool_call.function.arguments)
                location = args.get("location")

                weather_info = get_weather(location)
                print(f"Agent: Checked the weather for {location}... {weather_info}.")

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "get_weather",
                    "content": weather_info,
                })

        second_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )
        print(f"Agent: {second_response.choices[0].message.content}")
    else:
        print(f"Agent: {response_message.content}")



# 4. Test it
if __name__ == "__main__":
    run_agent("Hey, what time is it right now?")