import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

PIONEER_BASE = "https://api.pioneer.ai/v1"


async def classify_relevance(text: str) -> dict:
    api_key = os.getenv("PIONEER_API_KEY", "")
    if not api_key:
        return {"relevant": True, "entities": [], "reason": "no pioneer key"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{PIONEER_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "meta-llama/Llama-3.2-3B-Instruct",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""You are a property management document classifier.

Is this document relevant to property management? Relevant means it contains info about: owners, tenants, contractors, maintenance, repairs, assembly decisions, rent, legal matters, or building issues.

Document:
{text[:1500]}

Respond with JSON only, no markdown:
{{"relevant": true, "confidence": 0.9, "reason": "contains owner and maintenance info"}}"""
                        }
                    ],
                    "max_tokens": 100,
                }
            )
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            return {
                "relevant": result.get("relevant", True),
                "entities": [],
                "reason": result.get("reason", ""),
            }
    except Exception as e:
        return {"relevant": True, "entities": [], "reason": f"fallback: {str(e)}"}


async def extract_entities(text: str) -> list[dict]:
    result = await classify_relevance(text)
    return result.get("entities", [])
