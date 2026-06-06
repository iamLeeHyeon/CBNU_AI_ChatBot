# 충북대학교 AI 챗봇

Google Gemini 2.5 Flash와 Tavily 웹 검색을 결합한 충북대학교 전용 AI 챗봇입니다.  
LMS(e-Class) 연동을 통해 수강 강좌, 과제, 성적 정보를 제공하며, 학식 메뉴 실시간 크롤링 기능을 포함합니다.

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
│   │   ├── main.py                  # FastAPI 앱, CORS, 미들웨어, 라우터 등록
│   │   ├── middleware/
│   │   │   └── rate_limit.py        # IP 기반 요청 속도 제한
│   │   ├── routers/
│   │   │   ├── chat.py              # POST /api/chat (SSE 스트리밍)
│   │   │   └── lms.py               # /api/lms/* (로그인, 대시보드, 과제, 성적 등)
│   │   ├── services/
│   │   │   ├── gemini.py            # Gemini 스트리밍 응답, 쿼리 최적화, 결과 평가
│   │   │   ├── gemini_client.py     # Gemini 클라이언트 싱글톤
│   │   │   ├── tavily.py            # Tavily 웹 검색
│   │   │   ├── cafeteria.py         # 충북대 학식 메뉴 크롤러
│   │   │   ├── lms.py               # e-Class REST API 클라이언트
│   │   │   ├── lms_context.py       # LMS 데이터 → Gemini 컨텍스트 변환
│   │   │   ├── utils.py             # URL 정규화, 검색 결과 전처리
│   │   │   └── config.py            # 전역 설정값
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic 스키마
│   │   └── crawler/
│   │       └── notice_crawler.py    # 공지사항/학사일정 검색
│   ├── tests/                       # 단위 테스트
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── App.jsx                  # 루트 컴포넌트, 상태 관리, SSE 파싱
        └── components/
            ├── ChatWidget.jsx       # 플로팅 채팅 위젯 (대화 목록, 삭제)
            ├── ChatWindow.jsx       # 메시지 목록 렌더링
            ├── InputBar.jsx         # 입력창 + 웹 검색 토글
            ├── MessageBubble.jsx    # 메시지 버블 (출처 URL 표시)
            └── LMS/
                ├── LMSLogin.jsx     # LMS 로그인 폼
                └── LMSDashboard.jsx # 강좌·과제·성적 대시보드
```

---

## 시작하기

### 사전 준비

- Python 3.10 이상
- Node.js 18 이상
- [Gemini API 키](https://aistudio.google.com/app/apikey)
- [Tavily API 키](https://tavily.com)

### 의존성 

```bash
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
google-generativeai==0.8.3
tavily-python==0.5.0
httpx==0.27.2
pydantic==2.9.2
playwright==1.49.0
beautifulsoup4==4.12.3
```

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

### 3. Unit Test 실행

```bash
cd backend
source venv/bin/activate        # Windows: venv\Scripts\activate

# 테스트 의존성 설치
pip install pytest pytest-cov
# 테스트용 비동기 함수               └── LMSDashboard.jsx # 강좌·과제·성적 대시보드
```

---

## 시작하기

### 사전 준비

- Python 3.10 이상
- Node.js 18 이상
- [Gemini API 키](https://aistudio.google.com/app/apikey)
- [Tavily API 키](https://tavily.com)

### 의존성 

```bash
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
google-generativeai==0.8.3
tavily-python==0.5.0
httpx==0.27.2
pydantic==2.9.2
playwright==1.49.0
beautifulsoup4==4.12.3
```

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

### 3. Unit Test 실행

```bash
cd backend
source venv/bin/activate        # Windows: venv\Scripts\activate

# 테스트 의존성 설치
pip install pytest pytest-cov
# 비동기 프로그램 테스트를 위한 pytest 플러그인
pip install pytest-asyncio

#전체 테스트
pytest tests/ --cov=app --cov-report=term-missing   

#특정 파일만 테스트
#pytest에서는 전체 경로 지정, --cov= 에서는 파일명만 지정
pytest tests/test_myfile.py --cov=myfile --cov-report=term-missing
```
테스트 실행시 환경변수 .env파일 있는지 확인, 없다면 아래 환경변수 설정에 따라 .env 파일 만든 후 
유닛테스트만 실행을 한다면 api키 자리에 DUMMY(아무 값, 더미)추가 후 유닛테스트 실행 

---

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
| POST | `/api/chat` | AI 응답 요청 — SSE 스트리밍 방식 |

**요청 예시:**
```json
{
  "messages": [
    { "role": "user", "content": "충북대 도서관 운영 시간 알려줘" }
  ],
  "use_search": true
}
```

**응답 형식 (SSE 스트리밍):**
```
data: {"type": "token",   "value": "충북대학교 "}
data: {"type": "token",   "value": "도서관은..."}
data: {"type": "sources", "value": ["https://..."]}
data: {"type": "done"}
```

### LMS (e-Class 연동)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/lms/login` | LMS 로그인 (쿠키 세션 발급) |
| POST | `/api/lms/logout` | 로그아웃 |
| POST | `/api/lms/sync` | LMS 데이터 재동기화 |
| GET | `/api/lms/dashboard` | 강좌·과제·성적 일괄 조회 |
| GET | `/api/lms/assignments` | 과제 목록 조회 |
| GET | `/api/lms/materials` | 강의자료 목록 조회 |

---

## 주요 기능

- **멀티턴 대화** — 이전 대화 맥락을 유지한 연속 질문 가능
- **SSE 스트리밍** — 응답 토큰 단위로 실시간 출력
- **웹 검색 연동** — 토글 활성화 시 Tavily로 최신 정보 검색 후 답변에 반영
- **LMS 연동** — 충북대 e-Class 로그인 후 과제 마감일·성적·강의자료 조회
- **학식 메뉴 크롤링** — "오늘 학식" 질문 시 충북대 생협 사이트에서 실시간 메뉴 크롤링
- **대화 관리** — 채팅 히스토리 저장, 대화 전환 및 삭제
- **Rate Limiting** — IP 기반 분당 요청 수 제한 (API 남용 방지)

---

## License

MIT License

Copyright (c) 2026 LeeHyeon, HongSeonggwon, KimSan, ChoiJinwoo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Contributors

- 최진우 @ediottchoi
- 김산 @sankim05
- 홍성권 @joheonkr
- 이현 @iamLeeHyeon
