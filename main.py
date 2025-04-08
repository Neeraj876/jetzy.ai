import os
import json
import sys
import streamlit as st
# sys.path.append(os.path.abspath("..")) 
from mcp_client import run_async

# Set page configuration
st.set_page_config(
    page_title="Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Streamlit UI
st.title("✈️ Travel Planner")
st.markdown("Plan your perfect vacation with our travel assistant.")

# Create tabs for different travel planning functions
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Flight Search", "Hotels", "Attractions", "Restaurants", "Transportation"])

with tab1:
    st.header("Search for Flights")
    col1, col2 = st.columns(2)
    
    with col1:
        from_location = st.text_input("From", "New York")
        date_range = st.text_input("Date Range (YYYY-MM-DD to YYYY-MM-DD)", "2025-05-01 to 2025-05-15")
    
    with col2:
        to_location = st.text_input("To", "Paris")
    
    if st.button("Search Flights"):
        with st.spinner("Searching for flights..."):
            query = f"Find flights from {from_location} to {to_location} for dates {date_range}"
            result = run_async(query)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
                st.write(result.get("response", ""))
            else:
                st.success("Flights found!")
                try:
                    flights = json.loads(result["result"])
                    for i, flight in enumerate(flights):
                        with st.expander(f"Flight {i+1}: {flight['airline']} - ${flight['price_usd']}"):
                            st.write(f"**From:** {flight['from']}")
                            st.write(f"**To:** {flight['to']}")
                            st.write(f"**Departure:** {flight['departure_date']}")
                            st.write(f"**Return:** {flight['return_date']}")
                            st.markdown(f"[Book Now]({flight['mock_booking_link']})")
                except:
                    st.write(result["result"])

with tab2:
    st.header("Find Hotels")
    hotel_location = st.text_input("City", "Paris", key="hotel_city")
    budget_options = st.radio("Budget", ["low", "medium", "high"], horizontal=True)
    
    if st.button("Find Hotels"):
        with st.spinner("Searching for hotels..."):
            query = f"Recommend hotels in {hotel_location} with a {budget_options} budget"
            result = run_async(query)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
                st.write(result.get("response", ""))
            else:
                st.success("Hotels found!")
                try:
                    hotels = json.loads(result["result"])
                    for hotel in hotels:
                        with st.expander(f"{hotel['name']} - ${hotel['price_per_night_usd']}/night"):
                            st.write(f"**Location:** {hotel['location']}")
                            st.write(f"**Rating:** {hotel['rating']}⭐")
                            st.markdown(f"[Book Now]({hotel['mock_booking_link']})")
                except:
                    st.write(result["result"])

with tab3:
    st.header("Discover Attractions")
    attraction_location = st.text_input("City", "Rome", key="attraction_city")
    
    if st.button("Find Attractions"):
        with st.spinner("Finding attractions..."):
            query = f"Recommend attractions in {attraction_location}"
            result = run_async(query)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
                st.write(result.get("response", ""))
            else:
                st.success("Attractions found!")
                try:
                    attractions = json.loads(result["result"])
                    for attraction in attractions:
                        with st.expander(f"{attraction['name']}"):
                            st.write(f"**Location:** {attraction['location']}")
                            st.write(f"**Description:** {attraction['description']}")
                except:
                    st.write(result["result"])

with tab4:
    st.header("Find Restaurants")
    col1, col2 = st.columns(2)
    
    with col1:
        restaurant_location = st.text_input("City", "Paris", key="restaurant_city")
    
    with col2:
        cuisine_type = st.selectbox("Cuisine", ["any", "italian", "japanese", "french", "american", "chinese"])
    
    if st.button("Search Restaurants"):
        with st.spinner("Finding restaurants..."):
            query = f"Recommend {cuisine_type} restaurants in {restaurant_location}"
            result = run_async(query)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
                st.write(result.get("response", ""))
            else:
                st.success("Restaurants found!")
                try:
                    restaurants = json.loads(result["result"])
                    for restaurant in restaurants:
                        with st.expander(f"{restaurant['name']} - {restaurant['rating']}⭐"):
                            st.write(f"**Location:** {restaurant['location']}")
                            st.write(f"**Cuisine:** {restaurant['cuisine']}")
                except:
                    st.write(result["result"])

with tab5:
    st.header("Transportation Options")
    col1, col2 = st.columns(2)
    
    with col1:
        transport_from = st.text_input("From", "Rome", key="transport_from")
    
    with col2:
        transport_to = st.text_input("To", "Florence", key="transport_to")
    
    if st.button("Find Transport Options"):
        with st.spinner("Finding transportation options..."):
            query = f"Show transport options from {transport_from} to {transport_to}"
            result = run_async(query)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
                st.write(result.get("response", ""))
            else:
                st.success("Transportation options found!")
                try:
                    options = json.loads(result["result"])
                    for mode, details in options.items():
                        st.write(f"**{mode.capitalize()}:** Duration: {details['duration']}, Price: ${details['price_usd']}")
                except:
                    st.write(result["result"])

# Side panel for travel advice
with st.sidebar:
    st.header("Travel Advice")
    destination = st.text_input("Where are you planning to visit?", "Greece")
    
    if st.button("Get Seasonal Advice"):
        with st.spinner("Getting travel advice..."):
            query = f"What is the seasonal travel advice for {destination}?"
            result = run_async(query)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.info(result["result"])
    
    # Add some general travel tips
    st.subheader("Travel Tips")
    tips = [
        "Remember to check visa requirements before traveling",
        "Get travel insurance for peace of mind",
        "Make copies of important documents",
        "Check COVID-19 restrictions and requirements"
    ]
    for tip in tips:
        st.markdown(f"• {tip}")

# Footer
st.markdown("---")
st.caption("Travel Planner App - Plan your perfect vacation with AI assistance")

if __name__ == "__main__":
    pass