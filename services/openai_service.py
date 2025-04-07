# import openai
import os
from openai import OpenAI
from typing import List, Dict, Any
from mcp.tools import get_available_tools

class OpenAIService:
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-3.5-turbo", 
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 0.9,
        frequency_penalty: float = 0.2,
        presence_penalty: float = 0.3
    ):
        """
        Initialize the OpenAI service with the specified parameters.
        """
        # openai.api_key = api_key
        # self.client = OpenAI(api_key=api_key)
        os.environ["OPENAI_API_KEY"] = api_key
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        
        # Get tools for function calling
        self.tools = get_available_tools()
        
    def _create_system_message(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Create a system message with context to guide the AI responses.
        """
        # Base system prompt
        system_prompt = """
        You are the Jetzy Travel AI ChatBot, an intelligent conversational travel assistant.
        Provide helpful, accurate, and personalized travel information including flight options,
        hotel recommendations, local attractions, dining options, and transportation advice.
        Always be conversational, friendly, and concise in your responses.
        
        When providing recommendations, include brief descriptions and note that booking 
        links would normally be provided (but you don't need to include fake links).
        """
        
        # Add contextual information if available
        if context.get("location"):
            system_prompt += f"\nThe user is currently located in {context['location']}."
            
        if context.get("preferences"):
            prefs = context["preferences"]
            preferences_text = "User preferences:"
            
            if prefs.get("home_airport"):
                preferences_text += f"\n- Home airport: {prefs['home_airport']}"
            if prefs.get("preferred_airlines") and prefs["preferred_airlines"] != ["Any"]:
                preferences_text += f"\n- Preferred airlines: {', '.join(prefs['preferred_airlines'])}"
            if prefs.get("budget_level"):
                preferences_text += f"\n- Budget level: {prefs['budget_level']}"
            if prefs.get("travel_interests"):
                preferences_text += f"\n- Travel interests: {', '.join(prefs['travel_interests'])}"
                
            system_prompt += f"\n\n{preferences_text}"
            
        return {"role": "system", "content": system_prompt}
    
    def get_response(self, messages: List[Dict[str, str]], context: Dict[str, Any]) -> Dict[str, str]:
        """
        Simulate a response from the assistant.
        """
        last_user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "Hello")
        return {
            "role": "assistant",
            "content": f"(Simulated Response) You said: '{last_user_message}'. Here's a fun travel tip: Always carry a power bank! ⚡"
        }

        
    # def get_response(self, messages: List[Dict[str, str]], context: Dict[str, Any]) -> Dict[str, str]:
    #     """
    #     Get a response from the OpenAI API using the Model Context Protocol.
        
    #     Args:
    #         messages: List of message objects [{"role": "user", "content": "message"}, ...]
    #         context: User context information including location, preferences, etc.
            
    #     Returns:
    #         The assistant's response as a message object.
    #     """
    #     # Create a copy of messages to avoid modifying the original
    #     messages_copy = messages.copy()
        
    #     # Insert system message at the beginning
    #     system_message = self._create_system_message(context)
    #     messages_copy.insert(0, system_message)
        
    #     # Filter out any messages with role 'system' except for our own
    #     messages_copy = [msg for i, msg in enumerate(messages_copy) 
    #                      if i == 0 or msg["role"] != "system"]
        
    #     try:
    #         # Call OpenAI API with tools
    #         # response = openai.ChatCompletion.create(
    #         #     model=self.model,
    #         #     messages=messages_copy,
    #         #     temperature=self.temperature,
    #         #     max_tokens=self.max_tokens,
    #         #     top_p=self.top_p,
    #         #     frequency_penalty=self.frequency_penalty,
    #         #     presence_penalty=self.presence_penalty,
    #         #     tools=self.tools,
    #         #     tool_choice="auto"
    #         # )
    #         response = self.client.chat.completions.create(
    #             model=self.model,
    #             messages=messages_copy,
    #             temperature=self.temperature,
    #             max_tokens=self.max_tokens,
    #             top_p=self.top_p,
    #             frequency_penalty=self.frequency_penalty,
    #             presence_penalty=self.presence_penalty
    #         )
            
    #         assistant_message = response.choices[0].message
            
    #         # Handle tool calls if present
    #         if assistant_message.get("tool_calls"):
    #             # Process tool calls and get results
    #             assistant_message = self._handle_tool_calls(assistant_message, messages_copy)
            
    #         return {
    #             "role": "assistant",
    #             "content": assistant_message["content"]
    #         }
            
    #     except Exception as e:
    #         # Handle API errors gracefully
    #         error_msg = f"I'm sorry, I encountered an error: {str(e)}. Please try again."
    #         return {"role": "assistant", "content": error_msg}

    
    
    # def _handle_tool_calls(self, assistant_message, messages):
    #     """
    #     Process any tool calls from the assistant message.
        
    #     For now, this is a placeholder that would later be implemented to
    #     handle actual API integrations. Currently returns mock responses.
    #     """
    #     from mcp.tools import execute_tool_call
    #     import json
        
    #     # Process each tool call
    #     for tool_call in assistant_message.get("tool_calls", []):
    #         function_name = tool_call["function"]["name"]
    #         arguments = json.loads(tool_call["function"]["arguments"])
            
    #         # Execute the tool call
    #         result = execute_tool_call(function_name, arguments)
            
    #         # Add the tool response to messages
    #         messages.append({
    #             "tool_call_id": tool_call["id"],
    #             "role": "tool",
    #             "name": function_name,
    #             "content": json.dumps(result)
    #         })
        
    #     # Get a new response from the model with the tool results
    #     # second_response = openai.ChatCompletion.create(
    #     #     model=self.model,
    #     #     messages=messages,
    #     #     temperature=self.temperature,
    #     #     max_tokens=self.max_tokens,
    #     #     top_p=self.top_p,
    #     #     frequency_penalty=self.frequency_penalty,
    #     #     presence_penalty=self.presence_penalty
    #     # )
    #     second_response = self.client.chat.completions.create(
    #         model=self.model,
    #         messages=messages,
    #         temperature=self.temperature,
    #         max_tokens=self.max_tokens,
    #         top_p=self.top_p,
    #         frequency_penalty=self.frequency_penalty,
    #         presence_penalty=self.presence_penalty
    #     )
        
    #     return second_response.choices[0].message
    def _handle_tool_calls(self, assistant_message, messages):
        """
        Simulate handling tool calls by generating mock tool outputs and a follow-up assistant message.
        """
        import json
        from mcp.tools import execute_tool_call

        # Process each tool call
        for tool_call in assistant_message.get("tool_calls", []):
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])

            # Simulate executing the tool call
            result = execute_tool_call(function_name, arguments)

            # Add the tool response to the message list
            messages.append({
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": function_name,
                "content": json.dumps(result)
            })

        # Instead of calling the OpenAI API again, simulate a follow-up response
        return {
            "role": "assistant",
            "content": f"(Simulated Response after Tool Calls) I ran {len(assistant_message['tool_calls'])} tool(s) and here's the result: {json.dumps(result)}"
        }
