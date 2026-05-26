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

# ── 5. 학사일정 검색 ───────────────────────────────────────────────────────────
def search_academic_calendar(max_results: int = 5) -> list[dict]:
    """
    Tavily로 충북대 학사일정을 검색합니다.
    쿼리: '충북대학교 학사일정 site:cbnu.ac.kr'
    """
    client = _get_client()
    response = client.search(
        query="충북대학교 학사일정 site:cbnu.ac.kr",
        max_results=max_results,
    )
    return response.get("results", [])

# ── 6. 허용 도메인 필터링 ──────────────────────────────────────────────────────
def filter_by_allowed_domain(results: list[dict]) -> list[dict]:
    """
    검색 결과 중 robots.txt Allow 도메인에 해당하는 항목만 남깁니다.
    도메인 제한이 너무 엄격하면 전체 결과를 그대로 반환합니다.
    """
    filtered = [r for r in results if is_allowed_url(r.get("url", ""))]
    # 필터 후 결과가 없으면 원본 반환 (도메인 범위가 좁을 때 대비)
    return filtered if filtered else results

# ── 7. 결과 포맷 변환 ──────────────────────────────────────────────────────────
def format_results(results: list[dict], category: str) -> list[dict]:
    """
    Tavily 원시 결과를 title/url/content/category 형태의 dict로 변환합니다.
    category: 'notice' 또는 'academic_calendar'
    """
    formatted = []
    for r in results:
        formatted.append({
            "title": r.get("title", "제목 없음"),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "category": category,  # 공지사항인지 학사일정인지 구분
        })
    return formatted