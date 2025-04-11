import streamlit as st
from typing import Dict, Any, List, Optional, Set
import datetime
import json
import re

class ContextManager:
    def __init__(self):
        """
        Initialize the context manager for tracking user preferences and conversation context.
        Uses Streamlit's session_state for persistence during the session.
        """
        # Initialize context in session state if it doesn't exist
        if "user_context" not in st.session_state:
            st.session_state.user_context = {
                "location": None,  # User's current location
                "preferences": {},  # User preferences
                "recent_searches": [],  # Recent search history
                "mentioned_destinations": set(),  # Destinations mentioned in conversation
                "current_trip": {  
                    # Information about currently discussed trip
                    "origin": None,
                    "destination": None,
                    "date_range": None,
                    "budget": None
                },
                "last_updated": datetime.datetime.now().isoformat()
            }
    
    def get_user_context(self) -> Dict[str, Any]:
        """
        Get the current user context
        """
        return st.session_state.user_context
    
    def set_location(self, location: str) -> None:
        """
        Set the user's current location
        """
        st.session_state.user_context["location"] = location
        self._update_timestamp()
    
    def set_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Update user preferences
        """
        # Only update non-empty values
        for key, value in preferences.items():
            if value:  
                st.session_state.user_context["preferences"][key] = value
        
        self._update_timestamp()
    
    def add_search(self, search_query: str) -> None:
        """
        Add a search query to recent searches
        """
        # Keep only unique and non-empty searches

        if search_query and search_query.strip():

            # Remove existing duplicate
            if search_query in st.session_state.user_context["recent_searches"]:
                st.session_state.user_context["recent_searches"].remove(search_query)

            # Add to the beginning of the list
            st.session_state.user_context["recent_searches"].insert(0, search_query)
            # Keep only the 5 most recent searches
            st.session_state.user_context["recent_searches"] = st.session_state.user_context["recent_searches"][:10]
        
        self._update_timestamp()
    
    def add_mentioned_destination(self, destination: str) -> None:
        """
        Add a destination mentioned in the conversation
        """
        if destination:
            st.session_state.user_context["mentioned_destinations"].add(destination)
        
        self._update_timestamp()
    
    def update_current_trip(self, origin=None, destination=None, date_range=None, budget=None) -> None:
        """
        Update information about the current trip being discussed
        """
        current_trip = st.session_state.user_context["current_trip"]
        
        if origin:
            current_trip["origin"] = origin
        if destination:
            current_trip["destination"] = destination
            # Also add to mentioned destinations
            self.add_mentioned_destination(destination)
        if date_range:
            current_trip["date_range"] = date_range
        if budget:
            current_trip["budget"] = budget
        
        self._update_timestamp()
    
    def clear_context(self) -> None:
        """
        Clear the user context
        """
        st.session_state.user_context = {
            "location": None,
            "preferences": {},
            "recent_searches": [],
            "mentioned_destinations": set(),
            "current_trip": {
                "origin": None,
                "destination": None,
                "date_range": None,
                "budget": None
            },
            "last_updated": datetime.datetime.now().isoformat()
        }
    
    def extract_destinations(self, text: str) -> List[str]:
        """
        Extract potential destination names from text
        """
        common_destinations = [
            "New York", "Paris", "London", "Rome", "Tokyo", "Dubai", "Bangkok",
            "Greece", "Italy", "France", "Egypt", "Spain", "Japan", "Thailand",
            "Berlin", "Amsterdam", "Vienna", "Venice", "Milan", "Barcelona",
            "Hong Kong", "Singapore", "Sydney", "Cairo", "Istanbul", "Athens"
        ]

        # Add common destination aliases
        destination_aliases = {
            "NYC": "New York",
            "LA": "Los Angeles",
            "SF": "San Francisco",
            "Vegas": "Las Vegas",
            "UK": "United Kingdom",
            "US": "United States",
            "USA": "United States"
        }
        
        found_destinations = []

        for destination in common_destinations:
            # Look for the destination as a whole word
            if re.search(r'\b' + re.escape(destination) + r'\b', text, re.IGNORECASE):
                found_destinations.append(destination)

        # Check for aliases
        for alias, full_name in destination_aliases.items():
            if re.search(r'\b' + re.escape(alias) + r'\b', text, re.IGNORECASE):
                found_destinations.append(full_name)
        
        return list(dict.fromkeys(found_destinations))
    
    def extract_date_ranges(self, text: str) -> List[str]:
        """
        Extract date ranges from text using regex patterns
        """
        date_ranges = []
    
        # Standard format: YYYY-MM-DD to YYYY-MM-DD
        standard_format = re.findall(r'\d{4}-\d{2}-\d{2}\s+to\s+\d{4}-\d{2}-\d{2}', text)
        date_ranges.extend(standard_format)
        
        # Month year format: May 2025
        month_year_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
        month_year_matches = re.findall(month_year_pattern, text, re.IGNORECASE)
        date_ranges.extend(month_year_matches)
        
        # Date with ordinals: 21st May, 3rd June, etc.
        ordinal_date = r'\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?'
        ordinal_matches = re.findall(ordinal_date, text, re.IGNORECASE)
        
        # Convert dates into standard format where possible
        for date_str in ordinal_matches:
            date_ranges.append(date_str)
        
        # Look for "next week", "next month", etc.
        relative_dates = {
            r'\bnext\s+week\b': 'within a week',
            r'\bnext\s+month\b': 'within a month', 
            r'\bin\s+\d+\s+days\b': 'upcoming days',
            r'\bin\s+\d+\s+weeks\b': 'upcoming weeks'
        }
        
        for pattern, replacement in relative_dates.items():
            if re.search(pattern, text, re.IGNORECASE):
                date_ranges.append(replacement)
                
        return date_ranges
    
    def extract_budget(self, text: str) -> Optional[str]:
        """
        Extract budget information from text
        """
        budget_terms = {
            "low": ["low", "budget", "cheap", "inexpensive", "affordable"],
            "medium": ["medium", "moderate", "standard", "average"],
            "high": ["high", "luxury", "expensive", "premium", "upscale"]
        }
        
        for budget_level, terms in budget_terms.items():
            for term in terms:
                if re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE):
                    return budget_level
        
        return None
    
    def update_context_from_text(self, text: str) -> None:
            """
            Update context by extracting information from text
            """
            # Extract destinations
            destinations = self.extract_destinations(text)
            for dest in destinations:
                self.add_mentioned_destination(dest)
            
            # Try to determine if any are origin or destination for current trip
            if len(destinations) >= 2:
                
                # Look for patterns like "from X to Y" or "X to Y"
                from_to_pattern = re.search(r'from\s+([A-Za-z\s]+)\s+to\s+([A-Za-z\s]+)', text, re.IGNORECASE)

                # Extracts origin and destination cities using a regex pattern 
                if from_to_pattern:
                    origin_text = from_to_pattern.group(1).strip()
                    dest_text = from_to_pattern.group(2).strip()
                    
                    # Match with extracted destinations
                    origin = next((d for d in destinations if d.lower() in origin_text.lower()), None)
                    destination = next((d for d in destinations if d.lower() in dest_text.lower()), None)
                    
                    if origin and destination:
                        self.update_current_trip(origin=origin, destination=destination)
                        
            # NEW: Handle just destination scenario with "to X" pattern without "from"
            elif len(destinations) == 1:

                # Look for the pattern "to X"
                to_pattern = re.search(r'(?:to|in|for)\s+([A-Za-z\s]+)', text, re.IGNORECASE)

                # Extracts destination city using a regex pattern 
                if to_pattern:
                    dest_text = to_pattern.group(1).strip()

                    # Match with extracted destination
                    destination = next((d for d in destinations if d.lower() in dest_text.lower()), None)

                    if destination:
                        # Set as destination in current trip
                        self.update_current_trip(destination=destination)
                        
                        # If location is set and no origin, use location as default origin
                        if self.get_user_context()["location"] and not self.get_user_context()["current_trip"]["origin"]:
                            self.update_current_trip(origin=self.get_user_context()["location"])
            
            # Extract date ranges
            date_ranges = self.extract_date_ranges(text)
            if date_ranges:
                self.update_current_trip(date_range=date_ranges[0])
            
            # Extract budget
            budget = self.extract_budget(text)
            if budget:
                self.update_current_trip(budget=budget)

    def update_context(self, message: Dict[str, str]) -> None:
        """
        Update the context based on a message
        """
        content = message.get("content", "")
        
        # Update context based on text content (message)
        self.update_context_from_text(content)
        self._update_timestamp()
    
    def _update_timestamp(self) -> None:
        """
        Update the last_updated timestamp
        """
        st.session_state.user_context["last_updated"] = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Make the user context dictionary safe for JSON serialization. This is useful for saving, logging, sending to an API, or displaying in the UI.
        """
        try:
         
            context_dict = self.get_user_context().copy()

            # Convert sets to lists because sets are not JSON serializable
            if isinstance(context_dict.get("mentioned_destinations"), set):
                context_dict["mentioned_destinations"] = list(context_dict["mentioned_destinations"])
            
            # Ensure all values in the context are JSON serializable
            for key, value in list(context_dict.items()):
                try:
                    # Test if the value can be serialized to JSON
                    json.dumps({key: value})
                except (TypeError, OverflowError):
                    # If not, convert it to a string
                    context_dict[key] = str(value)
                    
            return context_dict
        except Exception as e:
            return {"error": "Context serialization failed", "last_updated": datetime.datetime.now().isoformat()}

    
    def from_dict(self, context_dict: Dict[str, Any]) -> None:
        """
        Load context from a dictionary
        """
        if "mentioned_destinations" in context_dict and isinstance(context_dict["mentioned_destinations"], list):
            context_dict["mentioned_destinations"] = set(context_dict["mentioned_destinations"])
        
        st.session_state.user_context = context_dict
        self._update_timestamp()