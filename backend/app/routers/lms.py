import uuid
from fastapi import APIRouter, HTTPException, Cookie, Response
from typing import Optional
from fastapi.concurrency import run_in_threadpool

from app.models.schemas import LMSLoginRequest

# 👇 1. 두 가지 무기를 모두 임포트합니다.
from app.services import lms as lms_api_service       # Plan A: 초고속 API 방식
from app.crawler.lms_crawler import get_lms_data      # Plan B: 무적의 크롤러 방식

router = APIRouter(prefix="/api/lms", tags=["lms"])
_sessions: dict[str, dict] = {}

@router.post("/login")
async def lms_login(req: LMSLoginRequest, response: Response):
    student_id = getattr(req, 'student_id', getattr(req, 'username', ''))
    password = req.password
    
    crawled_data = None
    user_name = "학우"
    
    # ==========================================
    # 🥇 Plan A: API(httpx) 방식으로 먼저 시도!
    # ==========================================
    try:
        print("🚀 [Plan A] API 방식으로 LMS 로그인 시도 중...")
        token = lms_api_service.get_token(student_id, password)
        info = lms_api_service.get_user_info(token)
        user_name = info.get("user_name", "학우")
        
        courses_api = lms_api_service.get_courses(token)
        course_ids = [c["id"] for c in courses_api]
        assignments_api = lms_api_service.get_assignments(token, course_ids)
        
        # 제출 여부 매핑
        if assignments_api:
            assign_ids = [a["id"] for a in assignments_api]
            submitted_map = lms_api_service.get_submission_statuses(token, assign_ids)
            for a in assignments_api:
                a["submitted"] = submitted_map.get(a["id"], False)
                
        assignments_api.sort(key=lambda x: x.get("due_date") or "9999-12-31")
        
        crawled_data = {
            "user_name": user_name,
            "courses": courses_api,
            "assignments": assignments_api,
            "materials": [] # 자료는 API에 없으면 빈칸
        }
        print("✅ [Plan A] API 로그인 및 데이터 수집 성공!")
        
    except ValueError as e:
        # 비밀번호가 진짜 틀린 거면 크롤러도 시도할 필요 없이 바로 입구컷!
        raise HTTPException(status_code=401, detail=str(e))
        
    except Exception as api_error:
        # ==========================================
        # 🥈 Plan B: API 실패 시, 크롤러로 자동 우회!
        # ==========================================
        print(f"⚠️ [Plan A 실패] 사유: {api_error}")
        print("🤖 [Plan B] 무적의 Playwright 크롤러로 우회합니다...")
        
        try:
            crawled_data = await run_in_threadpool(get_lms_data, student_id, password)
            user_name = crawled_data.get("user_name", "학우")
            print("✅ [Plan B] 크롤러 우회 로그인 및 수집 성공!")
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            # 크롤러마저 실패하면 그때서야 진짜 서버 에러를 뱉습니다.
            raise HTTPException(status_code=500, detail=f"LMS 서버 연결 완전 실패 (API/크롤러 모두 다운됨): {str(e)}")

    # ------------------------------------------
    # 성공적으로 모인 데이터를 세션과 쿠키에 저장
    # ------------------------------------------
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "student_id": student_id,
        "data": crawled_data 
    }

    response.set_cookie(
        key="lms_session",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    
    return {
        "success": True, 
        "message": "로그인 및 데이터 동기화 완료",
        "user_name": user_name
    }
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

@router.get("/dashboard")
async def lms_dashboard(lms_session: Optional[str] = Cookie(default=None)):
    """현재 로그인된 세션의 대시보드 통합 데이터(강좌, 과제, 이름 등)를 반환합니다."""
    if not lms_session or lms_session not in _sessions:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다. 다시 로그인하세요.")
    
    session_info = _sessions[lms_session]
    return {
        "success": True,
        "user_name": session_info["data"].get("user_name", "학우"),
        "courses": session_info["data"].get("courses", []),
        "assignments": session_info["data"].get("assignments", [])
    }    