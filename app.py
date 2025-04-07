import streamlit as st
import os
from dotenv import load_dotenv
from services.openai_service import OpenAIService
from mcp.context_manager import ContextManager

# Load environment variables
load_dotenv()

# Initialize services
context_manager = ContextManager()
openai_service = OpenAIService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=1000,
    top_p=0.9,
    frequency_penalty=0.2,
    presence_penalty=0.3
)

# Set page config
st.set_page_config(
    page_title="Jetzy Travel AI ChatBot",
    page_icon="✈️",
    layout="centered"  
)

# App title
st.title("✈️ Jetzy Travel AI")
st.markdown("Your intelligent travel assistant. Ask about flights, hotels, attractions, and more!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # Add system greeting
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hello! I'm your Jetzy Travel AI assistant. How can I help with your travel plans today?"
    })

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask me about your travel plans..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get user context (location, preferences, etc.)
    user_context = context_manager.get_user_context()
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        # Get response from OpenAI with context
        response = openai_service.get_response(
            messages=st.session_state.messages,
            context=user_context
        )
        
        # Extract and update context from response
        context_manager.update_context(response)
        
        # Display the response
        message_placeholder.markdown(response["content"])
    
    # Add assistant response to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response["content"]
    })
    
# Sidebar for user preferences
with st.sidebar:
    st.header("Travel Preferences")
    st.text_input("Home Airport", key="home_airport", placeholder="e.g., JFK")
    st.multiselect(
        "Preferred Airlines", 
        options=["Any", "American Airlines", "Delta", "United", "JetBlue", "Southwest"],
        default=["Any"]
    )
    st.select_slider(
        "Budget Level",
        options=["Budget", "Moderate", "Luxury"],
        value="Moderate"
    )
    st.multiselect(
        "Travel Interests", 
        options=["Beaches", "Mountains", "Cities", "Cultural", "Food", "Adventure", "Relaxation"],
        default=[]
    )
    
    # Update context when preferences change
    context_manager.set_preferences({
    "home_airport": st.session_state.get("home_airport", ""),
    "preferred_airlines": st.session_state.get("preferred_airlines", ["Any"]),
    "budget_level": st.session_state.get("budget_level", "Moderate"),
    "travel_interests": st.session_state.get("travel_interests", [])
})
    
    # Clear chat history
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.experimental_rerun()