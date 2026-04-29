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