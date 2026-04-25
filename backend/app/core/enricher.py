import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

_RELEVANT = {"hausverwaltung", "verwalter", "weg", "eigentümergemeinschaft", "verwaltungsbeirat"}
_SPAM = {"inserieren", "makler", "kaufen", "anrufen", "barrierefrei", "denkmal", "qm"}


async def enrich_property(address: str, property_name: str) -> str:
    """Return first relevant property management snippet, or empty string."""
    if not os.getenv("TAVILY_API_KEY"):
        return ""
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        result = client.search(
            query=f"WEG Hausverwaltung {address} Kontakt Verwalter",
            max_results=3,
            search_depth="basic",
        )
        for r in result.get("results", []):
            snippet = r.get("content", "")
            lower = snippet.lower()
            if any(kw in lower for kw in _SPAM):
                continue
            if any(kw in lower for kw in _RELEVANT):
                return snippet[:200]
        return ""
    except Exception:
        return ""


async def enrich_contractor(contractor_name: str) -> str:
    """Look up contractor contact details."""
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
        result = client.search(
            query=f"{contractor_name} Berlin Kontakt Telefon",
            max_results=2,
            search_depth="basic",
        )
        snippets = [r.get("content", "") for r in result.get("results", [])]
        return "\n".join(snippets[:2])
    except Exception:
        return ""
