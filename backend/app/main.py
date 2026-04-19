from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers.chat import router as chat_router
from app.routers.notices import router as notices_router
from app.routers.lms import router as lms_router

load_dotenv()

app = FastAPI(title="CBNU AI Chatbot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(notices_router)
app.include_router(lms_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
