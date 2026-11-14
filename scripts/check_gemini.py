import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Initialize Gemini client
client = genai.Client(
    api_key=api_key,
    http_options={"timeout": 20000}
)

print(f"Testing Gemini model: {model}", flush=True)

try:
    response = client.interactions.create(
        model=model,
        input="Say hello to the ResLink AI team!"
    )

    print("Response received!")
    print(response.output_text)

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

finally:
    client.close()