from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    use_search: bool = False


class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []



# ── LMS 관련 스키마 ──────────────────────────────────────────

class LMSLoginRequest(BaseModel):
    username: str
    password: str


class LMSLoginResponse(BaseModel):
    success: bool
    user_name: str = ""   # 로그인한 사용자 이름
    message: str = ""     # 실패 시 오류 메시지


class Course(BaseModel):
    id: int
    full_name: str        # 강좌 전체 이름
    short_name: str       # 강좌 약칭


class Assignment(BaseModel):
    id: int
    course_name: str
    name: str             # 과제명
    due_date: Optional[int] = None   # Unix timestamp (없으면 None)
    submitted: bool = False          # 제출 여부


class Grade(BaseModel):
    course_name: str
    item_name: str        # 평가 항목명
    grade: Optional[str] = None      # 점수 (문자열, 없으면 None)
    max_grade: Optional[str] = None  # 만점


class CalendarEvent(BaseModel):
    id: int
    name: str
    time_start: int       # Unix timestamp
    event_type: str       # "assignment", "course", "site" 등


class LMSDataResponse(BaseModel):
    courses: List[Course] = []
    assignments: List[Assignment] = []
    grades: List[Grade] = []
    calendar: List[CalendarEvent] = []

# LMS 로그인 요청 스키마
class LMSLoginRequest(BaseModel):
    student_id: str
    password: str

