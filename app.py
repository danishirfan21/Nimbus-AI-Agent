import streamlit as st
import os
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- 1. SETUP ---
st.set_page_config(page_title="AI Time Agent", page_icon="🤖")
st.title("🤖 My First AI Agent")
st.caption("Powered by Groq & Llama 3.1")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- 2. THE TOOL ---
def get_current_time():
    return datetime.now().strftime("%I:%M %p")

# --- 3. THE UI LOGIC ---
# Initialize chat history so it doesn't disappear on refresh
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask me for the time..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Agent Logic
    with st.chat_message("assistant"):
        with st.status("Agent is thinking...", expanded=True) as status:
            
            # Initial call to see if it needs the tool
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "get_current_time",
                        "description": "Get the current time."
                    }
                }]
            )
            
            response_message = response.choices[0].message
            
            if response_message.tool_calls:
                st.write("🕒 Checking the system clock...")
                time_now = get_current_time()
                status.update(label="Time retrieved!", state="complete", expanded=False)
                final_answer = f"The current time is {time_now}."
            else:
                status.update(label="Thinking complete", state="complete", expanded=False)
                final_answer = response_message.content
        
        st.markdown(final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
