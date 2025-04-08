# Travel Planner App

A Streamlit-based travel planning application that uses OpenAI's language models and the Managed Context Protocol (MCP) to help users plan their perfect vacation.

## Features

- **Flight Search**: Find flights between cities with customizable date ranges  
- **Hotel Recommendations**: Get hotel suggestions based on location and budget preferences  
- **Attraction Discovery**: Explore top attractions in various destinations  
- **Restaurant Finder**: Find dining options filtered by cuisine type  
- **Transportation Options**: Compare different ways to travel between locations  
- **Seasonal Travel Advice**: Get tips on the best time to visit different destinations  

## Technical Implementation

This application demonstrates the integration of:
- Streamlit for the user interface  
- OpenAI's language models for natural language understanding  
- Managed Context Protocol (MCP) for tool execution & Context-Aware Function Calling 

## Project Structure
```plaintext
project/
├── app.py            # Main application file
├── mcp_server.py     # MCP server implementation
├── mcp_client.py     # LLM Client for API connections
├── requirements.txt  # Project dependencies
└── README.md         # Project documentation
```

## Installation

1. Clone this repository
```bash
git clone https://github.com/Neeraj876/jetzy.ai.git
cd jetzy.ai
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key
```bash
export OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the MCP client in one terminal:
```bash
python mcp_client.py
```

2. In a separate terminal, start the Streamlit app:
```bash
streamlit run main.py
```

## Technologies Used

- **Python**  
- **Streamlit**  
- **OpenAI API** 
- **MCP SDK** 


## Requirements

- Python 3.8+
- streamlit
- openai
- mcp[cli]