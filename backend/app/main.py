import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers.chat import router as chat_router
from app.routers.lms import router as lms_router

load_dotenv()

# 필수 환경변수 체크 — 누락 시 서버 시작 전에 명확한 오류 발생
_REQUIRED_ENV = ["GEMINI_API_KEY", "TAVILY_API_KEY"]
_missing = [k for k in _REQUIRED_ENV if not os.getenv(k)]
if _missing:
    raise RuntimeError(f"필수 환경변수 누락: {', '.join(_missing)}")

# CORS 허용 오리진 — 환경변수로 관리 (배포 시 도메인 변경 가능)
_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="CBNU AI Chatbot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(lms_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
