# ──────────────────────────────────────────────
#  app/services/tavily.py
#  Tavily 웹 검색 클라이언트
# ──────────────────────────────────────────────
import os
from functools import lru_cache

from tavily import TavilyClient

from app.services.config import SEARCH_MAX_RESULTS
from app.services.utils import normalize_url  # 중복 정의 제거 → utils에서 import


@lru_cache(maxsize=1)
def _get_client() -> TavilyClient:
    """TavilyClient 싱글톤 (호출마다 재생성 방지)."""
    return TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search_web(query: str, max_results: int = SEARCH_MAX_RESULTS) -> list:
    """
    Tavily로 웹 검색 후 results 리스트를 반환.

    - sources 추출은 router에서 extract_unique_sources()로 일원화
    - 반환값을 단순화해 호출부의 혼란 제거 (튜플 → 리스트)
    """
    client = _get_client()
    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
    )
    return response.get("results", [])
