"""
tests/test_lms_api_extra.py
app/routers/lms.py 커버리지 보완 테스트
"""
import copy
import time
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.routers.lms import _sessions

FAKE_SESSION_ID = "extra-session-5678"
FAKE_DATA = {
    "user_name": "테스트학생",
    "courses": [{"id": 1, "full_name": "운영체제", "short_name": "OS"}],
    "assignments": [],
    "grades": [],
    "materials": [],
}


def _make_client(session_id: str | None = None) -> TestClient:
    c = TestClient(app, raise_server_exceptions=False)
    if session_id:
        c.cookies.set("lms_session", session_id)
    return c


def _inject_session(expires_offset: int = 3600):
    _sessions[FAKE_SESSION_ID] = {
        "student_id": "2024001",
        "token": "fake-token",
        "user_id": 999,
        "expires_at": time.time() + expires_offset,
        "data": copy.deepcopy(FAKE_DATA),
    }


class TestLMSAPIExtra(unittest.TestCase):

    def setUp(self):
        _sessions.clear()

    def tearDown(self):
        _sessions.clear()

    # ── 라인 32-33: get_token 500 에러 ───────────────────────────────
    @patch("app.services.lms.get_token", side_effect=Exception("서버 연결 실패"))
    def test_로그인_토큰_500(self, _):
        res = TestClient(app, raise_server_exceptions=False).post(
            "/api/lms/login", json={"student_id": "2024001", "password": "pw"}
        )
        self.assertEqual(res.status_code, 500)
        self.assertIn("LMS 서버 연결 실패", res.json()["detail"])

    # ── 라인 43-44: 로그인 후 데이터 조회 500 에러 ───────────────────
    @patch("app.services.lms.get_user_info", side_effect=Exception("데이터 조회 오류"))
    @patch("app.services.lms.get_token", return_value="token123")
    def test_로그인_데이터조회_500(self, *_):
        res = TestClient(app, raise_server_exceptions=False).post(
            "/api/lms/login", json={"student_id": "2024001", "password": "pw"}
        )
        self.assertEqual(res.status_code, 500)
        self.assertIn("LMS 데이터 조회 실패", res.json()["detail"])

    # ── 라인 56-61: 로그인 시 assignments 있을 때 제출 상태 조회 ──────
    @patch("app.services.lms.get_materials", return_value=[])
    @patch("app.services.lms.get_grades", return_value=[])
    @patch("app.services.lms.get_submission_statuses", return_value={1: True})
    @patch("app.services.lms.get_assignments", return_value=[
        {"id": 1, "name": "과제1", "due_date": 9999999999, "course_name": "운영체제"}
    ])
    @patch("app.services.lms.get_courses", return_value=[
        {"id": 10, "full_name": "운영체제", "short_name": "OS"}
    ])
    @patch("app.services.lms.get_user_info", return_value={"user_id": 1, "user_name": "홍길동"})
    @patch("app.services.lms.get_token", return_value="token123")
    def test_로그인_assignments_있을때_제출상태_조회(self, *_):
        res = TestClient(app).post(
            "/api/lms/login", json={"student_id": "2024001", "password": "pw"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

    # ── 라인 76-77: user_id 없을 때 grades 빈 리스트 ─────────────────
    @patch("app.services.lms.get_materials", return_value=[])
    @patch("app.services.lms.get_grades", return_value=[])
    @patch("app.services.lms.get_submission_statuses", return_value={})
    @patch("app.services.lms.get_assignments", return_value=[])
    @patch("app.services.lms.get_courses", return_value=[])
    @patch("app.services.lms.get_user_info", return_value={"user_id": None, "user_name": "학우"})
    @patch("app.services.lms.get_token", return_value="token123")
    def test_로그인_user_id_없으면_grades_빈리스트(self, *_):
        res = TestClient(app).post(
            "/api/lms/login", json={"student_id": "2024001", "password": "pw"}
        )
        self.assertEqual(res.status_code, 200)
        # grades 조회 없이 성공해야 함
        self.assertTrue(res.json()["success"])

    # ── 라인 116-121: sync 중 예외 500 ───────────────────────────────
    @patch("app.services.lms.get_courses", side_effect=Exception("동기화 오류"))
    def test_sync_예외시_500(self, _):
        _inject_session()
        res = _make_client(FAKE_SESSION_ID).post("/api/lms/sync")
        self.assertEqual(res.status_code, 500)
        self.assertIn("동기화 실패", res.json()["detail"])

    # ── 라인 136-137: sync 시 assignments 있을 때 제출 상태 조회 ──────
    @patch("app.services.lms.get_materials", return_value=[])
    @patch("app.services.lms.get_grades", return_value=[])
    @patch("app.services.lms.get_submission_statuses", return_value={1: False})
    @patch("app.services.lms.get_assignments", return_value=[
        {"id": 1, "name": "과제1", "due_date": 9999999999, "course_name": "운영체제"}
    ])
    @patch("app.services.lms.get_courses", return_value=[
        {"id": 10, "full_name": "운영체제", "short_name": "OS"}
    ])
    def test_sync_assignments_있을때_제출상태_조회(self, *_):
        _inject_session()
        res = _make_client(FAKE_SESSION_ID).post("/api/lms/sync")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])


if __name__ == "__main__":
    unittest.main()
