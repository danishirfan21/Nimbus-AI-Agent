# ☁️ Nimbus

A lightning-fast AI Agent built with Python, powered by Groq's Llama 3.1 models. **Nimbus** demonstrates the core concepts of "Function Calling" (Tools) where the AI can interact with the real world—specifically checking current time and weather across the globe.

### 🌐 Live Demo
[Check out Nimbus here!](https://danish-time-agent.streamlit.app/)


## 🚀 Features

- **Groq Powered**: Uses `llama-3.1-8b-instant` for near-instant responses.
- **Advanced Function Calling**: Real-time integration with Python functions to fetch data.
- **Nimbus Branding**: A personalized, sleek AI identity with custom status messaging.
- **Professional Weather Logic**: Switched to a robust two-step process:
    - **Geocoding**: Converts location names (e.g., "Paris") into precise coordinates.
    - **Open-Meteo API**: Fetches reliable, live weather data for those coordinates.
- **Enhanced Debugging**: Real-time logging both in the terminal (with `flush=True`) and directly in the Streamlit UI.
- **Interactive UI**: Built with Streamlit featuring a "Nimbus is calculating..." status loop.
- **CLI Mode**: Includes a terminal-based interface for fast, light-weight interaction.


## 🛠️ Setup

1. **Clone the repository** (or navigate to the folder).
2. **Create a virtual environment**:
   ```powershell
   python -m venv .venv
   ```
3. **Install dependencies**:
   ```powershell
   & ".venv/Scripts/python.exe" -m pip install -r requirements.txt
   ```
4. **Configure API Key**:
   Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_gsk_key_here
   ```

## 📖 Usage

### Web Application (Recommended)
Run the Streamlit app:
```powershell
& ".venv/Scripts/python.exe" -m streamlit run app.py
```

### Terminal Agent
Run the interactive CLI agent:
```powershell
& ".venv/Scripts/python.exe" agent.py
```


## 📂 Project Structure

- `app.py`: The main Nimbus web application (Streamlit).
- `agent.py`: The interactive CLI version of Nimbus.
- `requirements.txt`: List of Python dependencies.
- `.env`: (Ignored) Contains your sensitive API keys.
- `.gitignore`: Ensures sensitive and junk files aren't tracked.


## 🧠 How it Works

1. **User asks a question**: "What's the weather in London and what time is it there?"
2. **Nimbus Decides**: The AI identifies that it needs to call specific tools for location data.
3. **Execution & Observation**: 
   - **Time**: Calls `get_current_time` with the detected timezone.
   - **Weather**: Calls `get_weather` which handles geocoding and the Open-Meteo API.
4. **Natural Response**: Nimbus observes the raw data, applies conversational rules, and responds: "It's currently 06:45 PM in London with clear skies and a temperature of 18°C."
