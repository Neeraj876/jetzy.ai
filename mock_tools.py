from typing import Dict, Any, List

def get_available_tools() -> List[Dict[str, Any]]:
    """
    Return the list of tools/functions available for the OpenAI function calling API.
    These tools align with Jetzy Travel AI features from the PRD.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "search_flights",
                "description": "Search for flights based on origin, destination, dates, and preferences",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Origin city or airport code"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination city or airport code"
                        },
                        "departure_date": {
                            "type": "string",
                            "description": "Departure date in YYYY-MM-DD format"
                        },
                        "return_date": {
                            "type": "string",
                            "description": "Return date in YYYY-MM-DD format (optional for one-way)"
                        },
                        "passengers": {
                            "type": "integer",
                            "description": "Number of passengers"
                        },
                        "preferred_airlines": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of preferred airlines (optional)"
                        }
                    },
                    "required": ["origin", "destination", "departure_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_hotels",
                "description": "Search for hotels based on location, dates, and preferences",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City or area to search for hotels"
                        },
                        "check_in_date": {
                            "type": "string",
                            "description": "Check-in date in YYYY-MM-DD format"
                        },
                        "check_out_date": {
                            "type": "string",
                            "description": "Check-out date in YYYY-MM-DD format"
                        },
                        "guests": {
                            "type": "integer",
                            "description": "Number of guests"
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price per night"
                        },
                        "amenities": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of desired amenities"
                        }
                    },
                    "required": ["location", "check_in_date", "check_out_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "find_attractions",
                "description": "Find tourist attractions and activities in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City or area to search for attractions"
                        },
                        "categories": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["museums", "parks", "historical", "entertainment", "shopping"]
                            },
                            "description": "Categories of attractions to find"
                        },
                        "radius": {
                            "type": "number",
                            "description": "Search radius in kilometers"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "find_restaurants",
                "description": "Find restaurants and dining options in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City or area to search for restaurants"
                        },
                        "cuisine": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Types of cuisine"
                        },
                        "price_level": {
                            "type": "string",
                            "enum": ["$", "$$", "$$$", "$$$$"],
                            "description": "Price level"
                        },
                        "open_now": {
                            "type": "boolean",
                            "description": "Whether the restaurant should be open now"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_transport_options",
                "description": "Get transportation options between two locations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Ending location"
                        },
                        "transport_type": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["train", "bus", "car", "plane", "ferry"]
                            },
                            "description": "Types of transportation to include"
                        }
                    },
                    "required": ["origin", "destination"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_seasonal_advice",
                "description": "Get seasonal travel advice for a destination",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination": {
                            "type": "string",
                            "description": "Destination to get seasonal advice for"
                        },
                        "month": {
                            "type": "string",
                            "description": "Month to get advice for (optional)"
                        }
                    },
                    "required": ["destination"]
                }
            }
        }
    ]

def execute_tool_call(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool call and return mock results.
    In a production environment, this would call actual APIs.
    
    Args:
        function_name: The name of the function to call
        arguments: The arguments for the function
        
    Returns:
        Mock results for the function call
    """
    # Mock data handlers
    mock_handlers = {
        "search_flights": _mock_search_flights,
        "search_hotels": _mock_search_hotels,
        "find_attractions": _mock_find_attractions,
        "find_restaurants": _mock_find_restaurants,
        "get_transport_options": _mock_get_transport_options,
        "get_seasonal_advice": _mock_get_seasonal_advice
    }
    
    # Call the appropriate mock handler
    if function_name in mock_handlers:
        return mock_handlers[function_name](arguments)
    else:
        return {"error": f"Function {function_name} not implemented"}

# Mock data implementation for each tool
def _mock_search_flights(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock flight search results"""
    origin = args.get("origin", "")
    destination = args.get("destination", "")
    
    # Sample flight data
    return {
        "flights": [
            {
                "airline": "United Airlines",
                "flight_number": "UA123",
                "departure": f"{origin} 08:30 AM",
                "arrival": f"{destination} 11:45 AM",
                "duration": "3h 15m",
                "price": 320.50,
                "stops": 0
            },
            {
                "airline": "American Airlines",
                "flight_number": "AA456",
                "departure": f"{origin} 10:15 AM",
                "arrival": f"{destination} 01:30 PM",
                "duration": "3h 15m",
                "price": 295.75,
                "stops": 0
            },
            {
                "airline": "Delta",
                "flight_number": "DL789",
                "departure": f"{origin} 02:45 PM",
                "arrival": f"{destination} 08:20 PM",
                "duration": "5h 35m",
                "price": 275.00,
                "stops": 1
            }
        ]
    }

def _mock_search_hotels(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock hotel search results"""
    location = args.get("location", "")
    max_price = args.get("max_price", 1000)
    
    # Sample hotel data
    return {
        "hotels": [
            {
                "name": f"Grand Hotel {location}",
                "rating": 4.7,
                "price_per_night": min(max_price, 250),
                "address": f"123 Main St, {location}",
                "amenities": ["Pool", "Spa", "Free WiFi", "Restaurant"]
            },
            {
                "name": f"{location} Plaza Hotel",
                "rating": 4.5,
                "price_per_night": min(max_price, 180),
                "address": f"456 Broadway, {location}",
                "amenities": ["Free WiFi", "Fitness Center", "Restaurant"]
            },
            {
                "name": f"Comfort Inn {location}",
                "rating": 4.2,
                "price_per_night": min(max_price, 120),
                "address": f"789 Oak Drive, {location}",
                "amenities": ["Free Breakfast", "Free WiFi", "Parking"]
            }
        ]
    }

def _mock_find_attractions(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock attraction search results"""
    location = args.get("location", "")
    
    # Sample attraction data
    attractions_by_location = {
        "New York": [
            {"name": "Times Square", "category": "entertainment", "rating": 4.6},
            {"name": "Central Park", "category": "parks", "rating": 4.8},
            {"name": "Metropolitan Museum of Art", "category": "museums", "rating": 4.9}
        ],
        "Paris": [
            {"name": "Eiffel Tower", "category": "historical", "rating": 4.8},
            {"name": "Louvre Museum", "category": "museums", "rating": 4.9},
            {"name": "Notre-Dame Cathedral", "category": "historical", "rating": 4.7}
        ],
        "Rome": [
            {"name": "Colosseum", "category": "historical", "rating": 4.8},
            {"name": "Vatican Museums", "category": "museums", "rating": 4.7},
            {"name": "Trevi Fountain", "category": "historical", "rating": 4.8}
        ]
    }
    
    # Return default attractions if location not in our mock data
    default_attractions = [
        {"name": f"{location} Museum", "category": "museums", "rating": 4.5},
        {"name": f"{location} Park", "category": "parks", "rating": 4.6},
        {"name": f"Historic {location} Center", "category": "historical", "rating": 4.7}
    ]
    
    return {
        "attractions": attractions_by_location.get(location, default_attractions)
    }

def _mock_find_restaurants(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock restaurant search results"""
    location = args.get("location", "")
    
    # Sample restaurant data
    return {
        "restaurants": [
            {
                "name": f"The {location} Grill",
                "cuisine": "American",
                "price_level": "$$",
                "rating": 4.6,
                "address": f"123 Main St, {location}"
            },
            {
                "name": f"Pasta Palace {location}",
                "cuisine": "Italian",
                "price_level": "$$",
                "rating": 4.4,
                "address": f"456 Olive St, {location}"
            },
            {
                "name": f"{location} Sushi",
                "cuisine": "Japanese",
                "price_level": "$$$",
                "rating": 4.7,
                "address": f"789 Ocean Ave, {location}"
            }
        ]
    }

def _mock_get_transport_options(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock transportation options"""
    origin = args.get("origin", "")
    destination = args.get("destination", "")
    
    # Sample transport data
    return {
        "options": [
            {
                "type": "train",
                "duration": "3h 30m",
                "cost": 75.00,
                "departure_times": ["08:00", "10:30", "13:00", "15:30"]
            },
            {
                "type": "bus",
                "duration": "4h 15m",
                "cost": 35.00,
                "departure_times": ["07:30", "09:00", "12:00", "16:00"]
            },
            {
                "type": "plane",
                "duration": "1h 15m",
                "cost": 150.00,
                "departure_times": ["08:45", "12:30", "17:15"]
            }
        ]
    }

def _mock_get_seasonal_advice(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock seasonal travel advice"""
    destination = args.get("destination", "")
    month = args.get("month", "")
    
    # Sample seasonal advice
    seasonal_data = {
        "Egypt": {
            "best_time": "October to April",
            "avoid_time": "June to August (very hot)",
            "peak_season": "December to January",
            "events": ["Abu Simbel Sun Festival (February & October)"]
        },
        "Greece": {
            "best_time": "April to June, September to October",
            "avoid_time": "July to August (crowded and hot)",
            "peak_season": "July to August",
            "events": ["Greek Orthodox Easter (varies)", "Athens Festival (June to September)"]
        },
        "Italy": {
            "best_time": "April to June, September to October",
            "avoid_time": "August (many businesses closed)",
            "peak_season": "June to July",
            "events": ["Venice Carnival (February)", "Palio di Siena (July & August)"]
        }
    }
    
    # Return default seasonal advice if destination not in our mock data
    default_data = {
        "best_time": "Spring and Fall",
        "avoid_time": "Peak summer season",
        "peak_season": "Summer months",
        "events": [f"{destination} Annual Festival"]
    }
    
    return seasonal_data.get(destination, default_data)