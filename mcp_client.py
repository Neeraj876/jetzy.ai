import os
import json
import asyncio
import streamlit as st
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv
load_dotenv()

server_params = StdioServerParameters(command="python", args=["mcp_server.py"])

def llm_client(message:str):
    """
    Send a message to the LLM and return the response.
    """
    # Initialize the OpenAI client
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Send the message to the LLM
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"system",
                    "content":"You are an intelligent assistant. You will execute tasks as prompted",
                    "role": "user", "content": message}],
        temperature=0.7,
        max_tokens=1000,
        top_p=0.9,
        frequency_penalty=0.2,
        presence_penalty=0.3
    )

    # Extract and return the response content
    return response.choices[0].message.content.strip()

def get_prompt_to_identify_tool_and_arguments(query,tools):
    tools_description = "\n".join([f"- {tool.name}, {tool.description}, {tool.inputSchema} " for tool in tools])
    return  ("You are a helpful assistant with access to these tools:\n\n"
                f"{tools_description}\n"
                "Choose the appropriate tool based on the user's question. \n"
                f"User's Question: {query}\n"                
                "If no tool is needed, reply directly.\n\n"
                "IMPORTANT: When you need to use a tool, you must ONLY respond with "                
                "the exact JSON object format below, nothing else:\n"
                "Keep the values in str "
                "{\n"
                '    "tool": "tool-name",\n'
                '    "arguments": {\n'
                '        "argument-name": "value"\n'
                "    }\n"
                "}\n\n")


async def run_tool_query(query: str):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read,write) as session:

            await session.initialize()

            # Get the list of available tools
            tools = await session.list_tools()

            print(f"Available tools: {tools}")

            prompt = get_prompt_to_identify_tool_and_arguments(query,tools.tools)

            llm_response = llm_client(prompt)
            print(f"LLM Response: {llm_response}")

            try:
                tool_call = json.loads(llm_response)

                if not isinstance(tool_call, dict):
                        raise ValueError("LLM response is not a dictionary after JSON parsing")

                result = await session.call_tool(tool_call["tool"], arguments=tool_call["arguments"])

                print(f"the result is, {result.content[0].text}")

                return {
                    "tool": tool_call["tool"],
                    "arguments": tool_call["arguments"],
                    "result": result.content[0].text
                }
            
            except Exception as e:
                return {"error": str(e), "response": llm_response}

            # tool_call = json.loads(llm_response)

            # result = await session.call_tool(tool_call["tool"], arguments=tool_call["arguments"])

            # print(f"BMI for weight {tool_call["arguments"]["weight_kg"]}kg and height {tool_call["arguments"]["height_m"]}m is {result.content[0].text}")


# Main function to run asyncio event loop
def run_async(query):
    return asyncio.run(run_tool_query(query))

if __name__ == "__main__":
    pass
           