# ──────────────────────────────────────────────
#  app/services/gemini.py
#  Gemini API 연동: 쿼리 최적화 · 결과 평가 · 챗 응답
# ──────────────────────────────────────────────
import json
import re
import time
from datetime import datetime
from typing import List

from app.models.schemas import Message
from app.services.config import (
    CBNU_KEYWORDS,
    GEMINI_CHAT_CONFIG,
    GEMINI_QUERY_CONFIG,
    GEMINI_RANK_CONFIG,
    GEMINI_SUMMARY_CONFIG,
    HISTORY_RECENT_KEEP,
    HISTORY_SUMMARY_THRESHOLD,
    MAX_RETRIES,
    RANK_MIN_SCORE,
    RANK_TOP_K,
    SYSTEM_PROMPT,
)
from app.services.gemini_client import get_model
from app.services.utils import preprocess_context


# ── 내부 헬퍼 ─────────────────────────────────

def _format_messages_as_history(messages: list[Message]) -> list[dict]:
    """Message 리스트를 Gemini history 포맷으로 변환."""
    return [
        {
            "role": "user" if m.role == "user" else "model",
            "parts": [m.content],
        }
        for m in messages
    ]


def _summarize_history(past_messages: list[Message]) -> str:
    """오래된 대화를 3줄 이내로 요약."""
    past_content = "\n".join(f"{m.role}: {m.content}" for m in past_messages)
    prompt = (
        "다음 대화에서 충북대학교 관련 핵심 정보(언급된 학과, 일정, 문의 내용 등)만 "
        "3줄 이내로 요약하세요. 불필요한 인사말은 제외하세요:\n\n"
        + past_content
    )
    model = get_model(GEMINI_SUMMARY_CONFIG)
    response = model.generate_content(prompt)
    return f"[이전 대화 요약]: {response.text}"


def _build_history(messages: list[Message]) -> list[dict]:
    """
    메시지 수에 따라 히스토리를 구성.
    임계값 초과 시 오래된 부분을 요약으로 대체.
    """
    if len(messages) <= HISTORY_SUMMARY_THRESHOLD:
        return _format_messages_as_history(messages[:-1])

    summary_text = _summarize_history(messages[:-HISTORY_RECENT_KEEP])
    history = [{"role": "user", "parts": [summary_text]}]
    history.extend(_format_messages_as_history(messages[-HISTORY_RECENT_KEEP:-1]))
    return history


def _build_user_message(content: str, search_results: list) -> str:
    """검색 결과 유무에 따라 최종 사용자 메시지를 구성."""
    context = preprocess_context(search_results)

    if context:
        return (
            f"[참고 자료]\n{context}\n\n"
            f"---\n"
            f"위 참고 자료를 바탕으로 아래 질문에 답변하세요.\n\n"
            f"[질문]\n{content}"
        )

    return (
        f"[참고 자료 없음]\n"
        f"웹 검색 결과가 없습니다. 학습된 지식으로만 답변하되, "
        f"불확실한 내용은 공식 홈페이지 확인을 안내하세요.\n\n"
        f"[질문]\n{content}"
    )


def _send_with_retry(chat, message: str) -> str:
    """응답을 전송하고 finish_reason에 따라 재시도 또는 이어쓰기."""
    for attempt in range(MAX_RETRIES):
        response = chat.send_message(message)
        finish_reason = response.candidates[0].finish_reason.name

        if finish_reason == "STOP":
            return response.text

        print(f"[시도 {attempt + 1}] finish_reason: {finish_reason}")

        if finish_reason == "MAX_TOKENS":
            followup = chat.send_message("이어서 계속 작성해주세요.")
            return response.text + followup.text

        if finish_reason in ("SAFETY", "RECITATION"):
            return "해당 질문에는 답변이 어렵습니다. 충북대학교 공식 홈페이지를 확인해주세요."

        time.sleep(1)

    return response.text


# ── Public API ────────────────────────────────

def build_chat_response(messages: List[Message], search_results: list = None) -> str:
    """검색 결과를 참고해 Gemini 챗 응답을 생성."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    system_instruction = f"{SYSTEM_PROMPT}\n\n[시스템 정보]\n현재 일시: {now}"

    try:
        model = get_model(GEMINI_CHAT_CONFIG, system_instruction)

        history = _build_history(messages)

        total_tokens = model.count_tokens(str(history)).total_tokens
        print(f"현재 전송 토큰 수: {total_tokens}")

        chat = model.start_chat(history=history)
        user_message = _build_user_message(
            messages[-1].content,
            search_results or [],
        )
        return _send_with_retry(chat, user_message)

    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return "죄송합니다. 현재 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요."


async def optimize_search_query(user_query: str, messages: List[Message]) -> str:
    """사용자 질문을 웹 검색에 적합한 구체적인 쿼리로 변환."""
    recent_context = (
        "\n".join(f"{m.role}: {m.content}" for m in messages[-4:-1])
        if len(messages) > 1
        else "없음"
    )

    prompt = (
        f"사용자의 질문을 웹 검색에 적합한 구체적인 검색어로 변환하세요.\n\n"
        f"규칙:\n"
        f"1. '거기', '그거', '그 학과', '알려줘', '추려줘' 같은 대명사/동사는 앞 대화를 보고 반드시 구체적 명사로 교체하세요.\n"
        f"2. 충북대학교 관련 질문이면 '충북대학교' 키워드를 포함하세요.\n"
        f"3. 검색어는 반드시 10자 이상으로 작성하세요.\n"
        f"4. 검색어만 출력하고 설명, 따옴표, 부연은 절대 쓰지 마세요.\n\n"
        f"[이전 대화]\n{recent_context}\n\n"
        f"[사용자 질문]\n{user_query}\n\n"
        f"[검색어]"
    )

    try:
        model = get_model(GEMINI_QUERY_CONFIG)
        response = model.generate_content(prompt)

        finish_reason = response.candidates[0].finish_reason.name
        if finish_reason != "STOP":
            raise ValueError(f"finish_reason: {finish_reason}")

        optimized = response.text.strip()
        if len(optimized) < 10:
            raise ValueError(f"결과가 너무 짧음: '{optimized}'")

        print(f"[쿼리 최적화] '{user_query}' → '{optimized}'")
        return optimized

    except Exception as e:
        print(f"[쿼리 최적화 실패] {e}")
        fallback = (
            user_query
            if any(kw in user_query or kw in user_query.lower() for kw in CBNU_KEYWORDS)
            else f"충북대학교 {user_query}"
        )
        print(f"[폴백 쿼리] {fallback}")
        return fallback


def evaluate_and_rank_results(query: str, raw_results: list) -> list:
    """검색 결과를 Gemini로 평가해 관련도 높은 상위 결과만 반환."""
    if not raw_results:
        return []

    candidates_str = "\n\n".join(
        f"[{i}] 제목: {r.get('title', '')}\n"
        f"URL: {r.get('url', '')}\n"
        f"내용: {r.get('content', '')[:300]}"
        for i, r in enumerate(raw_results)
    )

    prompt = (
        f"다음은 '{query}'에 대한 웹 검색 결과입니다.\n\n"
        f"{candidates_str}\n\n"
        f"각 결과를 아래 기준으로 평가하여 JSON으로만 응답하세요. 설명 없이 JSON만 출력하세요.\n"
        f"기준:\n"
        f"1. 충북대학교와의 관련성 (0~10)\n"
        f"2. 정보의 구체성 (0~10)\n"
        f"3. 신뢰할 수 있는 출처 여부 (공식 홈페이지/뉴스/학교 공지 등) (0~10)\n\n"
        f"응답 형식:\n"
        f'[{{"index": 0, "score": 25, "reason": "공식 공지사항"}}, ...]'
    )

    try:
        model = get_model(
            GEMINI_RANK_CONFIG,
            system_instruction="당신은 정보 품질 평가 전문가입니다. JSON만 출력합니다.",
        )
        response = model.generate_content(prompt)

        raw = re.sub(r"```json|```", "", response.text.strip())
        rankings: list[dict] = json.loads(raw)
        rankings.sort(key=lambda x: x["score"], reverse=True)

        for r in rankings:
            print(f"[결과 평가] index={r['index']} score={r['score']} reason={r.get('reason', '')}")

        top_indices = [
            r["index"] for r in rankings if r["score"] >= RANK_MIN_SCORE
        ][:RANK_TOP_K]

        if not top_indices:
            print("[결과 평가] 기준 충족 결과 없음 → 전체 사용")
            return raw_results

        return [raw_results[i] for i in top_indices]

    except Exception as e:
        print(f"[결과 평가 실패] {e} → 전체 결과 사용")
        return raw_results
    
async def stream_chat_response(messages, search_results=None):
    """
    Gemini 응답을 토큰 단위로 스트리밍하는 비동기 제너레이터.
    router의 SSE 스트림에서 async for로 소비.
    """
    import asyncio as _asyncio
 
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    system_instruction = f"{SYSTEM_PROMPT}\n\n[시스템 정보]\n현재 일시: {now}"
 
    try:
        model = get_model(GEMINI_CHAT_CONFIG, system_instruction)
        history = _build_history(messages)
 
        total_tokens = model.count_tokens(str(history)).total_tokens
        print(f"현재 전송 토큰 수: {total_tokens}")
 
        chat = model.start_chat(history=history)
        user_message = _build_user_message(
            messages[-1].content,
            search_results or [],
        )
 
        # 동기 스트림을 별도 스레드에서 실행하고 Queue로 메인 루프에 전달
        # None은 종료 신호, Exception은 오류 전파용
        queue = _asyncio.Queue()
        loop = _asyncio.get_event_loop()
 
        def _run_stream():
            try:
                for chunk in chat.send_message(user_message, stream=True):
                    if chunk.text:
                        loop.call_soon_threadsafe(queue.put_nowait, chunk.text)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, e)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)
 
        import threading as _threading
        thread = _threading.Thread(target=_run_stream, daemon=True)
        thread.start()
 
        while True:
            item = await queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
            # 청크를 단어 단위로 쪼개 yield → 타이핑되는 느낌
            words = item.split(" ")
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                await _asyncio.sleep(0.03)
 
    except Exception as e:
        print(f"[스트리밍 오류] {e}")
        yield "죄송합니다. 현재 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요."
