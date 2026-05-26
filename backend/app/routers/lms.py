import uuid
import time
from fastapi import APIRouter, HTTPException, Cookie, Response
from typing import Optional

from app.models.schemas import (
    LMSLoginRequest, LMSLoginResponse,
    LMSDataResponse, Course, Assignment, Grade, CalendarEvent,
)
from app.services import lms as lms_service

router = APIRouter(prefix="/api/lms", tags=["lms"])

# 서버 메모리 세션 저장소: { session_id: { "token": ..., "user_id": ..., "user_name": ..., "expires_at": ... } }
_sessions: dict[str, dict] = {}
_SESSION_TTL = 60 * 60 * 8  # 8시간 (쿠키 max_age와 동일)


def _cleanup_sessions() -> None:
    """만료된 세션 정리."""
    now = time.time()
    expired = [k for k, v in _sessions.items() if now > v["expires_at"]]
    for k in expired:
        del _sessions[k]


def _get_session(session_id: Optional[str]) -> dict:
    """세션 ID로 세션 데이터 조회. 없거나 만료됐으면 401."""
    _cleanup_sessions()
    if not session_id or session_id not in _sessions:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    session = _sessions[session_id]
    if time.time() > session["expires_at"]:
        del _sessions[session_id]
        raise HTTPException(status_code=401, detail="세션이 만료됐습니다. 다시 로그인하세요.")
    return session


@router.post("/login", response_model=LMSLoginResponse)
async def lms_login(req: LMSLoginRequest, response: Response):
    """
    LMS 로그인.
    성공 시 서버 세션에 토큰 저장, 클라이언트엔 세션 쿠키만 반환.
    """
    try:
        token = lms_service.get_token(req.username, req.password)
    except ValueError as e:
        return LMSLoginResponse(success=False, message=str(e))
    except Exception:
        return LMSLoginResponse(success=False, message="LMS 서버에 연결할 수 없습니다.")

    try:
        info = lms_service.get_user_info(token)
    except Exception:
        info = {"user_id": None, "user_name": ""}

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "token": token,
        "user_id": info["user_id"],
        "user_name": info["user_name"],
        "expires_at": time.time() + _SESSION_TTL,
    }

    response.set_cookie(
        key="lms_session",
        value=session_id,
        httponly=True,   # JS에서 접근 불가
        samesite="lax",
        max_age=60 * 60 * 8,  # 8시간
    )
    return LMSLoginResponse(success=True, user_name=info["user_name"])


@router.post("/logout")
async def lms_logout(response: Response, lms_session: Optional[str] = Cookie(default=None)):
    """세션 삭제."""
    if lms_session and lms_session in _sessions:
        del _sessions[lms_session]
    response.delete_cookie("lms_session")
    return {"success": True}


@router.get("/me")
async def lms_me(lms_session: Optional[str] = Cookie(default=None)):
    """현재 로그인 상태 확인."""
    if not lms_session or lms_session not in _sessions:
        return {"logged_in": False}
    session = _sessions[lms_session]
    return {"logged_in": True, "user_name": session["user_name"]}


@router.get("/data", response_model=LMSDataResponse)
async def lms_data(lms_session: Optional[str] = Cookie(default=None)):
    """
    수강강좌 / 과제 / 성적 / 캘린더 일괄 반환.
    로그인 쿠키 필요.
    """
    session = _get_session(lms_session)
    token = session["token"]
    user_id = session["user_id"]

    # 1. 강좌 목록
    try:
        raw_courses = lms_service.get_courses(token)
    except Exception:
        raw_courses = []

    courses = [Course(**c) for c in raw_courses]
    course_ids = [c.id for c in courses]

    # 2. 과제 목록
    try:
        raw_assigns = lms_service.get_assignments(token, course_ids)
    except Exception:
        raw_assigns = []

    # 3. 제출 여부 (과제가 있을 때만)
    if raw_assigns:
        try:
            assign_ids = [a["id"] for a in raw_assigns]
            submitted_map = lms_service.get_submission_statuses(token, assign_ids)
            for a in raw_assigns:
                a["submitted"] = submitted_map.get(a["id"], False)
        except Exception:
            pass

    assignments = [Assignment(**a) for a in raw_assigns]

    # 4. 성적
    try:
        raw_grades = lms_service.get_grades(token, user_id) if user_id else []
    except Exception:
        raw_grades = []

    grades = [Grade(**g) for g in raw_grades]

    # 5. 캘린더
    try:
        raw_calendar = lms_service.get_calendar(token, user_id) if user_id else []
    except Exception:
        raw_calendar = []

    calendar = [CalendarEvent(**e) for e in raw_calendar]

    return LMSDataResponse(
        courses=courses,
        assignments=assignments,
        grades=grades,
        calendar=calendar,
    )
