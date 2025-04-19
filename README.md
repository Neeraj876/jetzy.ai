# Travel Planner App

The Jetzy Travel AI ChatBot will serve as an intelligent conversational travel assistant using ChatGPT API. 

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
- OpenAI's language models for understanding user query and dynamic response generation
- Managed Context Protocol (MCP) for tool execution & Context-Aware Function Calling 

## Installation

1. Clone this repository
```bash
git clone https://github.com/curriculo-tech/jetzy
cd jetzy
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key

To securely store your OpenAI API key, use a `.env` file in the root directory of your project.

```ini
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run main.py
```

## Technologies Used

- **Python**  
- **Streamlit**  
- **OpenAI API** 
- **MCP SDK**
- **NGINX**
- **GitHub Actions**

## Requirements

- Python 3.8+
- streamlit
- openai
- mcp[cli]
- python-dotenv
