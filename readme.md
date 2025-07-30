# 🌍 AI Travel Assistant

A Streamlit application that uses AI to generate personalized travel itineraries, search for flights, suggest hotels and restaurants, and send the itinerary via email.

---

## 🚀 Features

- 📍 **Smart travel planning**: Enter destination, trip duration, and trip theme to receive a detailed itinerary.
- ✈️ **Find cheap flights**: Uses Google Flights data via SerpAPI.
- 🏨 **Suggest hotels and restaurants**: AI filters results based on your budget and interests.
- 🧠 **Multi-agent AI system**: Specialized agents handle research, scheduling, and accommodation/food discovery.
- 📧 **Send itinerary via email**: Easily share the full plan with others.

---

## 📦 Installation

### 1. Clone the project
```bash
git clone https://github.com/UncleTien/AgentTravelAssistant.git
cd AgentTravelAssistant
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the root folder with the following content:

```env
SERPAPI_API_KEY=your_serpapi_key
GOOGLE_API_KEY=your_google_genai_key

GMAIL_SENDER_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
```

📌 **Notes:**  
- `SERPAPI_API_KEY`: Get from [SerpAPI](https://serpapi.com/)
- `GOOGLE_API_KEY`: Get from [Google Generative AI](https://makersuite.google.com/app/apikey)
- `GMAIL_APP_PASSWORD`: Set up via [Google App Passwords](https://myaccount.google.com/apppasswords)
- `GMAIL_SENDER_EMAIL`: Email address that the App Password is linked to

---

## 🏃‍♂️ Run the App

```bash
streamlit run main.py
```

The app will open in your default browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
.
├── main.py
├── agents.py
├── config.py
├── utils.py
├── email_utils.py
├── requirements.txt
├── .env
└── README.md
```

---

## 📬 Email Itinerary

After generating the plan, users can enter their email address and click “📤 Send Email” to receive the itinerary, hotel, and restaurant suggestions.

---

## 💡 Notes

- Example IATA airport codes: `SGN` (HCM), `CDG` (Paris), `LHR` (London), `JFK` (New York).
- Flight data is based on [Google Flights via SerpAPI](https://serpapi.com/google-flights-api).
- This app uses `agno` to manage multiple AI agents for task delegation.