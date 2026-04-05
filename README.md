# 충북대학교 AI 챗봇

Gemini Flash + Tavily 검색을 활용한 충북대학교 전용 AI 챗봇입니다.

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트엔드 | React 18 + Vite + Tailwind CSS |
| 백엔드 | FastAPI (Python) |
| AI | Google Gemini 1.5 Flash |
| 검색 | Tavily API |

## 시작하기

### 1. 백엔드

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env에 API 키 입력

uvicorn app.main:app --reload
```

### 2. 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

## 환경변수

`backend/.env` 파일에 아래 값을 설정합니다.

```
GEMINI_API_KEY=...
TAVILY_API_KEY=...
```

## API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 서버 상태 확인 |
| POST | `/api/chat` | 챗봇 응답 요청 |
