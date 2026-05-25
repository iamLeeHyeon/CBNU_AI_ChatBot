# ──────────────────────────────────────────────
#  app/api/router.py
#  FastAPI 라우터: 요청 수신 → 서비스 호출 → 응답
#  (비즈니스 로직 없는 얇은 컨트롤러)
# ──────────────────────────────────────────────
from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.gemini import build_chat_response, evaluate_and_rank_results, optimize_search_query
from app.services.tavily import search_web
from app.services.utils import extract_unique_sources

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages가 비어 있습니다.")

    ranked_results: list = []
    sources: list[str] = []

    if req.use_search:
        raw_query = req.messages[-1].content
        optimized_query = await optimize_search_query(raw_query, req.messages)
        print(f"[최적화 쿼리] {optimized_query}")

        raw_results = search_web(optimized_query)
        print(f"[검색 결과 수] {len(raw_results)}")
        print(f"[검색 결과 샘플] {raw_results[:1]}")

        ranked_results = evaluate_and_rank_results(raw_query, raw_results)
        sources = extract_unique_sources(ranked_results)  # utils에서 일원화된 중복 제거

    reply = build_chat_response(req.messages, search_results=ranked_results)
    return ChatResponse(reply=reply, sources=sources)
