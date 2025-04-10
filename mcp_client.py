import os
import json
import asyncio
import datetime
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
            
            system_message += "\nWhen sharing travel information, write in a natural, conversational style. Include: \n - Common departure airports for the origin city \n - Typical price ranges and popular airlines for this route \n - If specific flight data is available, highlight the best deals with exact dates and prices \n - YOU MUST INCLUDE BOOKING LINKS FOR EACH FLIGHT OPTION, HOTEL OPTION, ACCOMMODATION OPTION AND RESTAURANT OPTION MENTIONED IN YOUR RESPONSE \n - For flights: use mockup links like https://mockflights.com/book/airline-name \n - For hotels: use mockup links like https://mockhotels.com/book/hotel-name \n - For attractions: use links to TripAdvisor, GetYourGuide, or Viator \n - For restaurants: use links to TripAdvisor, OpenTable, or Yelp \n - Always offer to help with related travel needs (hotels, attractions, etc.)"
            
            # NEW: Add instruction for providing realistic data even for partial queries
            system_message += "\n\nIMPORTANT: When the user provides incomplete information (like just a destination without origin or dates), don't just ask for more information. Instead, provide helpful general information about typical flights to that destination including:\n- Common departure cities (New York, London, etc.)\n- Typical price ranges (e.g., '$600-900 roundtrip')\n- Popular airlines for this route\n- Example deals like 'There's a flight on Norwegian leaving New York 18th April to Athens, and back on 30th April for $403'\n- ALWAYS include realistic pricing data and specific flight examples\n- ALWAYS include clickable booking links for EACH flight option mentioned\n\nFormat your response as if you're a helpful travel agent having a conversation, not just listing data. Do not say you are an AI or language model. Just sound like a real assistant."
            
            # CRITICAL: emphasize that booking links are absolutely required
            system_message += "\n\nCRITICAL: Your response MUST include booking links for ALL options mentioned. If you don't include these links, the system will ignore your response and use a different method instead."
            
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
        
        # Add location if available for better defaults
        if context.get("location"):
            prompt += f"- User's current location: {context['location']}\n"
        
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
    
    # UPDATED: Guide for when to use tools vs. direct response
    prompt += "DECISION GUIDE:\n"
    prompt += "1. For flight queries: If origin, destination and dates are available (either from the query or context), use search_flights.\n"
    prompt += "2. For vague flight queries (like 'Find me flights to Paris'), use search_flights if you can determine an origin from context, creating a reasonable date range for next month if none specified.\n"
    prompt += "3. For hotel, attraction, or restaurant queries: Use the appropriate tool as long as location is provided.\n"
    prompt += "4. IMPORTANT: If the query explicitly asks for booking links or requires detailed pricing information, always use a tool rather than providing a general response.\n\n"
    
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
    prompt += "- Use information from the user context when the user query is vague or refers to previous conversation\n"
    prompt += "- If dates are missing and not in context, CREATE reasonable dates for next month instead of skipping the tool call\n"
    prompt += "- If origin is missing, use the user's location from context or 'New York' as a default rather than skipping the tool call"
    
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
                            
                            # Convert to list if a single flight was returned
                            if isinstance(flights_data, dict):
                                flights = [flights_data]  # Single flight object
                            elif isinstance(flights_data, list):
                                flights = flights_data    # Multiple flights
                            else:
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
                        return "⚠️ Sorry, I couldn't handle that request right now."
                    
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
        # Check if we have a very basic query with just a destination. If so, enhance it with some default information to get a better response
        words = query.lower().split()

        # Default location to use if none available in context
        default_origin = "New York"

        # Check if this is a simple destination query that might be handled by LLM
        if (len(words) <= 7 and 
            ("flight" in query.lower() or "fly" in query.lower()) and 
            "to " in query.lower() and 
            "from " not in query.lower()):
            
            # Use contextual origin if available
            origin = default_origin
            if context and context.get("current_trip", {}).get("origin"):
                origin = context["current_trip"]["origin"]
            elif context and context.get("location"):
                origin = context["location"]
                
            enhanced_query = f"Tell me about flights from {origin} to {query.lower().split('to ')[1].strip()}. Provide specific examples with dates and prices. IMPORTANT: You MUST include booking links for each flight option mentioned."

            # Try the LLM first
            llm_response = llm_client(enhanced_query, context)
            
            # Check if response contains booking links
            if "http" in llm_response and ("book" in llm_response.lower() or "booking" in llm_response.lower()):
                logger.info("LLM provided response with booking links")
                return llm_response
            else:
                # LLM didn't include required booking links, fall back to tool
                logger.info("LLM response missing booking links, falling back to tool workflow")
                # Extract destination for the tool call
                destination = query.lower().split("to ")[1].strip()
                # Create date range for next month (example)
                today = datetime.datetime.now()
                next_month = today + datetime.timedelta(days=30)
                date_start = next_month.strftime("%Y-%m-%d")
                date_end = (next_month + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                date_range = f"{date_start} to {date_end}"
                
                # Construct a synthetic query for the tool workflow
                tool_query = f"Find flights from {origin} to {destination} from {date_range}"
                result = asyncio.run(run_tool_query(tool_query, context))
                return result
        
        # For all other queries, proceed with normal tool selection flow
        result = asyncio.run(run_tool_query(query, context))
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