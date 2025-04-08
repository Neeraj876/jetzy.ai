import streamlit as st
import openai
from typing import List, Dict, Any
import json
import os
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenAIClient:
    """
    Client for integrating with OpenAI API using the Model Context Protocol.
    """
    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo"):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model: OpenAI model to use
        """
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Provide it or set OPENAI_API_KEY environment variable.")
        
        # Set up the client
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def send_message(
        self, 
        messages: List[Dict[str, str]], 
        tools: List[Dict[str, Any]] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Send a message to the OpenAI API and get a response.
        Includes retry logic for robustness.
        
        Args:
            messages: List of messages in OpenAI format
            tools: List of tool definitions for function calling
            temperature: Temperature parameter for response generation
            
        Returns:
            The OpenAI API response
        """
        try:
            # Prepare API call parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            # Make the API call
            response = self.client.chat.completions.create(**params)
            
            # Return the response
            return self._process_response(response)
        
        except Exception as e:
            st.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    def _process_response(self, response) -> Dict[str, Any]:
        """
        Process the OpenAI API response.
        
        Args:
            response: Response from OpenAI API
            
        Returns:
            Processed response with message content and tool calls
        """
        message = response.choices[0].message
        
        # Extract the basic response content
        processed_response = {
            "content": message.content or "",
            "role": "assistant"
        }
        
        # Process tool calls if any
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                tool_calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                })
            processed_response["tool_calls"] = tool_calls
        
        return processed_response

class JetzyTravelAssistant:
    """
    Main class for the Jetzy Travel AI Assistant that integrates
    context management, OpenAI API, and tool execution.
    """
    def __init__(self, api_key: str = None):
        """
        Initialize the travel assistant.
        
        Args:
            api_key: OpenAI API key
        """
        # Initialize components
        self.openai_client = OpenAIClient(api_key)
        self.context_manager = ContextManager()
        
        # Initialize conversation history
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = []
    
    def process_user_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message and get an AI response.
        
        Args:
            user_message: User's message text
            
        Returns:
            The assistant's response
        """
        # Add user message to conversation history
        user_msg_obj = {"role": "user", "content": user_message}
        st.session_state.conversation_history.append(user_msg_obj)
        
        # Get user context
        user_context = self.context_manager.get_user_context()
        
        # Create system prompt with context
        base_prompt = create_base_system_prompt()
        system_prompt = add_context_to_system_prompt(base_prompt, user_context)
        
        # Format messages for OpenAI
        formatted_messages = format_messages_for_openai(
            st.session_state.conversation_history, 
            system_prompt
        )
        
        # Get available tools
        tools = get_available_tools()
        
        # Send message to OpenAI
        response = self.openai_client.send_message(
            messages=formatted_messages,
            tools=tools
        )
        
        # Handle tool calls if any
        if "tool_calls" in response:
            response = self._handle_tool_calls(response, formatted_messages)
        
        # Add assistant response to conversation history
        assistant_msg = {"role": "assistant", "content": response["content"]}
        st.session_state.conversation_history.append(assistant_msg)
        
        # Update context based on response
        extracted_context = extract_context_from_response(response["content"])
        for destination in extracted_context.get("mentioned_destinations", []):
            self.context_manager.add_mentioned_destination(destination)
        
        return response
    
    def _handle_tool_calls(
        self, 
        response: Dict[str, Any], 
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Handle any tool calls from the assistant.
        
        Args:
            response: The assistant's response with tool calls
            messages: The current message history
            
        Returns:
            Updated response after tool execution
        """
        if "tool_calls" not in response:
            return response
        
        # Execute each tool call
        tool_results = []
        for tool_call in response["tool_calls"]:
            # Execute the tool
            result = execute_tool_call(
                tool_call["name"], 
                tool_call["arguments"]
            )
            
            # Add the result to tool results
            tool_results.append({
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": tool_call["name"],
                "content": json.dumps(result)
            })
        
        # Add tool results to messages
        new_messages = messages.copy()
        new_messages.append({
            "role": "assistant",
            "content": response["content"],
            "tool_calls": response["tool_calls"]
        })
        for tool_result in tool_results:
            new_messages.append(tool_result)
        
        # Get a new response from OpenAI with the tool results
        final_response = self.openai_client.send_message(messages=new_messages)
        return final_response
    
    def clear_conversation(self):
        """Clear the conversation history"""
        st.session_state.conversation_history = []
        self.context_manager.clear_context()

# Example Streamlit app implementation
def main():
    st.set_page_config(page_title="Jetzy Travel AI", page_icon="✈️")
    st.title("Jetzy Travel AI Assistant")
    
    # Initialize the assistant
    if "assistant" not in st.session_state:
        api_key = st.secrets.get("OPENAI_API_KEY", None)
        st.session_state.assistant = JetzyTravelAssistant(api_key)
    
    # Chat container
    chat_container = st.container()
    
    # User input
    user_message = st.chat_input("Ask me about travel...")
    
    # Clear conversation button
    if st.sidebar.button("Clear Conversation"):
        st.session_state.assistant.clear_conversation()
        st.rerun()
    
    # Update location in sidebar
    with st.sidebar:
        st.subheader("Your Current Location")
        location = st.text_input("Enter your location", key="user_location")
        if st.button("Update Location"):
            st.session_state.assistant.context_manager.set_location(location)
            st.success(f"Location updated to {location}")
    
    # Handle user message
    if user_message:
        # Process the message and get response
        response = st.session_state.assistant.process_user_message(user_message)
        
        # Force a rerun to update the UI
        st.rerun()
    
    # Display conversation history
    with chat_container:
        for msg in st.session_state.get("conversation_history", []):
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

if __name__ == "__main__":
    main()