import uuid
from fastapi import APIRouter, HTTPException, Cookie, Response
from typing import Optional

# 스키마는 두 브랜치에서 필요한 것만 가져옵니다.
from app.models.schemas import LMSLoginRequest
# 팀원이 만든 크롤러 모듈을 임포트합니다.
from app.crawler.lms_crawler import get_lms_data

router = APIRouter(prefix="/api/lms", tags=["lms"])

# 서버 메모리 세션 저장소: { session_id: { "student_id": ..., "data": ... } }
# (팀원의 불안전한 global 변수 대신 이 방식을 사용합니다)
_sessions: dict[str, dict] = {}


@router.post("/login")
async def lms_login(req: LMSLoginRequest, response: Response):
    """
    학번과 비밀번호로 LMS에 로그인하고 크롤링 데이터를 세션에 저장합니다.
    """
    # req.username인지 req.student_id인지는 스키마 정의에 따라 다를 수 있으니 유연하게 처리
    student_id = getattr(req, 'student_id', getattr(req, 'username', ''))
    
    try:
        # 팀원의 크롤러 함수 호출
        crawled_data = get_lms_data(student_id, req.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LMS 서버 연결 실패: {str(e)}")

    # 안전한 고유 세션 발급
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "student_id": student_id,
        "data": crawled_data  # 크롤링한 데이터를 해당 유저의 세션에만 보관
    }

    # 브라우저에 쿠키 심기
    response.set_cookie(
        key="lms_session",
        value=session_id,
        httponly=True,   # JS에서 접근 불가 (보안)
        samesite="lax",
        max_age=60 * 60 * 8,  # 8시간 유지
    )
    return {"success": True, "message": "로그인 및 데이터 동기화 완료"}


@router.get("/assignments")
async def lms_assignments(lms_session: Optional[str] = Cookie(default=None)):
    """현재 로그인된 세션의 과제 목록을 반환합니다."""
    if not lms_session or lms_session not in _sessions:
        raise HTTPException(status_code=401, detail="먼저 /api/lms/login으로 로그인하세요.")
    
    session_data = _sessions[lms_session]["data"]
    return {"assignments": session_data.get("assignments", [])}


@router.get("/materials")
async def lms_materials(lms_session: Optional[str] = Cookie(default=None)):
    """현재 로그인된 세션의 강의자료 목록을 반환합니다."""
    if not lms_session or lms_session not in _sessions:
        raise HTTPException(status_code=401, detail="먼저 /api/lms/login으로 로그인하세요.")
    
    session_data = _sessions[lms_session]["data"]
    return {"materials": session_data.get("materials", [])}


@router.post("/logout")
async def lms_logout(response: Response, lms_session: Optional[str] = Cookie(default=None)):
    """로그아웃 및 세션 파기"""
    if lms_session and lms_session in _sessions:
        del _sessions[lms_session]
    response.delete_cookie("lms_session")
    return {"success": True}