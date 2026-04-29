import os
from tavily import TavilyClient

# ── 1. 허용 도메인 상수 ────────────────────────────────────────────────────────
# robots.txt에서 Allow된 충북대 페이지만 결과에 포함시킵니다.
ALLOWED_DOMAINS = [
    "https://www.cbnu.ac.kr/www/index.do",
    "https://www.cbnu.ac.kr/service/index.do",
    "https://www.cbnu.ac.kr",
]

# ── 2. URL 허용 여부 검사 ──────────────────────────────────────────────────────
def is_allowed_url(url: str) -> bool:
    """URL이 robots.txt Allow 목록 도메인에 속하는지 확인합니다."""
    return any(url.startswith(domain) for domain in ALLOWED_DOMAINS)

# ── 3. Tavily 클라이언트 생성 ──────────────────────────────────────────────────
def _get_client() -> TavilyClient:
    """환경변수에서 API 키를 읽어 Tavily 클라이언트를 반환합니다."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY 환경변수가 설정되지 않았습니다.")
    return TavilyClient(api_key=api_key)

# ── 4. 공지사항 검색 ───────────────────────────────────────────────────────────
def search_notices(max_results: int = 5) -> list[dict]:
    """
    Tavily로 충북대 공지사항을 검색합니다.
    쿼리: '충북대학교 공지사항 site:cbnu.ac.kr'
    """
    client = _get_client()
    response = client.search(
        query="충북대학교 공지사항 site:cbnu.ac.kr",
        max_results=max_results,
    )
    # 검색 결과 리스트 추출 (없으면 빈 리스트)
    return response.get("results", [])
