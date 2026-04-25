import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


_SPAM_KEYWORDS = {"inserieren", "makler", "kaufen", "wohnung", "anrufen", "qm", "zimmer"}
_RELEVANT_KEYWORDS = {"hausverwaltung", "verwaltung", "eigentümer", "weg", "gebäude", "kontakt"}


def _is_relevant(snippet: str) -> bool:
    lower = snippet.lower()
    if any(kw in lower for kw in _SPAM_KEYWORDS):
        return False
    return any(kw in lower for kw in _RELEVANT_KEYWORDS)


async def enrich_property(address: str, property_name: str) -> str:
    """Search public records for property management info."""
    try:
        result = _client.search(
            query=f"Hausverwaltung Kontakt {address}",
            max_results=2,
            search_depth="basic",
        )
        snippets = [
            r.get("content", "")
            for r in result.get("results", [])
            if _is_relevant(r.get("content", ""))
        ]
        if not snippets:
            return ""
        return "\n".join(snippets[:2])[:150]
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