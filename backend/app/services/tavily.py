import os
from tavily import TavilyClient
from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    parsed = urlparse(url.lower().strip())
    host = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip("/")
    
    # 기본 페이지 경로 패턴 제거 (index.do, /www/index.do 등)
    default_paths = (
        "/index.do", "/index.html", "/index.php", "/main.do",
        "/www/index.do", "/www/index.html", "/www/main.do", "/www",
    )
    if path in default_paths or path.endswith(default_paths):
        path = ""

    return urlunparse((parsed.scheme, host, path, "", "", ""))

def search_web(query: str, max_results: int = 3) -> tuple[str, list[str]]:
    """Tavily로 웹 검색 후 (컨텍스트 문자열, 출처 URL 리스트) 반환."""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    optimized_query = f"충북대학교(CBNU) 공식 홈페이지 {query}"

    response = client.search(query=optimized_query, 
                             max_results=max_results,
                             search_depth="advanced")

    results = response.get("results", [])
    context = "\n\n".join(
        f"[{r['title']}]\n{r['content']}" for r in results
    )
    sources = [r["url"] for r in results]
    return context, sources
