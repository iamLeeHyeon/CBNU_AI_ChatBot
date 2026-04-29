import os
from tavily import TavilyClient

# ── 1. 허용 도메인 상수 ────────────────────────────────────────────────────────
# robots.txt에서 Allow된 충북대 페이지만 결과에 포함시킵니다.
ALLOWED_DOMAINS = [
    "https://www.cbnu.ac.kr/www/index.do",
    "https://www.cbnu.ac.kr/service/index.do",
    "https://www.cbnu.ac.kr",
]
