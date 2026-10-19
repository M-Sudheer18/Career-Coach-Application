import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")

print("Key loaded:", bool(api_key))
print("Key prefix:", api_key[:3] if api_key else "NONE")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Reply with exactly: Gemini API works"
)

print(response.text)