# 충북대학교 AI 챗봇

Google Gemini 2.5 Flash와 Tavily 웹 검색을 결합한 충북대학교 전용 AI 챗봇입니다.  
LMS(e-Class) 연동을 통해 수강 강좌, 과제, 성적, 캘린더 정보를 제공합니다.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트엔드 | React 18 + Vite + Tailwind CSS |
| 백엔드 | FastAPI (Python 3.10+) |
| AI | Google Gemini 2.5 Flash |
| 웹 검색 | Tavily API |
| LMS 연동 | 충북대 e-Class (Moodle REST API) |

---

## 프로젝트 구조

```
cbnu-ai-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 앱, CORS, 라우터 등록
│   │   ├── routers/
│   │   │   ├── chat.py          # POST /api/chat
│   │   │   ├── lms.py           # /api/lms/* (로그인, 과제, 성적 등)
│   │   │   └── notices.py       # GET /api/notices (공지사항)
│   │   ├── services/
│   │   │   ├── gemini.py        # Gemini 모델 초기화 및 응답 생성
│   │   │   ├── tavily.py        # Tavily 웹 검색
│   │   │   └── lms.py           # e-Class REST API 클라이언트
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic 스키마
│   │   └── crawler/
│   │       └── notice_crawler.py # 공지사항/학사일정 검색
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── App.jsx              # 루트 컴포넌트, 상태 관리
        └── components/
            ├── ChatWindow.jsx   # 메시지 목록 렌더링
            ├── InputBar.jsx     # 입력창 + 웹 검색 토글
            └── MessageBubble.jsx # 메시지 버블 (출처 URL 표시)
```

---

## 시작하기

### 사전 준비

- Python 3.10 이상
- Node.js 18 이상
- [Gemini API 키](https://aistudio.google.com/app/apikey)
- [Tavily API 키](https://tavily.com)
  
### 의존성 설치
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
google-generativeai==0.8.3
tavily-python==0.5.0
httpx==0.27.2
pydantic==2.9.2
playwright==1.49.0
beautifulsoup4==4.12.3

### 1. 백엔드 실행

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력

# 서버 실행
uvicorn app.main:app --reload   # http://localhost:8000
```

### 2. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

브라우저에서 `http://localhost:5173` 접속

---

### 3. UnitTest 실행
```bash
# 테스트 의존성 설치
pip install pytest pytest-cov

# 전체 테스트
pytest tests/ --cov -v

# 특정 파일만 테스트
# pytest에서는 전체 경로 지정, --cov= 에서는 파일명만 지정
pytest tests/test_myfile.py --cov=myfile --cov-report=term-missing
```

## 환경변수

`backend/.env` 파일에 설정합니다.

| 변수 | 필수 | 설명 |
|------|------|------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API 키 |
| `TAVILY_API_KEY` | ✅ | Tavily 검색 API 키 |
| `ALLOWED_ORIGINS` | ❌ | CORS 허용 오리진 (기본값: `http://localhost:5173`) |

> **참고:** `ALLOWED_ORIGINS`는 콤마로 복수 오리진 설정 가능  
> 예) `ALLOWED_ORIGINS=https://cbnu-chatbot.com,https://www.cbnu-chatbot.com`

---

## API 엔드포인트

### 공통

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 서버 상태 확인 |

### 챗봇

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat` | AI 응답 요청 (멀티턴, 웹 검색 옵션 포함) |

**요청 예시:**
```json
{
  "messages": [
    { "role": "user", "content": "충북대 도서관 운영 시간 알려줘" }
  ],
  "use_search": true
}
```

### LMS (e-Class 연동)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/lms/login` | LMS 로그인 (쿠키 세션 발급) |
| POST | `/api/lms/logout` | 로그아웃 |
| GET | `/api/lms/me` | 현재 로그인 상태 확인 |
| GET | `/api/lms/data` | 강좌·과제·성적·캘린더 일괄 조회 |

### 공지사항

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/notices` | 충북대 공지사항 및 학사일정 |

---

## 주요 기능

- **멀티턴 대화** — 이전 대화 맥락을 유지한 연속 질문 가능
- **웹 검색 연동** — 토글 활성화 시 Tavily로 최신 정보 검색 후 답변에 반영
- **LMS 연동** — 충북대 e-Class 로그인 후 과제 마감일·성적·캘린더 조회
- **공지사항 검색** — 충북대 공지사항 및 학사일정 실시간 검색

### License



# Contributors
- 최진우 @ediottchoi
- 김산 @sankim05
- 홍성권 @joheonkr
- 이현 @iamLeeHyeon
