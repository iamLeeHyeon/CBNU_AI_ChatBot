from fastapi import APIRouter, HTTPException
from app.crawler.notice_crawler import search_notices, search_academic_calendar

router = APIRouter(prefix="/api", tags=["notices"])


@router.get("/notices")
async def notices():
    """충북대 공지사항 및 학사일정을 반환합니다."""
    try:
        return {
            "notices": search_notices(),
            "academic_calendar": search_academic_calendar(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
