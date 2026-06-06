"""
tests/test_notices_api.py
app/routers/notices.py 유닛 테스트
"""
import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.notices import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


MOCK_NOTICES = [
    {"title": "공지1", "url": "https://www.cbnu.ac.kr/notice/1"},
    {"title": "공지2", "url": "https://www.cbnu.ac.kr/notice/2"},
]
MOCK_CALENDAR = [
    {"title": "수강신청", "url": "https://www.cbnu.ac.kr/calendar/1"},
]


# ════════════════════════════════════════════════════════════════
# 1. GET /api/notices
# ════════════════════════════════════════════════════════════════
class TestNoticesEndpoint:

    @patch("app.routers.notices.search_academic_calendar", return_value=MOCK_CALENDAR)
    @patch("app.routers.notices.search_notices", return_value=MOCK_NOTICES)
    def test_200_정상_반환(self, mock_notices, mock_calendar):
        res = client.get("/api/notices")
        assert res.status_code == 200

    @patch("app.routers.notices.search_academic_calendar", return_value=MOCK_CALENDAR)
    @patch("app.routers.notices.search_notices", return_value=MOCK_NOTICES)
    def test_notices_키_포함(self, mock_notices, mock_calendar):
        res = client.get("/api/notices")
        assert "notices" in res.json()

    @patch("app.routers.notices.search_academic_calendar", return_value=MOCK_CALENDAR)
    @patch("app.routers.notices.search_notices", return_value=MOCK_NOTICES)
    def test_academic_calendar_키_포함(self, mock_notices, mock_calendar):
        res = client.get("/api/notices")
        assert "academic_calendar" in res.json()

    @patch("app.routers.notices.search_academic_calendar", return_value=MOCK_CALENDAR)
    @patch("app.routers.notices.search_notices", return_value=MOCK_NOTICES)
    def test_notices_데이터_일치(self, mock_notices, mock_calendar):
        res = client.get("/api/notices")
        assert res.json()["notices"] == MOCK_NOTICES

    @patch("app.routers.notices.search_academic_calendar", return_value=MOCK_CALENDAR)
    @patch("app.routers.notices.search_notices", return_value=MOCK_NOTICES)
    def test_academic_calendar_데이터_일치(self, mock_notices, mock_calendar):
        res = client.get("/api/notices")
        assert res.json()["academic_calendar"] == MOCK_CALENDAR

    @patch("app.routers.notices.search_academic_calendar", return_value=[])
    @patch("app.routers.notices.search_notices", return_value=[])
    def test_빈_결과도_200(self, mock_notices, mock_calendar):
        res = client.get("/api/notices")
        assert res.status_code == 200
        assert res.json() == {"notices": [], "academic_calendar": []}

    @patch("app.routers.notices.search_notices", side_effect=Exception("API 오류"))
    def test_search_notices_예외시_500(self, mock_notices):
        res = client.get("/api/notices")
        assert res.status_code == 500

    @patch("app.routers.notices.search_notices", side_effect=Exception("API 오류"))
    def test_500_detail_메시지_포함(self, mock_notices):
        res = client.get("/api/notices")
        assert "API 오류" in res.json()["detail"]

    @patch("app.routers.notices.search_academic_calendar", side_effect=Exception("캘린더 오류"))
    @patch("app.routers.notices.search_notices", return_value=MOCK_NOTICES)
    def test_search_calendar_예외시_500(self, mock_notices, mock_calendar):
        res = client.get("/api/notices")
        assert res.status_code == 500
