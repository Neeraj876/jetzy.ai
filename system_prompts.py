from typing import List, Dict, Any

def format_messages_for_openai(
    user_messages: List[Dict[str, str]],
    system_prompt: str
) -> List[Dict[str, str]]:
    """
    Format messages for the OpenAI API using the Model Context Protocol format.
    
    Args:
        user_messages: List of message objects from the conversation history
        system_prompt: System prompt to guide the assistant
        
    Returns:
        List of message objects formatted for OpenAI API
    """
    formatted_messages = []
    
    # Add system message at the beginning
    formatted_messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # Add user messages
    for message in user_messages:
        formatted_messages.append(message)
    
    return formatted_messages

def create_base_system_prompt() -> str:
    """
    Create the base system prompt for the Jetzy Travel AI ChatBot.
    
    Returns:
        Base system prompt string
    """
    return """You are the Jetzy Travel AI ChatBot, an intelligent conversational travel assistant.

Your primary functions:
1. Provide travel information: Deliver relevant, accurate travel data to users
2. Personalization: Offer tailored recommendations using user preferences
3. Real-time assistance: Provide up-to-date travel details 
4. Enhance user experience: Ensure intuitive and seamless conversations

You can help with:
- Flight search: Provide airline options, prices, schedules, and booking links
- Hotel recommendations: Suggest hotels based on budget, preferences, location
- Local attractions: Recommend tourist attractions and activities
- Dining recommendations: Provide restaurant options with cuisine and ratings
- Transport assistance: Offer travel options between destinations
- Seasonal travel advice: Suggest ideal travel times based on weather and events

Always be conversational, helpful, and concise. When providing recommendations, 
note that in the actual app, your responses would include links to book or learn more 
about each option.
"""

def add_context_to_system_prompt(
    base_prompt: str, 
    context: Dict[str, Any]
) -> str:
    """
    Enhance the system prompt with user context information.
    
    Args:
        base_prompt: Base system prompt
        context: User context information
        
    Returns:
        Enhanced system prompt with context
    """
    enhanced_prompt = base_prompt
    
    # Add location context if available
    if context.get("location"):
        enhanced_prompt += f"\n\nThe user is currently located in {context['location']}."
    
    # Add preferences context if available
    preferences = context.get("preferences", {})
    if preferences:
        pref_text = "\n\nUser preferences:"
        
        if preferences.get("home_airport"):
            pref_text += f"\n- Home airport: {preferences['home_airport']}"
            
        if preferences.get("preferred_airlines") and preferences["preferred_airlines"] != ["Any"]:
            airlines = ", ".join(preferences["preferred_airlines"])
            pref_text += f"\n- Preferred airlines: {airlines}"
            
        if preferences.get("budget_level"):
            pref_text += f"\n- Budget level: {preferences['budget_level']}"
            
        if preferences.get("travel_interests") and len(preferences["travel_interests"]) > 0:
            interests = ", ".join(preferences["travel_interests"])
            pref_text += f"\n- Travel interests: {interests}"
            
        enhanced_prompt += pref_text
    
    # Add recent search context if available
    recent_searches = context.get("recent_searches", [])
    if recent_searches:
        searches = ", ".join(recent_searches[:3])  # Use only the 3 most recent searches
        enhanced_prompt += f"\n\nRecent searches: {searches}"
    
    # Add mentioned destinations context if available
    mentioned = context.get("mentioned_destinations", set())
    if mentioned:
        destinations = ", ".join(list(mentioned)[:5])  # Use only the 5 most recent destinations
        enhanced_prompt += f"\n\nPreviously discussed destinations: {destinations}"
    
    return enhanced_prompt

def extract_context_from_response(response_content: str) -> Dict[str, Any]:
    """
    Extract contextual information from the assistant's response.
    This is a simplified implementation - in a real application, 
    you might use NLP techniques for better extraction.
    
    Args:
        response_content: The content of the assistant's response
        
    Returns:
        Dictionary of extracted context information
    """
    extracted_context = {
        "mentioned_destinations": set(),
        "mentioned_interests": set()
    }
    
    # Simple destination extraction based on keyword matching
    # In a real application, you would use NLP for better extraction
    potential_destinations = [
        "New York", "Rome", "Paris", "London", "Tokyo", "Greece", 
        "Italy", "France", "Egypt", "Milan", "Barcelona", "Madrid",
        "Amsterdam", "Berlin", "Vienna", "Prague", "Budapest"
    ]
    
    for destination in potential_destinations:
        if destination.lower() in response_content.lower():
            extracted_context["mentioned_destinations"].add(destination)
    
    # Simple interest extraction
    potential_interests = [
        "beach", "mountain", "museum", "food", "culture", "history",
        "adventure", "relax", "shopping", "nightlife", "nature"
    ]
    
    for interest in potential_interests:
        if interest.lower() in response_content.lower():
            extracted_context["mentioned_interests"].add(interest)
    
    return extracted_context