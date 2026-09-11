import os
from typing import Dict, Any, List
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class DocumentationResearcher:
    """Uses Tavily to query developer documentation and migration guides on the live web."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("Missing TAVILY_API_KEY. Please set it in your .env file.")
        self.client = TavilyClient(api_key=self.api_key)

    def search_schema_changelog(self, mutated_keys: List[str]) -> Dict[str, Any]:
        search_query = f"JSON schema mapping guide fields {' '.join(mutated_keys)}"
        try:
            response = self.client.search(
                query=search_query,
                search_depth="basic",
                max_results=2,
            )
            snippets = [r.get("content", "") for r in response.get("results", [])]
            sources = [{"title": r.get("title"), "url": r.get("url")} for r in response.get("results", [])]

            return {
                "summary": "\n\n".join(snippets) if snippets else "No external documentation found.",
                "sources": sources,
                "status": "success",
            }
        except Exception as e:
            return {
                "summary": f"Tavily search error: {str(e)}",
                "sources": [],
                "status": "error",
            }