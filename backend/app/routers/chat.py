from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.gemini import build_chat_response, optimize_search_query, preprocess_context, evaluate_and_rank_results
from app.services.tavily import search_web, normalize_url

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    if not req.messages:
        raise HTTPException(status_code=400, detail="messages가 비어 있습니다.")

    search_results: list = []
    sources: list[str] = []

    if req.use_search:
        query = req.messages[-1].content
        optimized_query = await optimize_search_query(query, req.messages)
        print(f"[최적화 쿼리] {optimized_query}")
        
        search_results, sources = search_web(query)
        print(f"[검색 결과 수] {len(search_results)}")          
        print(f"[검색 결과 내용] {search_results[:1]}")          
        print(f"[use_search 값] {req.use_search}")   

        #  필터링/중복제거 후 남은 결과에서 sources 추출
        ranked_results = evaluate_and_rank_results(query, search_results)

        #  URL 정규화 기반 중복 제거해서 sources 추출
        seen_urls = set()
        sources = []    

        for r in ranked_results:
            url = r.get("url", "")
            combined = (r.get("title", "") + r.get("content", "") + url).lower()
            if not any(kw in combined for kw in ["충북대", "chungbuk", "cbnu"]):
                continue
            norm = normalize_url(url)
            if norm in seen_urls:
                continue
            seen_urls.add(norm)
            sources.append(url)

        sources = [
            r["url"] for r in ranked_results
            if any(kw in (r.get("title","") + r.get("content","") + r.get("url","")).lower()
                   for kw in ["충북대", "chungbuk", "cbnu"])
        ]

    reply = build_chat_response(req.messages, search_results=search_results)
    return ChatResponse(reply=reply, sources=sources)
