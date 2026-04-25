import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

FLASH = "gemini-2.5-flash"
PRO   = "gemini-2.5-pro"

async def generate(prompt: str, system: str = "", model: str = FLASH, temperature: float = 0.2) -> str:
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system or None,
    )
    response = _client.models.generate_content(model=model, contents=prompt, config=config)
    return response.text

async def generate_json(prompt: str, system: str = "", model: str = FLASH) -> str:
    config = types.GenerateContentConfig(
        temperature=0.1,
        system_instruction=system or None,
        response_mime_type="application/json",
    )
    response = _client.models.generate_content(model=model, contents=prompt, config=config)
    return response.text
