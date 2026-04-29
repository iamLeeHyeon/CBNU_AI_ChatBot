# 충북대학교 AI 챗봇

Google Gemini 2.5 Flash와 Tavily 웹 검색을 활용한 충북대학교 전용 AI 챗봇입니다.  
학생·교직원·방문자에게 학교 관련 정보를 실시간으로 제공합니다.

## 주요 기능

- **AI 챗봇**: Gemini 2.5 Flash 기반 대화형 응답
- **웹 검색 연동**: Tavily API를 이용한 실시간 정보 검색 (토글 방식)
- **공지사항 크롤링**: 충북대 공지사항 및 학사일정 자동 수집
- **대화 히스토리**: 멀티턴 대화 컨텍스트 유지
- **출처 표시**: 검색 기반 답변 시 참고 URL 제공

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트엔드 | React 18 + Vite + Tailwind CSS |
| 백엔드 | FastAPI (Python 3.13) |
| AI 모델 | Google Gemini 2.5 Flash |
| 웹 검색 | Tavily API |

## 프로젝트 구조

```
cbnu-ai-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── routers/
│   │   │   ├── chat.py          # 채팅 API 라우터
│   │   │   └── notices.py       # 공지사항 API 라우터
│   │   ├── services/
│   │   │   ├── gemini.py        # Gemini 모델 연동
│   │   │   └── tavily.py        # Tavily 웹 검색 연동
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic 스키마
│   │   └── crawler/
│   │       └── notice_crawler.py # 충북대 공지 크롤러
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx              # 루트 컴포넌트 (상태 관리, API 호출)
        └── components/
            ├── ChatWindow.jsx   # 메시지 목록 렌더링
            ├── InputBar.jsx     # 입력창 + 웹 검색 토글
            └── MessageBubble.jsx
```

## 시작하기

### 사전 요구사항

- Python 3.10 이상
- Node.js 18 이상
- [Gemini API 키](https://aistudio.google.com/app/apikey)
- [Tavily API 키](https://tavily.com)

### 1. 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력 (아래 환경변수 섹션 참고)

# 서버 실행
uvicorn app.main:app --reload
```

백엔드 서버: `http://localhost:8000`

### 2. 프론트엔드 설정

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

## 환경변수

`backend/.env` 파일에 아래 값을 설정합니다.

```env
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

## API 명세

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 서버 상태 확인 |
| POST | `/api/chat` | AI 챗봇 응답 요청 |
| GET | `/api/notices` | 충북대 공지사항 조회 |

### POST /api/chat

**Request**
```json
{
  "messages": [
    { "role": "user", "content": "수강신청은 언제인가요?" }
  ],
  "use_search": false
}
```

**Response**
```json
{
  "reply": "수강신청 일정은 ...",
  "sources": ["https://..."]
}
```

- `use_search: true`로 설정하면 Tavily 웹 검색 결과를 컨텍스트로 활용합니다.
- `sources`는 웹 검색 사용 시 참고한 URL 목록입니다.
