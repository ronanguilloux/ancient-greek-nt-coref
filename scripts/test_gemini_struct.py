import os
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

load_dotenv()

class ProDropResolution(BaseModel):
    resolved_entity: str
    confidence: str

client = genai.Client()

response = client.models.generate_content(
    model='gemini-3.1-pro-preview',
    contents="Translate 'hello' to French and give confidence.",
    config={
        'response_mime_type': 'application/json',
        'response_schema': ProDropResolution,
    },
)

print(response.text)
