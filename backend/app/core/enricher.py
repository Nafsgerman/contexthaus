import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


_AD_KEYWORDS = {"anrufen", "inserieren", "makler", "kaufen", "mieten"}


def _is_clean(snippet: str) -> bool:
    lower = snippet.lower()
    return not any(kw in lower for kw in _AD_KEYWORDS)


async def enrich_property(address: str, property_name: str) -> str:
    """Search public records for property/contractor info."""
    try:
        result = _client.search(
            query=f"{address} Berlin Hausverwaltung Gebäudedaten",
            max_results=2,
            search_depth="basic",
        )
        snippets = [
            r.get("content", "")
            for r in result.get("results", [])
            if _is_clean(r.get("content", ""))
        ]
        combined = "\n".join(snippets[:2])
        return combined[:300]
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