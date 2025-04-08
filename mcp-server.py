from mcp.server.fastmcp import FastMCP
from typing import List, Dict
import random
import datetime

mcp = FastMCP("My Server")

@mcp.tool()
def search_flights(from_location: str, to_location: str, date_range: str) -> List[Dict]:
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
def recommend_hotels(location: str, budget: str = "medium") -> list:
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
def recommend_attractions(location: str) -> list:
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
def recommend_restaurants(location: str, cuisine: str = "any") -> list:
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
    return {
        "bus": {
            "duration": "10h",
            "price_usd": 45
        },
        "train": {
            "duration": "6h",
            "price_usd": 75
        },
        "flight": {
            "duration": "1h 30m",
            "price_usd": 150
        },
        "car": {
            "duration": "8h",
            "price_usd": 90
        }
    }

@mcp.tool()
def seasonal_travel_advice(destination: str) -> str:
    seasons = {
        "Greece": "Best time to visit Greece is between April and June or September and October.",
        "Japan": "Visit Japan in March-April for cherry blossoms or November for fall colors.",
        "Thailand": "Dry season from November to February is ideal for travel."
    }

    return seasons.get(destination, f"Visit {destination} in its dry or festival season for the best experience.")


if __name__ == "__main__":
    mcp.run(transport="stdio")