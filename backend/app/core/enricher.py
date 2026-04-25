import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


async def enrich_property(address: str, property_name: str) -> str:
    """Search public records for property/contractor info."""
    try:
        result = _client.search(
            query=f"Hausverwaltung {address} Berlin Eigentümer Kontakt",
            max_results=3,
            search_depth="basic",
        )
        snippets = [r.get("content", "") for r in result.get("results", [])]
        return "\n".join(snippets[:3])
    except Exception:
        return ""


async def enrich_contractor(contractor_name: str) -> str:
    """Look up contractor contact details."""
    try:
        result = _client.search(
            query=f"{contractor_name} Berlin Kontakt Telefon",
            max_results=2,
            search_depth="basic",
        )
        snippets = [r.get("content", "") for r in result.get("results", [])]
        return "\n".join(snippets[:2])
    except Exception:
        return ""