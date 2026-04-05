from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.gemini import build_chat_response
from app.services.tavily import search_web

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages가 비어 있습니다.")

    context = ""
    sources: list[str] = []

    if req.use_search:
        query = req.messages[-1].content
        context, sources = search_web(query)

    reply = build_chat_response(req.messages, context)
    return ChatResponse(reply=reply, sources=sources)
