import asyncio
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Cookie
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, Course, Assignment, Grade, LMSDataResponse
from app.services.gemini import stream_chat_response, evaluate_and_rank_results, optimize_search_query
from app.services.tavily import search_web
from app.services.utils import extract_unique_sources
from app.services.lms_context import build_lms_context
from app.routers.lms import _sessions
import app.services.lms as lms_service

router = APIRouter(prefix="/api", tags=["chat"])

async def _event_stream(req: ChatRequest, lms_context: str):
    """SSE 스트림 제너레이터 (LMS 데이터 + 웹 검색 병합)"""
    try:
        ranked_results: list = []
        sources: list[str] = []

        if req.use_search:
            raw_query = req.messages[-1].content
            optimized_query = await optimize_search_query(raw_query, req.messages)
            print(f"[최적화 쿼리] {optimized_query}")

            raw_results = search_web(optimized_query)
            print(f"[검색 결과 수] {len(raw_results)}")

            ranked_results = evaluate_and_rank_results(raw_query, raw_results)
            sources = extract_unique_sources(ranked_results)

        # 토큰 스트리밍 (lms_context를 Gemini로 전달)
        async for token in stream_chat_response(req.messages, search_results=ranked_results, lms_context=lms_context):
            yield f"data: {json.dumps({'type': 'token', 'value': token}, ensure_ascii=False)}\n\n"

        # 출처 전송
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'value': sources}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        print(f"[스트리밍 오류] {e}")
        yield f"data: {json.dumps({'type': 'error', 'value': '죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'}, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(req: ChatRequest, lms_session: Optional[str] = Cookie(default=None)):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages가 비어 있습니다.")

    lms_context = ""
    if lms_session and lms_session in _sessions:
        try:
            token   = _sessions[lms_session]["token"]
            user_id = _sessions[lms_session]["user_id"]

            raw_courses = lms_service.get_courses(token)
            courses     = [Course(**c) for c in raw_courses]
            course_ids  = [c.id for c in courses]

            raw_assigns = lms_service.get_assignments(token, course_ids)
            if raw_assigns:
                assign_ids    = [a["id"] for a in raw_assigns]
                submitted_map = lms_service.get_submission_statuses(token, assign_ids)
                for a in raw_assigns:
                    a["submitted"] = submitted_map.get(a["id"], False)
            assignments = [Assignment(**a) for a in raw_assigns]

            raw_grades  = lms_service.get_grades(token, user_id) if user_id else []
            grades      = [Grade(**g) for g in raw_grades]

            lms_data    = LMSDataResponse(courses=courses, assignments=assignments, grades=grades)
            lms_context = build_lms_context(lms_data)

        except Exception as e:
            print(f"LMS Context 로드 실패: {e}")
            lms_context = ""  # LMS 오류가 챗봇 전체를 막는 것을 방지

    return StreamingResponse(
        _event_stream(req, lms_context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        },
    )