import streamlit as st
from typing import Dict, Any, List, Optional
import datetime
import json

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
            # Add to the beginning of the list
            st.session_state.user_context["recent_searches"].insert(0, search_query)
            # Keep only the 5 most recent searches
            st.session_state.user_context["recent_searches"] = st.session_state.user_context["recent_searches"][:5]
        
        self._update_timestamp()
    
    def add_mentioned_destination(self, destination: str) -> None:
        """
        Add a destination mentioned in the conversation
        """
        if destination:
            st.session_state.user_context["mentioned_destinations"].add(destination)
        
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
            "last_updated": datetime.datetime.now().isoformat()
        }
    
    def update_context(self, response: Dict[str, str]) -> None:
        """
        Update the context based on the assistant's response
        This extracts information from the response to update the context
        """
        content = response.get("content", "")
        
        # Example logic to extract destinations from the response
        # This is a simplified example - in a real implementation, you might use NLP
        potential_destinations = ["New York", "Rome", "Paris", "London", "Tokyo", 
                                 "Greece", "Italy", "France", "Egypt", "Milan"]
        
        for destination in potential_destinations:
            if destination.lower() in content.lower():
                self.add_mentioned_destination(destination)
        
        self._update_timestamp()
    
    def _update_timestamp(self) -> None:
        """
        Update the last_updated timestamp
        """
        st.session_state.user_context["last_updated"] = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary
        """
        context_dict = self.get_user_context().copy()
        # Convert set to list for serialization
        context_dict["mentioned_destinations"] = list(context_dict["mentioned_destinations"])
        return context_dict
    
    def from_dict(self, context_dict: Dict[str, Any]) -> None:
        """
        Load context from a dictionary
        """
        if "mentioned_destinations" in context_dict:
            context_dict["mentioned_destinations"] = set(context_dict["mentioned_destinations"])
        
        st.session_state.user_context = context_dict
        self._update_timestamp()