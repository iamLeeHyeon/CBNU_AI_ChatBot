import os
import google.generativeai as genai
from typing import List
from app.models.schemas import Message
from datetime import datetime

SYSTEM_PROMPT = """당신은 충북대학교(CBNU) 전용 AI 챗봇입니다.
학생, 교직원, 방문자에게 충북대학교에 관한 정확하고 친절한 정보를 제공합니다.
모르는 내용은 솔직히 모른다고 답하고, 공식 홈페이지(https://www.chungbuk.ac.kr) 확인을 안내하세요.
항상 한국어로 답변하세요."""


def build_chat_response(messages: List[Message], context: str = "") -> str:

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dynamic_prompt = f"{SYSTEM_PROMPT}\n\n[시스템 정보]\n현재 일시: {now}"

    generation_config = {
    "temperature": 0.2,    # 낮을수록 정확하고 일관된 답변 (0.0 ~ 2.0), 대답이 너무 일관적인 경우 상향조정
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 1024, # 답변 길이 제한
    }

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=dynamic_prompt,
        generation_config = generation_config,
    )

    # 2. 히스토리 요약 로직 추가
    # 대화 내역이 너무 길어지면(예: 15개 이상) 앞부분을 요약하여 전달
    if len(messages) > 15:
        summary_prompt = "다음은 이전까지의 대화 내용입니다. 핵심 내용을 3줄 이내로 요약하세요:\n"
        past_content = "\n".join([f"{m.role}: {m.content}" for m in messages[:-10]])

        # 별도 호출로 요약본 생성
        summary_response = model.generate_content(summary_prompt + past_content)
        if summary_response.text:
            summary_text = f"[이전 대화 요약]: {summary_response.text}"
        else:
            summary_text = "[이전 대화 내용 생략]"
	            
        # 요약본을 첫 번째 히스토리로 넣고, 최근 10개만 유지
        history = [{"role": "user", "parts": [summary_text]}]
        history.extend([
            {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
            for m in messages[-10:-1]
        ])
        


    try:
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
    
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return "죄송합니다. 현재 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요."
