from pydantic import BaseModel
from typing import List


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    use_search: bool = False


class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []
