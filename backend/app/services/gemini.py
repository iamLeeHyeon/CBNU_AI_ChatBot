import os
import time
import google.generativeai as genai
from typing import List
from app.models.schemas import Message
from datetime import datetime
from urllib.parse import urlparse, urlunparse

SYSTEM_PROMPT = """당신은 충북대학교(CBNU) 전용 AI 챗봇입니다.
학생, 교직원, 방문자에게 충북대학교에 관한 정확하고 친절한 정보를 제공합니다.

[답변 원칙]
1. 반드시 제공된 [참고 자료]를 우선 근거로 삼아 답변하세요.
2. 참고 자료만으로 답변이 불충분할 경우, 학습된 지식을 보조적으로 활용하되 "공식 확인 필요" 라고 명시하세요.
3. 참고 자료에 없는 내용은 솔직히 모른다고 하고, 공식 홈페이지(https://www.chungbuk.ac.kr) 확인을 안내하세요.
4. 오래된 정보(6개월 이상)는 변경 가능성을 언급하세요.

[답변 형식]
- 핵심 내용을 먼저 제시하고, 세부 내용을 뒤에 서술하세요 (두괄식).
- 단계적 설명이 필요한 경우 번호 목록을 활용하세요.
- 불필요한 반복이나 중언부언을 피하고 간결하게 작성하세요.
- 항상 한국어로 답변하세요.

[사고 과정]
답변 생성 전 내부적으로 다음을 수행하세요:
1. 질문의 핵심 의도 파악
2. 참고 자료에서 관련 정보 추출
3. 정보의 최신성 및 신뢰도 판단
4. 위 과정을 바탕으로 최종 답변 구성

"""
def normalize_url(url: str) -> str:
    parsed = urlparse(url.lower().strip())
    host = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip("/")

#  검색 결과 전처리: 중복 제거 + 길이 제한 + 날짜/출처 포맷
def preprocess_context(raw_results: list, max_chars_per_result: int = 600) -> str:
    """
    Tavily 검색 결과를 Gemini에 넘기기 전에 정제합니다.
    - raw_results: Tavily response["results"] 리스트
    - 각 항목: {"title", "url", "content", "published_date"(optional)}
    """
    if not raw_results:
        return ""

    seen_contents = set()
    processed = []

    for i, result in enumerate(raw_results):
        content = result.get("content", "").strip()

        # 중복 내용 제거 (앞 50자 기준)
        content_key = content[:50]
        if content_key in seen_contents:
            continue
        seen_contents.add(content_key)

        # 길이 제한
        if len(content) > max_chars_per_result:
            content = content[:max_chars_per_result] + "..."

        title = result.get("title", "제목 없음")
        url = result.get("url", "")
        date = result.get("published_date", "")
        date_str = f" ({date})" if date else ""

        processed.append(
            f"[출처 {i+1}] {title}{date_str}\n"
            f"URL: {url}\n"
            f"{content}"
        )

    if not processed:
        return ""

    return "\n\n---\n\n".join(processed)

def build_chat_response(messages: List[Message], search_results: list = None) -> str:

    """ 
    search_results: Tavily의 response["results"] 리스트 (없으면 None)
    context 문자열 대신 raw results를 받아서 내부에서 전처리합니다.
    """ 

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dynamic_prompt = f"{SYSTEM_PROMPT}\n\n[시스템 정보]\n현재 일시: {now}"

    generation_config = {
    "temperature": 0.2,    # 낮을수록 정확하고 일관된 답변 (0.0 ~ 2.0), 대답이 너무 일관적인 경우 상향조정
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 4096, # 답변 길이 제한
    }

    try:
        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=dynamic_prompt,
            generation_config = generation_config,
        )

        # 히스토리 요약 로직 추가
        # 대화 내역이 너무 길어지면(예: 15개 이상) 앞부분을 요약하여 전달
        if len(messages) > 15:
            past_content = "\n".join(
                [f"{m.role}: {m.content}" for m in messages[:-10]]
            )
            summary_prompt = (
                "다음 대화에서 충북대학교 관련 핵심 정보(언급된 학과, 일정, 문의 내용 등)만 "
                "3줄 이내로 요약하세요. 불필요한 인사말은 제외하세요:\n\n"
                + past_content
            )
            summary_response = model.generate_content(summary_prompt)
            summary_text = f"[이전 대화 요약]: {summary_response.text}"
                    
            # 요약본을 첫 번째 히스토리로 넣고, 최근 10개만 유지
            history = [{"role": "user", "parts": [summary_text]}]
            history.extend([
                {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
                for m in messages[-10:-1]
            ])
            
        else:
            history = [
                {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
                for m in messages[:-1]
            ]
        # 토큰 개수 확인 (디버깅용)
        total_tokens = model.count_tokens(str(history)).total_tokens
        print(f"현재 전송 토큰 수: {total_tokens}")
        print(f"메시지당 평균 토큰: {total_tokens / len(history):.1f}")

        chat = model.start_chat(history=history)
        
        #  검색 결과 전처리 후 컨텍스트 구성
        last_content = messages[-1].content
        context = preprocess_context(search_results) if search_results else ""

        if context:
            last_content = (
                f"[참고 자료]\n{context}\n\n"
                f"---\n"
                f"위 참고 자료를 바탕으로 아래 질문에 답변하세요. "
                f"[질문]\n{last_content}"
            )
        else:
            # 검색 결과 없을 때 Gemini에게 명시적으로 알림
            last_content = (
                f"[참고 자료 없음]\n"
                f"웹 검색 결과가 없습니다. 학습된 지식으로만 답변하되, "
                f"불확실한 내용은 공식 홈페이지 확인을 안내하세요.\n\n"
                f"[질문]\n{last_content}"
            )

        #  finish_reason 체크 + 재시도 로직
        max_retries = 3
        for attempt in range(max_retries):
            response = chat.send_message(last_content)
            finish_reason = response.candidates[0].finish_reason.name

            if finish_reason == "STOP":
                return response.text

            print(f"[시도 {attempt + 1}] finish_reason: {finish_reason}")

            if finish_reason == "MAX_TOKENS":
                # 답변이 잘린 경우 이어쓰기 요청
                followup = chat.send_message("이어서 계속 작성해주세요.")
                return response.text + followup.text

            if finish_reason in ("SAFETY", "RECITATION"):
                return "해당 질문에는 답변이 어렵습니다. 충북대학교 공식 홈페이지를 확인해주세요."

            time.sleep(1)

        return response.text

    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return "죄송합니다. 현재 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요."

async def optimize_search_query(user_query: str, messages: List[Message]) -> str:
    recent_context = "\n".join(
        [f"{m.role}: {m.content}" for m in messages[-4:-1]]
    ) if len(messages) > 1 else ""

    prompt = f"""사용자의 질문을 웹 검색에 적합한 구체적인 검색어로 변환하세요.

    규칙:
    1. "거기", "그거", "그 학과", "알려줘", "추려줘" 같은 대명사/동사는 앞 대화를 보고 반드시 구체적 명사로 교체하세요.
    2. 충북대학교 관련 질문이면 "충북대학교" 키워드를 포함하세요.
    3. 검색어는 반드시 10자 이상으로 작성하세요.
    4. 검색어만 출력하고 설명, 따옴표, 부연은 절대 쓰지 마세요.

    [이전 대화]
    {recent_context if recent_context else "없음"}

    [사용자 질문]
    {user_query}

    [검색어]"""

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"temperature": 0.0, "max_output_tokens": 64},
        )
        response = model.generate_content(prompt)

        #  finish_reason 먼저 확인 후 text 접근 (SAFETY 등 비정상 종료 대비)
        finish_reason = response.candidates[0].finish_reason.name
        if finish_reason != "STOP":
            raise ValueError(f"finish_reason: {finish_reason}")

        optimized = response.text.strip()

        #  중복 "충북대학교" 제거 후 길이 체크
        if len(optimized) < 10:
            raise ValueError(f"결과가 너무 짧음: '{optimized}'")

        print(f"[쿼리 최적화] '{user_query}' → '{optimized}'")
        return optimized
    
    except Exception as e:
        #  폴백: 이미 충북대 포함이면 그대로, 없으면 앞에 붙이기
        print(f"[쿼리 최적화 실패] {e}")
        fallback = user_query if "충북대" in user_query or "cbnu" in user_query.lower() \
                   else f"충북대학교 {user_query}"
        print(f"[폴백 쿼리] {fallback}")
        return fallback