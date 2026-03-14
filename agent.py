import os
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. Setup the Client for Groq
# Make sure to set GROQ_API_KEY in your .env file or environment
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
)

# 2. Define the "Tool" (The action the agent can take)
def get_current_time():
    return datetime.now().strftime("%I:%M %p")

# 3. The Logic
def run_agent(user_prompt):
    print(f"User: {user_prompt}")
    
    # Initialize messages list
    messages = [{"role": "user", "content": user_prompt}]
    
    # Define available tools
    tools = [{
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time if the user asks for it."
        }
    }]

    # Initial call to the model
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # Check if the AI wants to use the tool
    if tool_calls:
        # Add the assistant's message to the conversation history
        messages.append(response_message)
        
        # Process each tool call
        for tool_call in tool_calls:
            if tool_call.function.name == "get_current_time":
                time_info = get_current_time()
                print(f"Agent: Checked the clock... it's {time_info}.")
                
                # Add tool response to history
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "get_current_time",
                    "content": time_info,
                })
        
        # Second call to get the final natural language response
        second_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=tools # Keep tools defined in follow-up
        )
        print(f"Agent: {second_response.choices[0].message.content}")
    else:
        print(f"Agent: {response_message.content}")


# 4. Test it
if __name__ == "__main__":
    run_agent("Hey, what time is it right now?")