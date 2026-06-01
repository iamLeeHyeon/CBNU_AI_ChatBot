from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional
from datetime import datetime
from app.models.schemas import ChatRequest, ChatResponse
from app.services.gemini import build_chat_response
from app.services.tavily import search_web
from app.services.cafeteria import is_cafeteria_query, get_today_cafeteria_menu
from app.routers.lms import _sessions

router = APIRouter(prefix="/api", tags=["chat"])


def _build_lms_context(data: dict) -> str:
    sections = []

    courses = data.get("courses", [])
    if courses:
        names = ", ".join(c["name"] for c in courses)
        sections.append(f"수강 중인 과목: {names}")

    now = datetime.now()
    upcoming = []
    for a in data.get("assignments", []):
        if a.get("submitted"):
            continue
        due_str = a.get("due_date", "")
        if not due_str:
            continue
        try:
            due = datetime.strptime(due_str.strip(), "%Y-%m-%d %H:%M")
            diff_days = (due - now).total_seconds() / 86400
            if 0 <= diff_days <= 7:
                d_label = "D-DAY" if diff_days < 1 else f"D-{int(diff_days)}"
                upcoming.append((diff_days, f"  - [{a['course_name']}] {a['title']} ({d_label})"))
        except ValueError:
            pass
    upcoming.sort(key=lambda x: x[0])
    if upcoming:
        sections.append("이번 주 마감 과제 (미제출):\n" + "\n".join(t for _, t in upcoming))

    if not sections:
        return ""
    return "[현재 학생 LMS 정보]\n" + "\n\n".join(sections)


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
            lms_context = _build_lms_context(_sessions[lms_session]["data"])
        except Exception:
            lms_context = ""

    reply = build_chat_response(req.messages, context, lms_context)
    return ChatResponse(reply=reply, sources=sources)
