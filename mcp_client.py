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

# def llm_client(message: str):
#     """
#     Send a message to the LLM and return the response.
#     """
#     try:

#         logger.info("Sending request to OpenAI API")

#         # Initialize the OpenAI client
#         openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
#         # Send the message to the LLM
#         response = openai_client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are an intelligent assistant. You will execute tasks as prompted"},
#                 {"role": "user", "content": message}
#             ],
#             temperature=0.7,
#             max_tokens=1000,
#             top_p=0.9,
#             frequency_penalty=0.2,
#             presence_penalty=0.3
#         )
        
#         # Extract and return the response content
#         content = response.choices[0].message.content 

#         logger.info(f"Received response from LLM: {content[:100]}...")  

#         return content
#     except Exception as e:
#         logger.error(f"Error in LLM client: {e}")
#         return f"Error communicating with AI service: {str(e)}"
    
def llm_client(message: str):
    """Simulated LLM response function that doesn't use OpenAI API"""
    try:
        logger.info("Using simulated LLM response")
        # Extract the user query from the prompt
        query = message.split("User's Question: ")[1].split("\n")[0] if "User's Question: " in message else message
        
        # Generate a simulated response based on keywords
        if "flight" in query.lower():
            return '{"tool": "search_flights", "arguments": {"from_location": "New York", "to_location": "Paris", "date_range": "2025-05-01 to 2025-05-14"}}'
        elif "hotel" in query.lower():
            return '{"tool": "recommend_hotels", "arguments": {"location": "Rome", "budget": "medium"}}'
        elif "attraction" in query.lower() or "to do" in query.lower():
            return '{"tool": "recommend_attractions", "arguments": {"location": "Tokyo"}}'
        elif "restaurant" in query.lower():
            return '{"tool": "recommend_restaurants", "arguments": {"location": "Paris", "cuisine": "any"}}'
        elif "transport" in query.lower():
            return '{"tool": "transport_options", "arguments": {"from_location": "Paris", "to_location": "Nice"}}'
        else:
            # Default response
            return "I'm your travel assistant. I can help with flights, hotels, attractions, restaurants, and transportation. How can I assist with your travel plans?"
    except Exception as e:
        logger.error(f"Error in simulated LLM: {e}")
        return f"Error generating response: {str(e)}"

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
                    
                    # Format result data into a user-friendly response
                    tool_data = result.content[0].text
                    
                    # Format response based on the tool type
                    if tool_call["tool"] == "search_flights":
                        try:
                            flights = json.loads(tool_data)
                            response = f"I found these flights from {tool_call['arguments']['from_location']} to {tool_call['arguments']['to_location']}:\n\n"
                            for flight in flights:
                                response += f"• {flight['airline']}: ${flight['price_usd']} - Departs {flight['departure_date']}, Returns {flight['return_date']}\n"
                            return response
                        except:
                            return tool_data
                    elif tool_call["tool"] == "recommend_hotels":
                        try:
                            hotels = json.loads(tool_data)
                            response = f"Here are some recommended hotels in {tool_call['arguments']['location']}:\n\n"
                            for hotel in hotels:
                                response += f"• {hotel['name']}: ${hotel['price_per_night_usd']} per night - Rating: {hotel['rating']}/5.0\n"
                            return response
                        except:
                            return tool_data
                    else:
                        # For other tools, return the raw response
                        return tool_data
                    
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
        if isinstance(result, dict) and "result" in result:
            return result["result"]
        return result
    except Exception as e:
        return f"Sorry, I encountered an error while processing your request: {str(e)}"

if __name__ == "__main__":
    pass