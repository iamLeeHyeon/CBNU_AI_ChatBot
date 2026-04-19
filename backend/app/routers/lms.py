from fastapi import APIRouter, HTTPException
from app.models.schemas import LMSLoginRequest
from app.crawler.lms_crawler import get_lms_data

router = APIRouter(prefix="/api/lms", tags=["lms"])

# 세션 내 크롤링 캐시 (로그인 후 데이터를 메모리에 보관)
_cached_data: dict | None = None


@router.post("/login")
async def lms_login(req: LMSLoginRequest):
    """학번과 비밀번호로 LMS 로그인 후 강의자료 + 과제를 반환합니다."""
    global _cached_data
    try:
        _cached_data = get_lms_data(req.student_id, req.password)
        return _cached_data
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments")
async def lms_assignments():
    """캐시된 LMS 데이터에서 과제 목록(마감일 정렬)을 반환합니다."""
    if not _cached_data:
        raise HTTPException(status_code=400, detail="먼저 /api/lms/login으로 로그인하세요.")
    return {"assignments": _cached_data.get("assignments", [])}


@router.get("/materials")
async def lms_materials():
    """캐시된 LMS 데이터에서 강의자료 목록을 반환합니다."""
    if not _cached_data:
        raise HTTPException(status_code=400, detail="먼저 /api/lms/login으로 로그인하세요.")
    return {"materials": _cached_data.get("materials", [])}
