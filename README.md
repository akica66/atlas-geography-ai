# 🌍 Atlas: Live AI Geography Guide & Mapping Bot

Atlas is an interactive desktop application built in Python that combines advanced generative AI with real-time geospatial tracking. Users can chat with "Atlas" a very knowlegable, sharp geography scholar and watch the embedded live map instantly pan, zoom, and drop tracking markers on the exact locations discussed during the conversation.

## 🚀 Features

- **Asynchronous AI Chat:** Powered by the Google Gemini API (`gemini-2.5-flash`) to deliver dynamic, highly specific geographical facts.
- **Live Interactive Map:** Integrated `tkintermapview` render engine centered on global OpenStreetMap tilesets.
- **Automated Telemetry Parsing:** Custom regex engine that catches location tags from the AI's hidden response metadata.
- **Geocoding Pipeline:** Connects directly to the TomTom Developer API to convert text strings into precise latitude and longitude coordinates.

---

## 🛠️ Installation & Setup:

### 1. Prerequisites
Make sure you have Python installed on your system. You will also need to install the required external packages:

```bash
pip install google-genai tkintermapview requests

2. Clone the Repository

git clone [https://github.com/akica66/atlas-geography-ai.git](https://github.com/akica66/atlas-geography-ai.git)
cd atlas-geography-ai

### 3. Configure your environment keys:

This project uses masked environment variables to protect personal API credentials.

1. Locate the .env.example file in the root directory.

2. Duplicate the file and rename the copy to exactly .env.

3. Open .env and paste your personal API keys into the placeholders (do not add extra spaces):

GEMINI_API_KEY=AIzaSyYourActualGeminiKeyHere
TOMTOM_API_KEY=YourActualTomTomKeyHere

Note: The .env file is explicitly ignored by git configuration and will never be pushed to public repositories.

### 4. How to Run: 

Launch the application terminal interface by executing the main script:

```bash
python bot.py

Type a question or name a unique geographic anomaly (e.g., "Tell me about the Baarle-Nassau enclave" or "Where is the source of the Nile?") and watch the tracker sync live!
