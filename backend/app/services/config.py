# ──────────────────────────────────────────────
#  app/services/config.py
#  전역 상수 · 설정값 모음 (하드코딩 제거)
# ──────────────────────────────────────────────

# ── 충북대 관련 키워드 ──────────────────────────
CBNU_KEYWORDS: tuple[str, ...] = ("충북대", "chungbuk", "cbnu")
CBNU_OFFICIAL_URL = "https://www.chungbuk.ac.kr"

# ── URL 정규화 시 제거할 기본 경로 패턴 ──────────
DEFAULT_URL_PATTERNS: tuple[str, ...] = (
    "/index.do", "/index.html", "/index.php", "/main.do",
    "/www/index.do", "/www/index.html", "/www/main.do", "/www",
)

# ── Gemini 모델 설정 ──────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"

GEMINI_CHAT_CONFIG = {
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 4096,
}

GEMINI_QUERY_CONFIG = {
    "temperature": 0.0,
    "max_output_tokens": 1024,
}

GEMINI_RANK_CONFIG = {
    "temperature": 0.0,
    "max_output_tokens": 2048,
}

GEMINI_SUMMARY_CONFIG = {
    "temperature": 0.2,
    "max_output_tokens": 512,
}

# ── 히스토리 요약 임계값 ──────────────────────
HISTORY_SUMMARY_THRESHOLD = 15   # 메시지 수 초과 시 요약
HISTORY_RECENT_KEEP = 10         # 요약 후 최근 N개 유지

# ── 검색 결과 처리 ────────────────────────────
SEARCH_MAX_RESULTS = 5           # Tavily 검색 결과 수
SEARCH_CONTEXT_MAX_CHARS = 600   # 결과 1건당 최대 글자 수
RANK_MIN_SCORE = 15              # 이 점수 미만이면 결과 제외
RANK_TOP_K = 3                   # 상위 N개 결과만 사용

# ── 재시도 설정 ───────────────────────────────
MAX_RETRIES = 3

# ── 시스템 프롬프트 ───────────────────────────
SYSTEM_PROMPT = f"""당신은 충북대학교(CBNU) 전용 AI 챗봇입니다.
학생, 교직원, 방문자에게 충북대학교에 관한 정확하고 친절한 정보를 제공합니다.

[답변 원칙]
1. 반드시 제공된 [참고 자료]를 우선 근거로 삼아 답변하세요.
2. 참고 자료만으로 답변이 불충분할 경우, 학습된 지식을 보조적으로 활용하되 "공식 확인 필요" 라고 명시하세요.
3. 참고 자료에 없는 내용은 솔직히 모른다고 하고, 공식 홈페이지({CBNU_OFFICIAL_URL}) 확인을 안내하세요.
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
4. 위 과정을 바탕으로 최종 답변 구성"""
