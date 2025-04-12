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
    prompt = "You are a travel expert assistant with a focus on providing detailed, actionable information. You have access to these tools:\n\n"
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

    # IMPROVED: Guide for comprehensive response with booking links
    prompt += "RESPONSE GUIDELINES:\n"
    prompt += "1. CRITICAL: EVERY recommendation you provide MUST include booking/reservation links or ticket purchase options.\n"
    prompt += "2. For ALL queries about flights, hotels, attractions, restaurants, or transport, use the appropriate tool.\n"
    prompt += "3. For vague queries, use context to fill in missing details rather than asking for more information.\n"
    prompt += "4. Your tool selection should match what the user is looking for, even if they don't explicitly mention the exact tool name.\n"
    prompt += "5. Provide comprehensive details for each option including pricing, ratings, and specific descriptive details.\n\n"

    # Specific guidance for each tool type
    prompt += "DETAILED TOOL USAGE INSTRUCTIONS:\n"
    prompt += "- For flight queries: Include origin, destination, flexible dates if specific ones aren't given.\n"
    prompt += "- For hotel queries: Always include specific hotel names, prices, ratings, descriptions and booking links.\n"
    prompt += "- For attraction queries: Include details about opening hours, ticket prices, and online booking options.\n"
    prompt += "- For restaurant queries: Include cuisine type, price range, ratings, and reservation links.\n"
    prompt += "- For transport options: Include duration, prices, and booking options for each transport mode.\n\n"

    # Tool selection criteria
    prompt += "TOOL SELECTION CRITERIA:\n"
    prompt += "- Flight queries (e.g., 'flights to Paris', 'how to get to Greece') → Use search_flights\n"
    prompt += "- Hotel queries (e.g., 'places to stay in Rome', 'hotels in Tokyo') → Use recommend_hotels\n"
    prompt += "- Attraction queries (e.g., 'things to do in Barcelona', 'visit museums in London') → Use recommend_attractions\n"
    prompt += "- Food queries (e.g., 'where to eat in Seoul', 'best restaurants in New York') → Use recommend_restaurants\n"
    prompt += "- Transportation queries (e.g., 'how to get around Amsterdam', 'transport in Berlin') → Use transport_options\n"
    prompt += "- Seasonal advice queries (e.g., 'best time to visit Thailand', 'weather in Mexico') → Use seasonal_travel_advice\n\n"

    # Missing information handling
    prompt += "HANDLING MISSING INFORMATION:\n"
    prompt += "- If origin location is missing: Use user's current location from context, or default to 'New York'\n"
    prompt += "- If dates are missing: Create reasonable dates for next month (e.g., 15-22 days from now)\n"
    prompt += "- If budget is missing: Default to 'medium' budget level\n"
    prompt += "- IMPORTANT: Always make an intelligent guess for missing information rather than skipping the tool call\n\n"
    
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
                            
                            # Origin and destination for the response
                            origin = tool_call['arguments']['from_location']
                            destination = tool_call['arguments']['to_location']
                            response = f"✈️ I found these flights from {origin} to {destination}:\n\n"
                            
                            for flight in flights:
                                # Ensure required fields exist
                                required_fields = ['airline', 'price_usd', 'departure_date', 'return_date']
                                for field in required_fields:
                                    if field not in flight:
                                        flight[field] = "Not specified"
                                
                                # Generate booking link if not provided
                                if 'mock_booking_link' not in flight:
                                    airline_slug = flight['airline'].lower().replace(' ', '-').replace("'", "")
                                    flight['mock_booking_link'] = f"https://mockflights.com/book/{airline_slug}"
                                
                                # Format the flight information with rich details
                                response += f"• {flight['airline']}: ${flight['price_usd']}\n"
                                response += f"  Departure: {flight['departure_date']} | Return: {flight['return_date']}\n"
                                
                                # Add optional details if available
                                if 'duration' in flight:
                                    response += f"  Duration: {flight['duration']}\n"
                                if 'stops' in flight:
                                    response += f"  Stops: {flight['stops']}\n"
                                if 'airports' in flight:
                                    response += f"  Airports: {flight['airports']}\n"
                                
                                # Add booking link with emoji
                                response += f"  🎫 Book flight now: {flight['mock_booking_link']}\n\n"
                            
                            # Add contextual follow-up suggestion
                            response += f"Would you like me to help you find hotels in {destination}?"

                            return response
                        except json.JSONDecodeError:
                            logger.error("Failed to parse flight data JSON")
                            return "⚠️ Sorry, I received invalid data from the flight search. Would you like to try again?"
                        except Exception as e:
                            logger.error(f"Error processing flight data: {e}")
                            return "⚠️ Sorry, I couldn't handle that flight request right now."
                    elif tool_call["tool"] == "recommend_hotels":
                        try:
                            hotels_data = json.loads(tool_data)

                            if not hotels_data:
                                return "I searched but couldn't find any hotels matching your criteria. Would you like to try different hotels?"
                            
                            if isinstance(hotels_data, dict):
                                hotels = [hotels_data]  # Single flight object
                            elif isinstance(restaurants_data, list):
                                hotels = hotels_data    # Multiple flights
                            else:
                                logger.warning(f"Unexpected Hotel data type: {type(hotels_data)}")
                                return "I couldn't process the hotel search results."

                            # budget = tool_call['arguments'].get('budget', 'medium')
                            # Enhance the response format with rich details and booking links
                            budget = tool_call['arguments'].get('budget', 'medium')
                            response = f"Here are some recommended hotels in {tool_call['arguments']['location']} (Budget: {budget}):\n\n"

                            for hotel in hotels:
                                required_fields = ['name', 'location', 'price_per_night_usd']
                                for field in required_fields:
                                    if field not in hotel:
                                        hotel[field] = "Not specified"

                                 # Generate a booking link
                                hotel_slug = hotel['name'].lower().replace(' ', '-').replace("'", "")
                                booking_link = f"https://mockhotels.com/book/{hotel_slug}"
                                
                                # Build rich response with detailed information
                                response += f"• {hotel['name']} - ${hotel['price_per_night_usd']} per night\n"
                                response += f"  Rating: {hotel['rating']}/5.0 | Location: {hotel.get('area', hotel['location'])}\n"
                                response += f"  {hotel.get('description', 'Comfortable accommodation with excellent amenities.')}\n"
                                response += f"  Amenities: {', '.join(hotel.get('amenities', ['Wi-Fi', 'Air conditioning', 'Breakfast']))}\n"
                                response += f"  📱 Book now: {booking_link}\n\n"

                               # Add contextually relevant follow-up suggestion
                            response += "Would you like recommendations for attractions or restaurants in this area as well?"
                                                
                            # Add contextual follow-up question based on previous conversation
                            if context and "mentioned_destinations" in context:
                                if tool_call['arguments']['location'] in context["mentioned_destinations"]:
                                    response += f"\nSince you mentioned {tool_call['arguments']['location']}, would you like some attraction suggestions for it?"
                            
                            return response
                        except:
                            return "⚠️ Sorry, I couldn't handle that request right now."
                    elif tool_call["tool"] == "recommend_attractions":
                        try:
                            attractions_data = json.loads(tool_data)

                            if not attractions_data:
                                return "I searched but couldn't find any attractions matching your criteria. Would you like to try different attractionss?"
                            
                            if isinstance(attractions_data, dict):
                                attractions = [attractions_data]  # Single attraction object
                            elif isinstance(attractions_data, list):
                                attractions = attractions_data    # Multiple attractions
                            else:
                                logger.warning(f"Unexpected attraction data type: {type(attractions_data)}")
                                return "I couldn't process the attractions search results."
                            
                            location = tool_call['arguments']['location']
                            response = f"Here are the top attractions in {location} worth visiting:\n\n"

                            for attraction in attractions:
                                required_fields = ['name', 'location', 'description']
                                for field in required_fields:
                                    if field not in attraction:
                                        attraction[field] = "Not specified"

                            
                                # Generate booking links
                                attraction_slug = attraction['name'].lower().replace(' ', '-').replace("'", "")
                                ticket_link = f"https://getyourguide.com/book/{attraction_slug}"
                                
                                # Build rich response
                                response += f"• {attraction['name']} - Rating: {attraction.get('rating', '4.5')}/5.0\n"
                                response += f"  {attraction['description']}\n"
                                response += f"  Hours: {attraction.get('hours', '9:00 AM - 5:00 PM daily')}\n"
                                response += f"  Price: {attraction.get('price', '$15-25 per person')}\n"
                                response += f"  🎟️ Get tickets: {ticket_link}\n\n"
                                                                        
                            # Add contextually relevant follow-up suggestion
                            response += f"Would you like restaurant recommendations in {location} as well?"
                            return response
                        except Exception as e:
                            logger.error(f"Error processing attractions data: {e}")
                            return "⚠️ Sorry, I couldn't process the attractions data right now. Please try again later."
                    elif tool_call["tool"] == "recommend_restaurants":
                        try:
                            restaurants_data = json.loads(tool_data)

                            if not restaurants_data:
                                return "I searched but couldn't find any restaurants matching your criteria. Would you like to try different restaurants?"

                        
                            if isinstance(restaurants_data, dict):
                                restaurants = [restaurants_data]  # Single restaurant object
                            elif isinstance(restaurants_data, list):
                                restaurants = restaurants_data    # Multiple restaurants
                            else:
                                logger.warning(f"Unexpected restaurant data type: {type(restaurants_data)}")
                                return "I couldn't process the restaurant search results."
                            
                            location = tool_call['arguments']['location']
                            cuisine = tool_call['arguments'].get('cuisine', 'any')

                            # Create rich response with booking links
                            response = f"Here are the top recommended restaurants in {location}"
                            if cuisine != 'any':
                                response += f" for {cuisine} cuisine"
                            response += ":\n\n"
        
                            
                            for restaurant in restaurants:
                                required_fields = ['name', 'location', 'cuisine']
                                for field in required_fields:
                                    if field not in restaurant:
                                        restaurant[field] = "Not specified"
                            
                            # Generate booking link
                                restaurant_slug = restaurant['name'].lower().replace(' ', '-').replace("'", "")
                                booking_link = f"https://opentable.com/book/{restaurant_slug}"
                                
                                # Build rich response
                                response += f"• {restaurant['name']} - {restaurant['cuisine']} cuisine\n"
                                response += f"  Rating: {restaurant['rating']}/5.0 \n"
                                response += f"  {restaurant.get('description', 'Popular local restaurant with great reviews.')}\n"
                                response += f"  Known for: {restaurant.get('signature_dish', 'Local specialties')}\n"
                                response += f"  📞 Make a reservation: {booking_link}\n\n"

                            response += f"Are you looking for any specific type of dining experience in {location}?"
                                            
                            return response
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error for restaurant data: {e}, data: {tool_data[:100]}")
                            return "I received invalid data from the restaurant search."
                        except Exception as e:
                            logger.error(f"Error parsing restaurant data: {e}")
                            return f"I found some restaurants, but I'm having trouble formatting the details."
                        # except Exception as e:
                        #     logger.error(f"Error parsing restaurant data: {e}")
                        #     return f"I found some restaurants, but I'm having trouble formatting the details. Here's the raw information: {tool_data}"
                    
                    elif tool_call["tool"] == "transport_options":
                        try:
                            options_data = json.loads(tool_data)

                            if isinstance(options_data, dict):
                                options = [options_data]  # Single transport object
                            elif isinstance(options_data, list):
                                options = options_data    # Multiple transports
                            else:
                                logger.warning(f"Unexpected flight data type: {type(options_data)}")
                                return "I couldn't process the flight search results. Would you like general information about this route instead?"
                            
                            for option in options:
                                required_fields = ['from_location', 'to_location']
                                for field in required_fields:
                                    if field not in option:
                                        option[field] = "Not specified"
                            
                            response = f"Here are transportation options from {tool_call['arguments']['from_location']} to {tool_call['arguments']['to_location']}:\n\n"

                            # for mode, details in options.items():
                            #     response += f"• By {mode}: {details['duration']} journey time - ${details['price_usd']}\n"
                            
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
        # Check if we have a very basic query with just a destination. If so, enhance it with some information to get a better response
        words = query.lower().split()

        # Default location to use if none available in context
        default_origin = "New York"

        # Check if this is a simple destination query that might be handled by LLM
        if (len(words) <= 7 and 
            ("flight" in query.lower() or "fly" in query.lower()) and 
            "to " in query.lower() and 
            "from " not in query.lower()):
            
            origin = default_origin

            # Use contextual origin if available
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

                if isinstance(result, dict) and "result" in result:
                    return result["result"]
                return result
        
        # For all other queries, proceed with normal tool selection flow
        result = asyncio.run(run_tool_query(query, context))
        logger.info(f"Final result type: {type(result)}")
        logger.info(f"Final result preview: {str(result)[:100]}")

        return result
    except Exception as e:
        logger.error(f"Error in run_async: {e}")
        return f"Sorry, I encountered an error while processing your request: {str(e)}"

if __name__ == "__main__":
    pass