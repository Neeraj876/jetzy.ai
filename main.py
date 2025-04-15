import streamlit as st
from dotenv import load_dotenv
from mcp_client import run_async
from context_manager import ContextManager

# Load environment variables
load_dotenv()

# Set page configuration with wider layout
st.set_page_config(
    page_title="Jetzy",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #616161;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .chat-container {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .user-message {
        background-color: #2C3E50;
        padding: 12px 18px;
        border-radius: 15px 15px 0 15px;
        margin: 10px 0;
        display: inline-block;
        max-width: 90%;
        float: right;
        clear: both;
    }
    .assistant-message {
        background-color: #808080;
        padding: 12px 18px;
        border-radius: 15px 15px 15px 0;
        margin: 10px 0;
        display: inline-block;
        max-width: 90%;
        float: left;
        clear: both;
    }
    .suggestion-button {
        margin: 5px;
        padding: 5px 15px;
        border: 1px solid #1E88E5;
        border-radius: 20px;
        background-color: #808080;
        color: #1E88E5;
        cursor: pointer;
        transition: all 0.3s;
    }
    .suggestion-button:hover {
        background-color: #808080;
        color: white;
    }
    .stTextArea textarea {
        border-radius: 20px;
        border: 1px solid #BDBDBD;
        padding: 15px;
    }
    .stButton>button {
        border-radius: 20px;
        padding: 5px 25px;
        background-color: #1E88E5;
        color: white;
        font-weight: 600;
    }
    .feature-card {
        background-color: #808080;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        height: 100%;
    }
    .feature-icon {
        font-size: 1.8rem;
        color: #1E88E5;
        margin-bottom: 10px;
    }
    .divider {
        margin-top: 30px;
        margin-bottom: 20px;
        border-top: 1px solid #EEEEEE;
    }
    .footer {
        text-align: center;
        color: #9E9E9E;
        font-size: 0.8rem;
        padding: 20px 0;
    }
    .context-panel {
        background-color: #f0f8ff;
        border-radius: 10px;
        padding: 10px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize context manager
context_manager = ContextManager()

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'showing_welcome' not in st.session_state:
    st.session_state.showing_welcome = True

# Sidebar content
with st.sidebar:
    st.markdown("### How can I help you?")
    
    st.markdown("#### I can assist with:")
    features = {
        "✈️ Flight Search": "Find available flights between destinations",
        "🏨 Hotel Recommendations": "Get hotel suggestions based on location and budget",
        "🗿 Local Attractions": "Discover must-visit places at your destination",
        "🍽️ Restaurant Tips": "Find the best dining options",
        "🚌 Transport Options": "Compare ways to get around",
        "🌤️ Seasonal Advice": "Learn the best time to visit"
    }
    
    for feature, description in features.items():
        st.markdown(f"**{feature}**  \n{description}")
    
    st.markdown("---")
    
    # Display user context in the sidebar
    user_context = context_manager.get_user_context()
    with st.expander("Your Travel Context", expanded=False):
        if user_context["location"]:
            st.write(f"📍 Your location: {user_context['location']}")
        
        if user_context["preferences"]:
            st.write("🌟 Your preferences:")
            for key, value in user_context["preferences"].items():
                st.write(f"- {key}: {value}")
        
        if user_context["mentioned_destinations"]:
            st.write("🌍 Destinations discussed:")
            for dest in user_context["mentioned_destinations"]:
                st.write(f"- {dest}")
        
        if user_context["recent_searches"]:
            st.write("🔍 Recent searches:")
            for search in user_context["recent_searches"][:3]:
                st.write(f"- {search}")
        
        if st.button("Clear Travel Context"):
            context_manager.clear_context()
            st.session_state.chat_history = []
            # You might also want to reset the welcome message
            st.session_state.showing_welcome = True
            st.rerun()

    st.markdown("---")
    st.markdown("##### Sample Queries")
    
    # Example query buttons
    if st.button("Find flights from NYC to Paris in May 2025"):
        st.session_state.query_input = "Find flights from New York to Paris from 2025-05-01 to 2025-05-14"
        st.session_state.showing_welcome = False
    
    if st.button("Recommend hotels in Rome"):
        st.session_state.query_input = "What are some good hotels in Rome with a medium budget?"
        st.session_state.showing_welcome = False
    
    if st.button("What to do in Tokyo?"):
        st.session_state.query_input = "What are the top attractions to visit in Tokyo?"
        st.session_state.showing_welcome = False

# Main content area
col1, col2, col3 = st.columns([1, 10, 1])
with col2:
    st.markdown('<h1 class="main-header">Jetzy</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your personal travel planner for seamless trip organization</p>', unsafe_allow_html=True)

    # Query input area
    with st.container():
        with st.form(key="query_form", clear_on_submit=False):
            # Use session state for input if available
            query_value = st.session_state.get('query_input', '')
            user_query = st.text_area(
                "What would you like to know about your travel plans?", 
                value=query_value,
                height=100, 
                placeholder="e.g., I want to travel from New York to Paris next summer. What flights are available?"
            )
            
            col1, col2 = st.columns([5, 1])
            with col2:
                submit_button = st.form_submit_button("Send")
            
            # Clear the session state input after retrieving it
            if 'query_input' in st.session_state:
                del st.session_state.query_input

    # Show welcome message or process query
    if st.session_state.showing_welcome and not submit_button:
        st.markdown("""
        <div class="feature-card">
            <h3>👋 Welcome to Jetzy!</h3>
            <p>I'm your travel assistant, ready to help plan your perfect trip. Ask me about flights, hotels, 
            local attractions, restaurants, transportation options, or seasonal travel advice.</p>
            <p>Try asking questions like:</p>
            <ul>
                <li>"What flights are available from London to Tokyo in June?"</li>
                <li>"Recommend me luxury hotels in Dubai"</li>
                <li>"What are the must-see attractions in Rome?"</li>
                <li>"How should I get around in Bangkok?"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature cards in 3 columns
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("### How Jetzy Works")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h4>Ask Naturally</h4>
                <p>Simply type your travel questions in natural language. No need for specific formats or keywords.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <h4>Smart Analysis</h4>
                <p>Our AI analyzes your query and connects to the right travel tools and databases for accurate information.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">✨</div>
                <h4>Personalized Results</h4>
                <p>Get customized travel recommendations based on your preferences and requirements.</p>
            </div>
            """, unsafe_allow_html=True)
    
    if submit_button and user_query:
            # Add user query to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.session_state.showing_welcome = False
            
            # Update context with the current query 
            context_manager.update_context_from_text(user_query)
            
            # Record the search query in context
            context_manager.add_search(user_query)
            
            # Show a spinner while processing
            with st.spinner("Planning your perfect trip..."):
                # Pass the context to the MCP client
                response = run_async(user_query, context_manager.to_dict())
            
            # Add assistant response to chat history
            assistant_message = {"role": "assistant", "content": response}
            st.session_state.chat_history.append(assistant_message)
            
            # Update the context based on the assistant's response
            context_manager.update_context(assistant_message)

    # Display chat history
    if not st.session_state.showing_welcome or (submit_button and user_query):
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='assistant-message'>{message['content']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Add footer
st.markdown("<div class='footer'>Jetzy • Powered by advanced AI technology</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    pass