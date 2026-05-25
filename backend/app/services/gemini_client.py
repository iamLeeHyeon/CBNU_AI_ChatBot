# ──────────────────────────────────────────────
#  app/services/gemini_client.py
#  Gemini 클라이언트 싱글톤
#  (매 함수마다 genai.configure() 중복 호출 제거)
# ──────────────────────────────────────────────
import os
import google.generativeai as genai
from app.services.config import GEMINI_MODEL


def get_model(generation_config: dict, system_instruction: str = "") -> genai.GenerativeModel:
    """
    genai를 초기화하고 GenerativeModel을 반환.
    - API 키 설정은 이 함수에서만 수행
    - system_instruction이 없으면 생략
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    kwargs = {
        "model_name": GEMINI_MODEL,
        "generation_config": generation_config,
    }
    if system_instruction:
        kwargs["system_instruction"] = system_instruction

    return genai.GenerativeModel(**kwargs)
