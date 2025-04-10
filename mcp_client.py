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

def llm_client(message: str):
    """
    Send a message to the LLM and return the response.
    """
    try:

        logger.info("Sending request to OpenAI API")

        # Initialize the OpenAI client
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Send the message to the LLM
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a knowledgeable travel assistant with expertise in flight information. When sharing flight information, write in a natural, conversational style. Include: \n - Common departure airports for the origin city \n - Typical price ranges and popular airlines for this route \n - If specific flight data is available, highlight the best deals with exact dates and prices \n - Always offer to help with related travel needs (hotels, attractions, etc.) Format your response as if you're a helpful travel agent having a conversation, not just listing data. Do not say you are an AI or language model. Just sound like a real assistant."
                },
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
    
def get_prompt_to_identify_tool_and_arguments(query, tools):
    tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
    return (
        "You are a helpful travel assistant with access to these tools:\n\n"
        f"{tools_description}\n\n"
        "Choose the appropriate tool based on the user's question and extract all necessary parameters.\n"
        f"User's Question: {query}\n\n"
        "If no tool is needed, reply directly with a helpful travel-related answer.\n\n"
        "IMPORTANT: When you need to use a tool, you must ONLY respond with "
        "the exact JSON object format below, nothing else:\n"
        "{\n"
        '    "tool": "tool-name",\n'
        '    "arguments": {\n'
        '        "argument-name": "value"\n'
        "    }\n"
        "}\n\n"
        "Format requirements:\n"
        "- For dates, use YYYY-MM-DD format\n"
        "- City names should be full names (e.g., 'New York' not 'NY')\n"
        "- For date ranges, use the format 'YYYY-MM-DD to YYYY-MM-DD'"
    )

async def run_tool_query(query: str):
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Get the list of available tools
                tools = await session.list_tools()
                
                prompt = get_prompt_to_identify_tool_and_arguments(query, tools.tools)
                llm_response = llm_client(prompt)
                
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

                            # Check if the result is a list or a single object
                            if isinstance(flights_data, list):
                                flights = flights_data
                            else:
                                # If it's a single flight object, put it in a list
                                flights = [flights_data]

                            response = f"I found these flights from {tool_call['arguments']['from_location']} to {tool_call['arguments']['to_location']}:\n\n"
                            for flight in flights:
                                response += f"• {flight['airline']}: ${flight['price_usd']} - Departs {flight['departure_date']}, Returns {flight['return_date']}\n"
                                response += "\n Would you like me to help you find hotels at your destination?"

                            return response
                        except:
                            return "⚠️ Sorry, I couldn’t handle that request right now."
                    elif tool_call["tool"] == "recommend_hotels":
                        try:
                            hotels = json.loads(tool_data)
                            response = f"Here are some recommended hotels in {tool_call['arguments']['location']}:\n\n"
                            for hotel in hotels:
                                response += f"• {hotel['name']}: ${hotel['price_per_night_usd']} per night - Rating: {hotel['rating']}/5.0\n"
                            return response
                        except:
                            return "⚠️ Sorry, I couldn’t handle that request right now."
                    elif tool_call["tool"] == "recommend_attractions":
                        try:
                            attractions = json.loads(tool_data)
                            response = f"Here are some popular attractions in {tool_call['arguments']['location']}:\n\n"
                            for attraction in attractions:
                                response += f"• {attraction['name']}: {attraction['description']}\n"
                            
                            response += "\nWould you like restaurant recommendations as well?"
                            return response
                        except Exception as e:
                            logger.error(f"Error parsing attraction data: {e}")
                            return f"I found some attractions, but I'm having trouble formatting the details. Here's the raw information: {tool_data}"
                    
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

def run_async(query):
    """
    Run the asyncio event loop to process the query.
    Returns a string response suitable for displaying to the user.
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