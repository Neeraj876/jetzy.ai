from mcp.server.fastmcp import FastMCP
from typing import List, Dict
import random
import datetime

mcp = FastMCP("My Server")

@mcp.tool()
def search_flights(from_location: str, to_location: str, date_range: str) -> List[Dict]:
    """
    Simulates searching for available flights between two locations within a given date range.

    Args:
        from_location (str): The departure city or airport.
        to_location (str): The destination city or airport.
        date_range (str): The travel date range in a format like "2025-05-01 to 2025-05-07".

    Returns:
        list: A list of dictionaries where each dictionary represents a flight option, 
              including airline, price, departure, and arrival times.
    """
    airlines = ["Delta", "United", "Air France", "Qatar Airways", "Lufthansa"]
    airport_codes = {
        "New York": "JFK",
        "Paris": "CDG",
        "London": "LHR",
        "Rome": "FCO",
        "Greece": "ATH",
        "Tokyo": "HND",
        "Dubai": "DXB"
    }

    try:
        start_str, end_str = date_range.split("to")
        start_date = datetime.datetime.strptime(start_str.strip(), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_str.strip(), "%Y-%m-%d")
    except ValueError:
        return [{"error": "Invalid date range format. Use 'YYYY-MM-DD to YYYY-MM-DD'."}]

    if start_date >= end_date:
        return [{"error": "Start date must be before end date."}]

    results = []
    for _ in range(3):
        airline = random.choice(airlines)
        price = round(random.uniform(300, 1000), 2)

        departure = start_date + datetime.timedelta(days=random.randint(0, (end_date - start_date).days))
        return_date = departure + datetime.timedelta(days=random.randint(5, 10))

        results.append({
            "airline": airline,
            "price_usd": price,
            "from": f"{from_location} ({airport_codes.get(from_location, 'XXX')})",
            "to": f"{to_location} ({airport_codes.get(to_location, 'XXX')})",
            "departure_date": departure.strftime("%Y-%m-%d"),
            "return_date": return_date.strftime("%Y-%m-%d"),
            "mock_booking_link": f"https://mockflights.com/book/{airline.lower().replace(' ', '')}"
        })

    return results

@mcp.tool()
def recommend_hotels(location: str, budget: str = "medium") -> list[dict]:
    """
    Provides a simulated list of hotel recommendations based on the location and budget.

    Args:
        location (str): The city or region where the user wants to stay.
        budget (str): The budget category, such as "low", "medium", or "high".

    Returns:
        list: A list of dictionaries where each dictionary contains hotel name, 
              location, price per night, rating, and a mock booking link.
    """
    hotel_data = {
        "low": [("Budget Inn", 50), ("City Hostel", 35)],
        "medium": [("Comfort Suites", 120), ("Holiday Hotel", 90)],
        "high": [("Grand Palace", 300), ("Luxury Stay", 450)]
    }

    hotels = hotel_data.get(budget.lower(), hotel_data["medium"])
    return [
        {
            "name": name,
            "location": location,
            "price_per_night_usd": price,
            "rating": round(random.uniform(3.5, 5.0), 1),
            "mock_booking_link": f"https://mockhotels.com/book/{name.lower().replace(' ', '')}"
        }
        for name, price in hotels
    ]

@mcp.tool()
def recommend_attractions(location: str) -> list[dict]:
    """
    Returns a list of tourist attractions for a given location.

    Args:
        location (str): The name of the city or country to explore.

    Returns:
        list: A list of dictionaries where each dictionary includes the attraction name, 
              its location, and a short description.
    """
    sample_attractions = {
        "Paris": ["Eiffel Tower", "Louvre Museum", "Seine River Cruise"],
        "New York": ["Statue of Liberty", "Central Park", "Broadway Shows"],
        "Rome": ["Colosseum", "Trevi Fountain", "Vatican Museums"]
    }

    return [
        {
            "name": attraction,
            "location": location,
            "description": f"{attraction} is a must-see attraction in {location}."
        }
        for attraction in sample_attractions.get(location, ["Main Square", "Local Market", "City Museum"])
    ]

@mcp.tool()
def recommend_restaurants(location: str, cuisine: str = "any") -> list[dict]:
    """
    Suggests local restaurants based on location and optionally preferred cuisine.

    Args:
        location (str): The city or region to search restaurants in.
        cuisine (str): The preferred type of cuisine, e.g., "italian", "japanese", or "any".

    Returns:
        list: A list of dictionaries where each dictionary contains restaurant name, 
              location, cuisine type, and a simulated rating.
    """
    cuisines = {
        "any": ["The Local Bite", "Food Corner", "Taste Hub"],
        "italian": ["Pasta House", "Trattoria Roma", "Mama's Kitchen"],
        "japanese": ["Sushi Zen", "Tokyo Bowl", "Ninja Ramen"]
    }

    restaurant_names = cuisines.get(cuisine.lower(), cuisines["any"])
    return [
        {
            "name": name,
            "location": location,
            "cuisine": cuisine,
            "rating": round(random.uniform(3.5, 5.0), 1)
        }
        for name in restaurant_names
    ]

@mcp.tool()
def transport_options(from_location: str, to_location: str) -> dict:
    """
    Simulates available transport options between two locations including price and duration.

    Args:
        from_location (str): The origin city or place.
        to_location (str): The destination city or place.

    Returns:
        dict: A dictionary with keys like "bus", "train", "flight", and "car", 
              each containing a nested dictionary with duration and price in USD.
    """
    return {
        "bus": {
            "route": f"{from_location} to {to_location}",
            "duration": "10h",
            "price_usd": 45
        },
        "train": {
            "route": f"{from_location} to {to_location}",
            "duration": "6h",
            "price_usd": 75
        },
        "flight": {
            "route": f"{from_location} to {to_location}",
            "duration": "1h 30m",
            "price_usd": 150
        },
        "car": {
            "route": f"{from_location} to {to_location}",
            "duration": "8h",
            "price_usd": 90
        }
    }

@mcp.tool()
def seasonal_travel_advice(destination: str) -> str:
    """
    Provides general travel advice based on the season for a given destination.

    Args:
        destination (str): The name of the travel destination (city or country).

    Returns:
        str: A brief travel tip describing the ideal time to visit the destination.
    """
    seasons = {
        "Greece": "Best time to visit Greece is between April and June or September and October.",
        "Japan": "Visit Japan in March-April for cherry blossoms or November for fall colors.",
        "Thailand": "Dry season from November to February is ideal for travel."
    }

    return seasons.get(destination, f"Visit {destination} in its dry or festival season for the best experience.")


if __name__ == "__main__":
    mcp.run(transport="stdio")