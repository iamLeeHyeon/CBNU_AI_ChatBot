# ──────────────────────────────────────────────
#  app/services/utils.py
#  공통 유틸: URL 정규화 · 검색 결과 전처리
#  (gemini.py / tavily.py 중복 제거)
# ──────────────────────────────────────────────
from urllib.parse import urlparse, urlunparse
from app.services.config import CBNU_KEYWORDS, DEFAULT_URL_PATTERNS, SEARCH_CONTEXT_MAX_CHARS


def normalize_url(url: str) -> str:
    """URL을 정규화해 중복 비교에 사용할 표준 형태로 반환."""
    parsed = urlparse(url.lower().strip())
    host = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip("/")

    if path in DEFAULT_URL_PATTERNS:
        path = ""
    else:
        for pattern in DEFAULT_URL_PATTERNS:
            if path.endswith(pattern):
                path = path[: -len(pattern)]
                break

    path = path.strip("/")
    if path:
        path = "/" + path

    return urlunparse((parsed.scheme, host, path, "", "", ""))


def is_cbnu_related(title: str, content: str, url: str) -> bool:
    """제목·본문·URL 중 하나라도 충북대 키워드를 포함하면 True."""
    combined = (title + content + url).lower()
    return any(kw in combined for kw in CBNU_KEYWORDS)


def preprocess_context(
    raw_results: list,
    max_chars_per_result: int = SEARCH_CONTEXT_MAX_CHARS,
) -> str:
    """
    검색 결과를 Gemini 프롬프트용 텍스트로 변환.
    - 충북대 무관 결과 필터링
    - URL·내용 중복 제거
    - 본문 길이 제한
    """
    if not raw_results:
        return ""

    seen_urls: set[str] = set()
    seen_contents: set[str] = set()
    processed: list[str] = []

    for i, result in enumerate(raw_results):
        title = result.get("title", "제목 없음")
        url = result.get("url", "")
        content = result.get("content", "").strip()
        date = result.get("published_date", "")
        date_str = f" ({date})" if date else ""

        # 충북대 무관 결과 제외
        if not is_cbnu_related(title, content, url):
            print(f"[필터링] 충북대 무관 결과 제외: {title}")
            continue

        # URL 중복 제거
        norm_url = normalize_url(url)
        if norm_url in seen_urls:
            print(f"[URL 중복 제거] {url}")
            continue
        seen_urls.add(norm_url)

        # 내용 중복 제거
        content_key = content[:50]
        if content_key in seen_contents:
            continue
        seen_contents.add(content_key)

        # 길이 제한
        if len(content) > max_chars_per_result:
            content = content[:max_chars_per_result] + "..."

        processed.append(
            f"[출처 {i + 1}] {title}{date_str}\n"
            f"URL: {url}\n"
            f"{content}"
        )

    return "\n\n---\n\n".join(processed)


def extract_unique_sources(results: list) -> list[str]:
    """
    결과 리스트에서 충북대 관련 URL만 중복 없이 추출.
    router와 gemini 양쪽에서 공유.
    """
    seen_urls: set[str] = set()
    sources: list[str] = []

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        content = r.get("content", "")

        if not is_cbnu_related(title, content, url):
            continue

        norm = normalize_url(url)
        if norm in seen_urls:
            continue

        seen_urls.add(norm)
        sources.append(url)

    return sources
