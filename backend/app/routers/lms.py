import uuid
import time
from fastapi import APIRouter, HTTPException, Cookie, Response
from typing import Optional
from fastapi.concurrency import run_in_threadpool

from app.models.schemas import LMSLoginRequest
import app.services.lms as lms_service

router = APIRouter(prefix="/api/lms", tags=["lms"])

# 서버 메모리 세션 저장소: { session_id: { "token": ..., "user_id": ..., "expires_at": ..., "data": {...} } }
_sessions: dict[str, dict] = {}
_SESSION_TTL = 60 * 60 * 8  # 8시간 (쿠키 max_age와 동일)


def _cleanup_sessions() -> None:
    """만료된 세션 정리."""
    now = time.time()
    expired = [k for k, v in _sessions.items() if now > v.get("expires_at", 0)]
    for k in expired:
        del _sessions[k]


def _get_session(session_id: Optional[str]) -> dict:
    """세션 ID로 세션 데이터 조회. 없거나 만료됐으면 401."""
    _cleanup_sessions()
    if not session_id or session_id not in _sessions:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    session = _sessions[session_id]
    if time.time() > session.get("expires_at", 0):
        del _sessions[session_id]
        raise HTTPException(status_code=401, detail="세션이 만료됐습니다. 다시 로그인하세요.")
    return session


@router.post("/login")
async def lms_login(req: LMSLoginRequest, response: Response):
    try:
        token = await run_in_threadpool(lms_service.get_token, req.student_id, req.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LMS 서버 연결 실패: {str(e)}")

    try:
        user_info = await run_in_threadpool(lms_service.get_user_info, token)
        user_id = user_info.get("user_id")
        user_name = user_info.get("user_name", "학우")

        raw_courses = await run_in_threadpool(lms_service.get_courses, token)
        course_ids = [c["id"] for c in raw_courses]

        raw_assigns = await run_in_threadpool(lms_service.get_assignments, token, course_ids)
        if raw_assigns:
            assign_ids = [a["id"] for a in raw_assigns]
            submitted_map = await run_in_threadpool(
                lms_service.get_submission_statuses, token, assign_ids
            )
            for a in raw_assigns:
                a["submitted"] = submitted_map.get(a["id"], False)

        all_grades = (
            await run_in_threadpool(lms_service.get_grades, token, user_id)
            if user_id else []
        )
        course_id_set = set(course_ids)
        course_name_map = {c["id"]: c["full_name"] for c in raw_courses}
        raw_grades = [
            {**g, "course_name": course_name_map.get(g.get("course_id"), g.get("course_name", ""))}
            for g in all_grades
            if g.get("course_id") in course_id_set
        ]
        raw_materials = await run_in_threadpool(lms_service.get_materials, token, course_ids)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LMS 데이터 조회 실패: {str(e)}")

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "student_id": req.student_id,
        "token": token,
        "user_id": user_id,
        "expires_at": time.time() + _SESSION_TTL,
        "data": {
            "user_name": user_name,
            "courses": raw_courses,       # [{id, full_name, short_name}]
            "assignments": raw_assigns,   # [{id, course_name, name, due_date(Unix), submitted}]
            "grades": raw_grades,
            "materials": raw_materials,   # [{title, url, course_id}]
        },
    }

    response.set_cookie(
        key="lms_session",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    return {"success": True, "message": "로그인 및 데이터 동기화 완료", "user_name": user_name}


@router.post("/sync")
async def lms_sync(lms_session: Optional[str] = Cookie(default=None)):
    session = _get_session(lms_session)
    token = session["token"]
    user_id = session["user_id"]

    try:
        raw_courses = await run_in_threadpool(lms_service.get_courses, token)
        course_ids = [c["id"] for c in raw_courses]

        raw_assigns = await run_in_threadpool(lms_service.get_assignments, token, course_ids)
        if raw_assigns:
            assign_ids = [a["id"] for a in raw_assigns]
            submitted_map = await run_in_threadpool(
                lms_service.get_submission_statuses, token, assign_ids
            )
            for a in raw_assigns:
                a["submitted"] = submitted_map.get(a["id"], False)

        all_grades = (
            await run_in_threadpool(lms_service.get_grades, token, user_id)
            if user_id else []
        )
        course_id_set = set(course_ids)
        course_name_map = {c["id"]: c["full_name"] for c in raw_courses}
        raw_grades = [
            {**g, "course_name": course_name_map.get(g.get("course_id"), g.get("course_name", ""))}
            for g in all_grades
            if g.get("course_id") in course_id_set
        ]
        raw_materials = await run_in_threadpool(lms_service.get_materials, token, course_ids)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"동기화 실패: {str(e)}")

    _sessions[lms_session]["data"].update({
        "courses": raw_courses,
        "assignments": raw_assigns,
        "grades": raw_grades,
        "materials": raw_materials,
    })
    return {"success": True, "message": "동기화 완료"}


@router.get("/assignments")
async def lms_assignments(lms_session: Optional[str] = Cookie(default=None)):
    session = _get_session(lms_session)
    return {"assignments": session["data"].get("assignments", [])}


@router.get("/materials")
async def lms_materials(lms_session: Optional[str] = Cookie(default=None)):
    session = _get_session(lms_session)
    return {"materials": session["data"].get("materials", [])}


@router.post("/logout")
async def lms_logout(response: Response, lms_session: Optional[str] = Cookie(default=None)):
    if lms_session and lms_session in _sessions:
        del _sessions[lms_session]
    response.delete_cookie("lms_session")
    return {"success": True}


@router.get("/dashboard")
async def lms_dashboard(lms_session: Optional[str] = Cookie(default=None)):
    session = _get_session(lms_session)
    data = session["data"]
    return {
        "success": True,
        "user_name": data.get("user_name", "학우"),
        "courses": data.get("courses", []),
        "assignments": data.get("assignments", []),
        "grades": data.get("grades", []),
    }
