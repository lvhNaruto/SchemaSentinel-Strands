import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NEBIUS_API_KEY")

# Initialize Nebius client
client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1",
    api_key=api_key,
)

print("Fetching available models from your Nebius account...\n")
try:
    models = client.models.list()
    print("Found models:")
    for m in models.data:
        # Print all models or filter for nvidia / llama
        print(f"- {m.id}")
except Exception as e:
    print(f"Error fetching models: {e}")