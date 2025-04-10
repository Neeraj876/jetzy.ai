import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("API key (first 5 chars):", os.getenv("OPENAI_API_KEY")[:5] if os.getenv("OPENAI_API_KEY") else "Not found")

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("API is working:", response.choices[0].message.content)
except Exception as e:
    print("API error:", e)