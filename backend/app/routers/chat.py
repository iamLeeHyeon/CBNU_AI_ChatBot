from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional
from app.models.schemas import ChatRequest, ChatResponse
from app.services.gemini import build_chat_response
from app.services.tavily import search_web
from app.services.cafeteria import is_cafeteria_query, get_today_cafeteria_menu
from app.services.lms_context import build_lms_context
from app.routers.lms import _sessions

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
            lms_context = build_lms_context(_sessions[lms_session]["data"])
        except Exception:
            lms_context = ""

    reply = build_chat_response(req.messages, context, lms_context)
    return ChatResponse(reply=reply, sources=sources)
