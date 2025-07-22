import streamlit as st
import json
from config import SERPAPI_KEY
from utils import format_datetime, fetch_flights, extract_cheapest_flights
from agents import researcher, planner, hotel_restaurant_finder

st.set_page_config(page_title="🌍 AI Travel Planner", layout="wide")
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            font-size: 32px;
            font-weight: 600;
            color: #2c3e50;
        }
        .subtitle {
            text-align: center;
            font-size: 18px;
            color: #7f8c8d;
        }
        .stSlider > div {
            background-color: #f4f6f7;
            padding: 10px;
            border-radius: 8px;
        }
        .simple-card {
            border: 1px solid #e1e1e1;
            border-radius: 8px;
            padding: 16px;
            background: #fff;
            box-shadow: 0 2px 8px rgba(44,62,80,0.04);
            margin-bottom: 16px;
        }
        .simple-btn {
            display: inline-block;
            padding: 8px 18px;
            font-size: 15px;
            font-weight: 500;
            color: #fff;
            background-color: #2980b9;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="title">AI Agent Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Plan your dream trip with AI. Get simple, personalized recommendations for flights, hotels, and activities.</p>', unsafe_allow_html=True)

st.markdown("### Where are you headed?")
source = st.text_input("Departure City (IATA Code):", "BOM")
destination = st.text_input("Destination (IATA Code):", "DEL")

st.markdown("### Plan Your Adventure")
num_days = st.slider("Trip Duration (days):", 1, 14, 5)
travel_theme = st.selectbox(
    "Select Your Travel Theme:",
    ["Couple Getaway", "Family Vacation", "Adventure Trip", "Solo Exploration"]
)

st.markdown("---")

st.markdown(
    f"""
    <div style="
        text-align: center; 
        padding: 10px; 
        background-color: #f4f6f7; 
        border-radius: 8px; 
        margin-top: 10px;
    ">
        <h3 style="color:#2980b9;">Your {travel_theme} to {destination} is about to begin!</h3>
        <p style="color:#7f8c8d;">Let's find the best flights, stays, and experiences for your journey.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

activity_preferences = st.text_area(
    "What activities do you enjoy? (e.g., relaxing on the beach, exploring historical sites, nightlife, adventure)",
    "Relaxing on the beach, exploring historical sites"
)

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

st.sidebar.title("Travel Assistant")
st.sidebar.subheader("Personalize Your Trip")

budget = st.sidebar.radio("Budget Preference:", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("Flight Class:", ["Economy", "Business", "First Class"])
hotel_rating = st.sidebar.selectbox("Preferred Hotel Rating:", ["Any", "3⭐", "4⭐", "5⭐"])

st.sidebar.subheader("Packing Checklist")
packing_list = {
    "Clothes": True,
    "Comfortable Footwear": True,
    "Sunglasses & Sunscreen": False,
    "Travel Guidebook": False,
    "Medications & First-Aid": True
}
for item, checked in packing_list.items():
    st.sidebar.checkbox(item, value=checked)

st.sidebar.subheader("Travel Essentials")
visa_required = st.sidebar.checkbox("Check Visa Requirements")
travel_insurance = st.sidebar.checkbox("Get Travel Insurance")
currency_converter = st.sidebar.checkbox("Currency Exchange Rates")

params = {
    "engine": "google_flights",
    "departure_id": source,
    "arrival_id": destination,
    "outbound_date": str(departure_date),
    "return_date": str(return_date),
    "currency": "INR",
    "hl": "en",
    "api_key": SERPAPI_KEY
}

if st.button("Generate Travel Plan"):
    with st.spinner("Fetching best flight options..."):
        flight_data = fetch_flights(source, destination, departure_date, return_date)
        cheapest_flights = extract_cheapest_flights(flight_data)

    with st.spinner("Researching best attractions & activities..."):
        research_prompt = (
            f"Research the best attractions and activities in {destination} for a {num_days}-day {travel_theme.lower()} trip. "
            f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. "
            f"Hotel Rating: {hotel_rating}. Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}."
        )
        research_results = researcher.run(research_prompt, stream=False)

    with st.spinner("Searching for hotels & restaurants..."):
        hotel_restaurant_prompt = (
            f"Find the best hotels and restaurants near popular attractions in {destination} for a {travel_theme.lower()} trip. "
            f"Budget: {budget}. Hotel Rating: {hotel_rating}. Preferred activities: {activity_preferences}."
        )
        hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)

    with st.spinner("Creating your personalized itinerary..."):
        planning_prompt = (
            f"Based on the following data, create a {num_days}-day itinerary for a {travel_theme.lower()} trip to {destination}. "
            f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. Hotel Rating: {hotel_rating}. "
            f"Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}. Research: {research_results.content}. "
            f"Flights: {json.dumps(cheapest_flights)}. Hotels & Restaurants: {hotel_restaurant_results.content}."
        )
        itinerary = planner.run(planning_prompt, stream=False)

    st.subheader("Cheapest Flight Options")
    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
                airline_logo = flight.get("airline_logo", "")
                airline_name = flight.get("airline", "Unknown Airline")
                price = flight.get("price", "Not Available")
                total_duration = flight.get("total_duration", "N/A")
                
                flights_info = flight.get("flights", [{}])
                departure = flights_info[0].get("departure_airport", {})
                arrival = flights_info[-1].get("arrival_airport", {})
                airline_name = flights_info[0].get("airline", "Unknown Airline") 
                
                departure_time = format_datetime(departure.get("time", "N/A"))
                arrival_time = format_datetime(arrival.get("time", "N/A"))
                
                departure_token = flight.get("departure_token", "")

                booking_link = "#"
                if departure_token:
                    params_with_token = {
                        **params,
                        "departure_token": departure_token
                    }
                    search_with_token = fetch_flights(source, destination, departure_date, return_date)
                    try:
                        booking_options = search_with_token['best_flights'][idx]['booking_token']
                        booking_link = f"https://www.google.com/travel/flights?tfs={booking_options}"
                    except Exception:
                        booking_link = "#"

                st.markdown(
                    f"""
                    <div class="simple-card">
                        <img src="{airline_logo}" width="80" alt="Flight Logo" />
                        <h4 style="margin: 8px 0; color:#2c3e50;">{airline_name}</h4>
                        <p><strong>Departure:</strong> {departure_time}</p>
                        <p><strong>Arrival:</strong> {arrival_time}</p>
                        <p><strong>Duration:</strong> {total_duration} min</p>
                        <h3 style="color: #2980b9;">{price}</h3>
                        <a href="{booking_link}" target="_blank" class="simple-btn">Book Now</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("No flight data available.")

    st.subheader("Hotels & Restaurants")
    st.write(hotel_restaurant_results.content)

    st.subheader("Your Personalized Itinerary")
    st.write(itinerary.content)

    st.success("Travel plan generated successfully!")