import os
import json
import asyncio
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

server_params = StdioServerParameters(command="python", args=["mcp_server.py"])

def llm_client(message: str, context=None):
    """
    Send a message to the LLM and return the response.
    Includes user context for better personalization.
    """
    try:
        logger.info("Sending request to OpenAI API")

        # Initialize the OpenAI client
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create system message with context awareness
        system_message = "You are a knowledgeable travel assistant with expertise in flight information. "
        
        if context:
            # Add contextual information if available
            system_message += "Here's information about the user I want you to use to personalize your response:\n"
            
            if context.get("location"):
                system_message += f"- Their current location seems to be {context['location']}\n"
            
            # Add current trip information
            current_trip = context.get("current_trip", {})
            if current_trip.get("origin") and current_trip.get("destination"):
                system_message += f"- They are planning a trip from {current_trip['origin']} to {current_trip['destination']}\n"
                
                if current_trip.get("date_range"):
                    system_message += f"- Their travel dates are: {current_trip['date_range']}\n"
                
                if current_trip.get("budget"):
                    system_message += f"- Their budget level is: {current_trip['budget']}\n"
            
            # Add mentioned destinations
            mentioned = context.get("mentioned_destinations", [])
            if mentioned:
                system_message += f"- Destinations mentioned in conversation: {', '.join(mentioned[:5])}\n"
            
            # Add recent searches for context
            recent = context.get("recent_searches", [])
            if recent:
                system_message += f"- Their recent searches include: {recent[0]}\n"
        
        system_message += "\nWhen sharing travel information, write in a natural, conversational style. Include: \n - Common departure airports for the origin city \n - Typical price ranges and popular airlines for this route \n - If specific flight data is available, highlight the best deals with exact dates and prices \n - Include the provided booking links for each flight option, hotel aption, accommodation option and restaurant option when available \n - Alternatively, Always provide direct links to relevant booking sites based on the query:\n   * For flights: suggest checking booking sites like Skyscanner, Expedia, or Google Flights\n   * For hotels: suggest checking booking sites like Booking.com, Hotels.com, or Airbnb\n   * For attractions: suggest checking booking sites like TripAdvisor, GetYourGuide, or Viator\n   * For restaurants: suggest checking booking sites like TripAdvisor, OpenTable, or Yelp\n - Always offer to help with related travel needs (hotels, attractions, etc.) Format your response as if you're a helpful travel agent having a conversation, not just listing data. Do not say you are an AI or language model. Just sound like a real assistant."
        
        # Send the message to the LLM
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
        
        # Extract and return the response content
        content = response.choices[0].message.content 

        logger.info(f"Received response from LLM: {content[:100]}...")  

        return content
    except Exception as e:
        logger.error(f"Error in LLM client: {e}")
        return f"Error communicating with AI service: {str(e)}"
    
def get_prompt_to_identify_tool_and_arguments(query, tools, context=None):
    tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
    
    # Initial prompt
    prompt = "You are a helpful travel assistant with access to these tools:\n\n"
    prompt += f"{tools_description}\n\n"
    
    # Add context information if available
    if context:
        prompt += "### USER CONTEXT INFO ###\n"
        
        # Add current trip information
        current_trip = context.get("current_trip", {})
        if current_trip.get("origin") and current_trip.get("destination"):
            prompt += f"- Current trip: {current_trip['origin']} to {current_trip['destination']}\n"
            
            if current_trip.get("date_range"):
                prompt += f"- Travel dates: {current_trip['date_range']}\n"
            
            if current_trip.get("budget"):
                prompt += f"- Budget level: {current_trip['budget']}\n"
        
        # Add destinations mentioned in conversation
        mentioned = context.get("mentioned_destinations", [])
        if mentioned:
            prompt += f"- Destinations discussed: {', '.join(mentioned[:5])}\n"
        
        prompt += "### END CONTEXT INFO ###\n\n"
    
    # # Continue with the rest of the prompt
    # prompt += "Choose the appropriate tool based on the user's question and extract all necessary parameters.\n"
    # prompt += f"User's Question: {query}\n\n"
    # prompt += "If no tool is needed, reply directly with a helpful travel-related answer.\n\n"
    # prompt += "IMPORTANT: When you need to use a tool, you must ONLY respond with "
    # prompt += "the exact JSON object format below, nothing else:\n"
    # prompt += "{\n"
    # prompt += '    "tool": "tool-name",\n'
    # prompt += '    "arguments": {\n'
    # prompt += '        "argument-name": "value"\n'
    # prompt += "    }\n"
    # prompt += "}\n\n"
    # prompt += "Format requirements:\n"
    # prompt += "- For dates, use YYYY-MM-DD format\n"
    # prompt += "- City names should be full names (e.g., 'New York' not 'NY')\n"
    # prompt += "- For date ranges, use the format 'YYYY-MM-DD to YYYY-MM-DD'\n"
    # prompt += "- Use information from the user context when the user query is vague or refers to previous conversation"

    # Guide for when to use tools vs. direct response
    prompt += "IMPORTANT DECISION RULES:\n"
    prompt += "1. For vague queries like 'Find me a flight', determine if you have enough context from previous conversation to provide real flight information using a tool.\n"
    prompt += "2. First check if necessary context (origin, destination, dates) is in USER CONTEXT INFO.\n"
    prompt += "3. If you have enough context information, use the appropriate tool to provide specific results.\n"
    prompt += "4. If you don't have enough context for a tool call, respond directly with general information and include relevant booking website links.\n\n"
    
    # Continue with the rest of the prompt
    prompt += f"User's Question: {query}\n\n"
    prompt += "IMPORTANT: When you need to use a tool, you must ONLY respond with "
    prompt += "the exact JSON object format below, nothing else:\n"
    prompt += "{\n"
    prompt += '    "tool": "tool-name",\n'
    prompt += '    "arguments": {\n'
    prompt += '        "argument-name": "value"\n'
    prompt += "    }\n"
    prompt += "}\n\n"
    prompt += "Format requirements:\n"
    prompt += "- For dates, use YYYY-MM-DD format\n"
    prompt += "- City names should be full names (e.g., 'New York' not 'NY')\n"
    prompt += "- For date ranges, use the format 'YYYY-MM-DD to YYYY-MM-DD'\n"
    prompt += "- Use information from the user context when the user query is vague or refers to previous conversation"
    
    return prompt
    
async def run_tool_query(query: str, context=None):
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Get the list of available tools
                tools = await session.list_tools()
                
                prompt = get_prompt_to_identify_tool_and_arguments(query, tools.tools, context)
                llm_response = llm_client(prompt, context)
                
                try:
                    # Check if response is valid JSON
                    tool_call = json.loads(llm_response)
                    
                    if not isinstance(tool_call, dict) or "tool" not in tool_call:
                        # This is a direct response, not a tool call
                        return llm_response
                    
                    available_tool_names = [tool.name for tool in tools.tools]
                    
                    if tool_call["tool"] not in available_tool_names:
                        return f"I don't have access to the tool needed for this query. Here's what I understand about your request: {query}"
                    
                    result = await session.call_tool(tool_call["tool"], arguments=tool_call["arguments"])
                    
                    # Get tool_data content
                    tool_data = result.content[0].text
                    
                    # Format response based on the tool type
                    if tool_call["tool"] == "search_flights":
                        try:
                            flights_data = json.loads(tool_data)

                            # Validate the response format
                            if not flights_data:
                                return "I searched but couldn't find any flights matching your criteria. Would you like to try different dates or destinations?"
                            
                            # # Check if the result is a list or a single object
                            # if isinstance(flights_data, list):
                            #     flights = flights_data
                            # elif:
                            #     # If it's a single flight object, put it in a list
                            #     flights = [flights_data]
                            # else:
                            #     raise ValueError("Unexpected response format")
                            
                            # Convert to list if a single flight was returned
                            # if isinstance(flights_data, dict) and all(key in flights_data for key in ['airline', 'price_usd']):
                            if isinstance(flights_data, dict):
                                flights = [flights_data]  # Single flight object
                            elif isinstance(flights_data, list):
                                flights = flights_data    # Multiple flights
                            else:
                                # If unexpected format but has 'flights' key
                                # if isinstance(flights_data, dict) and 'flights' in flights_data:
                                #     flights = flights_data['flights']
                                # else:
                                #     raise ValueError(f"Unexpected flight data format: {type(flights_data)}")
                                logger.warning(f"Unexpected flight data type: {type(flights_data)}")
                                return "I couldn't process the flight search results. Would you like general information about this route instead?"
                                
                            # Validate each flight has the required fields
                            for flight in flights:
                                required_fields = ['airline', 'price_usd', 'departure_date', 'return_date']
                                for field in required_fields:
                                    if field not in flight:
                                        flight[field] = "Not specified"

                            response = f"I found these flights from {tool_call['arguments']['from_location']} to {tool_call['arguments']['to_location']}:\n\n"

                            for flight in flights:
                                response += f"• {flight['airline']}: ${flight['price_usd']} - Departs {flight['departure_date']}, Returns {flight['return_date']}\n. Book flight now: {flight['mock_booking_link']}"

                            response += "\n Would you like me to help you find hotels at your destination?"

                            return response
                        except json.JSONDecodeError:
                            logger.error("Failed to parse flight data JSON")
                            return "⚠️ Sorry, I received invalid data from the flight search. Would you like to try again?"
                        except Exception as e:
                            logger.error(f"Error processing flight data: {e}")
                            return "⚠️ Sorry, I couldn't handle that flight request right now."
                    elif tool_call["tool"] == "recommend_hotels":
                        try:
                            hotels = json.loads(tool_data)
                            budget = tool_call['arguments'].get('budget', 'medium')
                            response = f"Here are some recommended {budget} hotels in {tool_call['arguments']['location']}:\n\n"
                            for hotel in hotels:
                                response += f"• {hotel['name']}: ${hotel['price_per_night_usd']} per night - Rating: {hotel['rating']}/5.0\n"
                            
                            # Add contextual follow-up question based on previous conversation
                            if context and "mentioned_destinations" in context:
                                if tool_call['arguments']['location'] in context["mentioned_destinations"]:
                                    response += "\nWould you like to know about attractions in this area as well?"
                            
                            return response
                        except:
                            return "⚠️ Sorry, I couldn't handle that request right now."
                    elif tool_call["tool"] == "recommend_attractions":
                        try:
                            attractions = json.loads(tool_data)
                            response = f"Here are some popular attractions in {tool_call['arguments']['location']}:\n\n"
                            for attraction in attractions:
                                response += f"• {attraction['name']}: {attraction['description']}\n"
                            
                            response += "\nWould you like restaurant recommendations as well?"
                            return response
                        except Exception as e:
                            logger.error(f"Error processing attractions data: {e}")
                            return "⚠️ Sorry, I couldn't process the attractions data right now. Please try again later."
                    elif tool_call["tool"] == "recommend_restaurants":
                        try:
                            restaurants = json.loads(tool_data)
                            cuisine = tool_call['arguments'].get('cuisine', 'local')
                            response = f"Here are some {cuisine} restaurants in {tool_call['arguments']['location']}:\n\n"
                            for restaurant in restaurants:
                                response += f"• {restaurant['name']} - Rating: {restaurant['rating']}/5.0\n"
                            
                            return response
                        except Exception as e:
                            logger.error(f"Error parsing restaurant data: {e}")
                            return f"I found some restaurants, but I'm having trouble formatting the details. Here's the raw information: {tool_data}"
                    
                    elif tool_call["tool"] == "transport_options":
                        try:
                            options = json.loads(tool_data)
                            response = f"Here are transportation options from {tool_call['arguments']['from_location']} to {tool_call['arguments']['to_location']}:\n\n"
                            for mode, details in options.items():
                                response += f"• By {mode}: {details['duration']} journey time - ${details['price_usd']}\n"
                            
                            return response
                        except Exception as e:
                            logger.error(f"Error parsing transport data: {e}")
                            return f"I found some transport options, but I'm having trouble formatting the details. Here's the raw information: {tool_data}"
                        
                    elif tool_call["tool"] == "seasonal_travel_advice":
                        try:
                            # This tool returns a plain string, not JSON
                            advice = tool_data
                            destination = tool_call['arguments']['destination']
                            
                            response = f"📅 Seasonal Travel Advice for {destination}:\n\n"
                            response += f"{advice}\n\n"
                            response += "Would you like information about attractions or hotels in this destination?"
                            
                            return response
                        except Exception as e:
                            logger.error(f"Error formatting seasonal advice: {e}")
                            return f"I have some seasonal travel information, but I'm having trouble formatting it properly. Here's what I know: {tool_data}"
                                            
                    else:
                        # For other tools, return the raw response
                        logger.warning(f"Unhandled tool: {tool_call['tool']}")
                        return "⚠️ Sorry, I couldn’t handle that request right now."
                    
                except json.JSONDecodeError:
                    # If we can't parse JSON, the LLM gave a direct response
                    return llm_response
                except Exception as e:
                    return f"I encountered an error while processing your request: {str(e)}. Let me help you directly instead."
    except Exception as e:
        return f"I couldn't connect to my travel tools right now. Error: {str(e)}. Please try again later."

def run_async(query, context=None):
    """
    Run the asyncio event loop to process the query.
    Returns a string response suitable for displaying to the user.
    
    Args:
        query (str): The user's query
        context (dict, optional): User context for personalized responses
    """
    try:
        result = asyncio.run(run_tool_query(query))
        logger.info(f"Final result type: {type(result)}")
        logger.info(f"Final result preview: {str(result)[:100]}")
        
        if isinstance(result, dict) and "result" in result:
            return result["result"]
        return result
    except Exception as e:
        logger.error(f"Error in run_async: {e}")
        return f"Sorry, I encountered an error while processing your request: {str(e)}"

if __name__ == "__main__":
    pass