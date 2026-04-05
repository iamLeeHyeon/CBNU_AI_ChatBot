import os
import google.generativeai as genai
from typing import List
from app.models.schemas import Message

SYSTEM_PROMPT = """당신은 충북대학교(CBNU) 전용 AI 챗봇입니다.
학생, 교직원, 방문자에게 충북대학교에 관한 정확하고 친절한 정보를 제공합니다.
모르는 내용은 솔직히 모른다고 답하고, 공식 홈페이지(https://www.chungbuk.ac.kr) 확인을 안내하세요.
항상 한국어로 답변하세요."""


def build_chat_response(messages: List[Message], context: str = "") -> str:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )

    history = []
    for msg in messages[:-1]:
        history.append({
            "role": "user" if msg.role == "user" else "model",
            "parts": [msg.content],
        })

    chat = model.start_chat(history=history)

    last_content = messages[-1].content
    if context:
        last_content = f"[참고 자료]\n{context}\n\n[질문]\n{last_content}"

    response = chat.send_message(last_content)
    return response.text
