#──────────────────────────────────────────────
#  app/middleware/rate_limit.py
#  IP 기반 요청 속도 제한 (슬라이딩 윈도우)
# ──────────────────────────────────────────────
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ── 설정 ──────────────────────────────────────
RATE_LIMIT_REQUESTS = 10   # 허용 요청 수
RATE_LIMIT_WINDOW = 60     # 윈도우 크기 (초)
RATE_LIMITED_PATHS = {"/api/chat"}  # 제한 적용 경로

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    슬라이딩 윈도우 방식 IP별 Rate Limiter.
    - RATE_LIMIT_WINDOW 초 안에 RATE_LIMIT_REQUESTS 회 초과 시 429 반환
    - /api/chat 경로에만 적용
    """

    def __init__(self, app):
        super().__init__(app)
        # IP → 요청 타임스탬프 큐
        self._requests: dict[str, deque] = defaultdict(deque)

    def _get_client_ip(self, request: Request) -> str:
        """X-Forwarded-For 헤더 우선, 없으면 직접 연결 IP."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path not in RATE_LIMITED_PATHS:
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW
        queue = self._requests[ip]

        # 윈도우 밖 타임스탬프 제거
        while queue and queue[0] < window_start:
            queue.popleft()

        if len(queue) >= RATE_LIMIT_REQUESTS:
            retry_after = int(queue[0] + RATE_LIMIT_WINDOW - now) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"요청이 너무 많습니다. {retry_after}초 후 다시 시도해주세요."
                },
                headers={"Retry-After": str(retry_after)},
            )

        queue.append(now)
        return await call_next(request)