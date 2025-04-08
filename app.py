import streamlit as st
import os
from dotenv import load_dotenv

# Import from our modules
from context_manager import ContextManager
from openai_mcp import OpenAIClient, JetzyTravelAssistant

def main():
    # Load environment variables
    load_dotenv()
    
    st.set_page_config(page_title="Jetzy Travel AI", page_icon="✈️")
    st.title("Jetzy Travel AI Assistant")
    
    # Initialize session state for conversation history
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    # Initialize the assistant
    if "assistant" not in st.session_state:
        # Try to get API key from environment or secrets
        # Change this line:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            st.error("OpenAI API key not found. Please set it  as an environment variable.")
            st.stop()
        
        st.session_state.assistant = JetzyTravelAssistant(api_key)
    
    # Chat container
    chat_container = st.container()
    
    # Clear conversation button and user preferences
    with st.sidebar:
        st.subheader("Settings")
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            st.session_state.assistant.clear_conversation()
            st.rerun()
        
        st.divider()
        
        # User preferences section
        st.subheader("Your Preferences")
        
        # Current location
        location = st.text_input("Your current location", key="user_location")
        if st.button("Update Location"):
            st.session_state.assistant.context_manager.set_location(location)
            st.success(f"Location updated to {location}")
        
        # Travel preferences
        st.subheader("Travel Preferences")
        
        home_airport = st.text_input("Home Airport", placeholder="e.g., JFK, LAX")
        
        travel_interests = st.multiselect(
            "Travel Interests",
            options=["Beach", "Mountains", "Culture", "Food", "Adventure", "Relaxation", "Shopping", "Nightlife"],
            default=[]
        )
        
        budget_level = st.select_slider(
            "Budget Level",
            options=["Budget", "Moderate", "Luxury"],
            value="Moderate"
        )
        
        if st.button("Update Preferences"):
            preferences = {
                "home_airport": home_airport,
                "travel_interests": travel_interests,
                "budget_level": budget_level
            }
            st.session_state.assistant.context_manager.set_preferences(preferences)
            st.success("Preferences updated!")
    
    # Display conversation history
    with chat_container:
        if not st.session_state.conversation_history:
            st.info("👋 Hello! I'm your Jetzy Travel Assistant. Ask me about destinations, flights, hotels, or any travel advice you need!")
        
        for msg in st.session_state.conversation_history:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])
    
    # User input
    user_message = st.chat_input("Ask me about travel...")
    
    # Handle user message
    if user_message:
        # Add user message to conversation history
        st.session_state.conversation_history.append({"role": "user", "content": user_message})
        
        # Process the message and get response
        try:
            with st.spinner("Thinking..."):
                response = st.session_state.assistant.process_user_message(user_message)
                # Add assistant response to conversation history
                st.session_state.conversation_history.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Error processing your request: {str(e)}")
        
        # Force a rerun to update the UI
        st.rerun()

if __name__ == "__main__":
    main()