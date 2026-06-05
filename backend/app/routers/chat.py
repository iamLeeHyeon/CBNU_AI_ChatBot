# ──────────────────────────────────────────────
#  app/api/chat.py
#  FastAPI 라우터 - SSE 스트리밍 응답
# ──────────────────────────────────────────────
import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest
from app.services.gemini import stream_chat_response, optimize_search_query
from app.services.tavily import search_web
from app.services.utils import extract_unique_sources
from app.services.cafeteria import is_cafeteria_query, get_today_cafeteria_menu

router = APIRouter(prefix="/api", tags=["chat"])


async def _event_stream(req: ChatRequest):
    """
    SSE 스트림 제너레이터.
    청크 타입:
      {"type": "token",   "value": "글자..."}   ← 응답 토큰
      {"type": "sources", "value": ["url", ...]} ← 출처 (스트림 끝에 1회)
      {"type": "done"}                           ← 종료 신호
      {"type": "error",   "value": "메시지"}     ← 오류
    """
    try:
        ranked_results: list = []
        sources: list[str] = []

        last_message = req.messages[-1].content

        if is_cafeteria_query(last_message):
            menu = get_today_cafeteria_menu()
            print(f"[학식 크롤링] 메뉴 조회 완료")
            ranked_results = [{"title": "충북대 학식 메뉴", "url": "", "content": menu}]
        elif req.use_search:
            raw_query = last_message
            optimized_query = await optimize_search_query(raw_query, req.messages)
            print(f"[최적화 쿼리] {optimized_query}")

            raw_results = search_web(optimized_query)
            print(f"[검색 결과 수] {len(raw_results)}")

            ranked_results = raw_results
            sources = extract_unique_sources(ranked_results)

        # 토큰 스트리밍
        async for token in stream_chat_response(req.messages, search_results=ranked_results):
            yield f"data: {json.dumps({'type': 'token', 'value': token}, ensure_ascii=False)}\n\n"

        # 출처 전송
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'value': sources}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        print(f"[스트리밍 오류] {e}")
        yield f"data: {json.dumps({'type': 'error', 'value': '죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'}, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages가 비어 있습니다.")

    return StreamingResponse(
        _event_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        },
    )
