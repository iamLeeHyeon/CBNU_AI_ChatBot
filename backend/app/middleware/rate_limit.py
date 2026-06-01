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