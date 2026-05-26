from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str = Field(min_length=1, max_length=2000)
    
    # role 값 검증
    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v):
        if v not in ("user", "assistant"):
            raise ValueError("role은 user 또는 assistant여야 합니다.")
        return v

class ChatRequest(BaseModel):
    messages: List[Message] = Field(min_length=1, max_length=50)
    use_search: bool = False


class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []


# ── LMS 관련 스키마 ──────────────────────────────────────────

class LMSLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=50)


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
