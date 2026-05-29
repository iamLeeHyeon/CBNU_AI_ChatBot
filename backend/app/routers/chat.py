from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional
from app.models.schemas import ChatRequest, ChatResponse, Course, Assignment, Grade, LMSDataResponse
from app.services.gemini import build_chat_response
from app.services.tavily import search_web
from app.services.lms_context import build_lms_context
from app.services.cafeteria import is_cafeteria_query, get_today_cafeteria_menu
from app.routers.lms import _sessions
import app.services.lms as lms_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, lms_session: Optional[str] = Cookie(default=None)):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages가 비어 있습니다.")

    context = ""
    sources: list[str] = []

    last_message = req.messages[-1].content
    if is_cafeteria_query(last_message):
        context = get_today_cafeteria_menu()
    elif req.use_search:
        context, sources = search_web(last_message)
    
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

        except Exception:
            lms_context = ""  # LMS 오류가 챗봇 전체를 막는 것을 방지
    
    reply = build_chat_response(req.messages, context, lms_context)
    return ChatResponse(reply=reply, sources=sources)
