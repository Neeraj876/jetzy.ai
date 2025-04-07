mock_destinations = {
    "paris": {
        "summary": "Paris is known for its cafes, art, and the iconic Eiffel Tower.",
        "top_attractions": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral"],
        "best_time_to_visit": "April to June and October to early November",
    },
    "tokyo": {
        "summary": "Tokyo blends futuristic technology with traditional culture.",
        "top_attractions": ["Shibuya Crossing", "Meiji Shrine", "Tokyo Skytree"],
        "best_time_to_visit": "March to May and October to November",
    },
    "bali": {
        "summary": "Bali offers beaches, temples, and natural beauty.",
        "top_attractions": ["Uluwatu Temple", "Tegallalang Rice Terraces", "Seminyak Beach"],
        "best_time_to_visit": "April to October",
    }
}


def get_mock_travel_info(destination_name: str) -> dict:
    """
    Retrieve mock travel info for a given destination.
    """
    key = destination_name.lower()
    return mock_destinations.get(key, {
        "summary": "Sorry, I don't have data for that destination yet.",
        "top_attractions": [],
        "best_time_to_visit": "Unknown"
    })
