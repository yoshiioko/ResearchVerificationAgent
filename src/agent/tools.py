"""External tool integrations (Tavily web search)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tavily import TavilyClient


@dataclass(frozen=True)
class SearchResult:
    """Normalized Tavily search result used for deterministic formatting."""

    title: str
    url: str
    snippet: str


def _normalize_results(raw_results: list[dict[str, Any]]) -> list[SearchResult]:
    normalized: list[SearchResult] = []
    for item in raw_results:
        normalized.append(
            SearchResult(
                title=str(item.get("title", "(no title)")).strip() or "(no title)",
                url=str(item.get("url", "")).strip(),
                snippet=str(item.get("content", "")).strip()
                or str(item.get("snippet", "")).strip(),
            )
        )
    return normalized


def _format_results_markdown(query: str, results: list[SearchResult]) -> str:
    lines: list[str] = []
    lines.append(f"## Search Query: {query}")

    if not results:
        lines.append("- No results returned.")
        return "\n".join(lines)

    for idx, result in enumerate(results, start=1):
        lines.append(f"- [{idx}] **{result.title}**")
        lines.append(f"  - URL: {result.url or '(missing URL)'}")
        lines.append(f"  - Snippet: {result.snippet or '(empty snippet)'}")

    return "\n".join(lines)


def web_search(*, tavily_api_key: str, query: str, max_results: int = 5) -> str:
    """Run Tavily search and return compact markdown for LLM consumption.

    Returns a text payload even on failure so the agent can continue gracefully.
    """

    query = query.strip()
    if not query:
        return '## Search Query: (empty)\n- Tool error: query must not be empty.'

    try:
        client = TavilyClient(api_key=tavily_api_key)
        response = client.search(query=query, max_results=max_results)
        raw_results = response.get("results", [])
        normalized = _normalize_results(raw_results)
        return _format_results_markdown(query, normalized)
    except Exception as exc:
        return (
            f"## Search Query: {query}\n"
            f"- Tool error: Tavily search failed: {type(exc).__name__}: {exc}"
        )
