import copy
import time
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.routers.lms import _sessions

FAKE_SESSION_ID = "test-session-1234"
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
        "data": copy.deepcopy(FAKE_DATA),  # sync 등 update 호출 시 FAKE_DATA 오염 방지
    }


class TestLMSAPI(unittest.TestCase):

    def setUp(self):
        _sessions.clear()

    def tearDown(self):
        _sessions.clear()

    @patch("app.services.lms.get_materials", return_value=[])
    @patch("app.services.lms.get_grades", return_value=[])
    @patch("app.services.lms.get_submission_statuses", return_value={})
    @patch("app.services.lms.get_assignments", return_value=[])
    @patch("app.services.lms.get_courses", return_value=[])
    @patch("app.services.lms.get_user_info", return_value={"user_id": 1, "user_name": "홍길동"})
    @patch("app.services.lms.get_token", return_value="token123")
    def test_lms_로그인_성공(self, *_):
        res = TestClient(app).post("/api/lms/login", json={"student_id": "2024001", "password": "pw"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(res.json()["user_name"], "홍길동")

    @patch("app.services.lms.get_token", side_effect=ValueError("로그인 실패"))
    def test_lms_로그인_비밀번호_오류(self, _):
        res = TestClient(app, raise_server_exceptions=False).post(
            "/api/lms/login", json={"student_id": "2024001", "password": "wrong"}
        )
        self.assertEqual(res.status_code, 401)

    def test_대시보드_세션_없으면_401(self):
        res = TestClient(app, raise_server_exceptions=False).get("/api/lms/dashboard")
        self.assertEqual(res.status_code, 401)

    def test_대시보드_세션_있으면_200(self):
        _inject_session()
        res = _make_client(FAKE_SESSION_ID).get("/api/lms/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user_name"], "테스트학생")
        self.assertEqual(len(res.json()["courses"]), 1)

    def test_만료된_세션은_401(self):
        _inject_session(expires_offset=-1)  # 이미 만료
        res = _make_client(FAKE_SESSION_ID).get("/api/lms/dashboard")
        self.assertEqual(res.status_code, 401)

    def test_로그아웃_후_세션_삭제(self):
        _inject_session()
        res = _make_client(FAKE_SESSION_ID).post("/api/lms/logout")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(FAKE_SESSION_ID, _sessions)

    def test_로그아웃_세션없어도_200(self):
        res = TestClient(app, raise_server_exceptions=False).post("/api/lms/logout")
        self.assertEqual(res.status_code, 200)

    # ── sync ─────────────────────────────────────────────────────────

    @patch("app.services.lms.get_materials", return_value=[])
    @patch("app.services.lms.get_grades", return_value=[])
    @patch("app.services.lms.get_submission_statuses", return_value={})
    @patch("app.services.lms.get_assignments", return_value=[])
    @patch("app.services.lms.get_courses", return_value=[])
    def test_sync_성공(self, *_):
        _inject_session()
        res = _make_client(FAKE_SESSION_ID).post("/api/lms/sync")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

    def test_sync_세션없으면_401(self):
        res = TestClient(app, raise_server_exceptions=False).post("/api/lms/sync")
        self.assertEqual(res.status_code, 401)

    # ── assignments ──────────────────────────────────────────────────

    def test_assignments_조회_성공(self):
        _inject_session()
        res = _make_client(FAKE_SESSION_ID).get("/api/lms/assignments")
        self.assertEqual(res.status_code, 200)
        self.assertIn("assignments", res.json())

    def test_assignments_세션없으면_401(self):
        res = TestClient(app, raise_server_exceptions=False).get("/api/lms/assignments")
        self.assertEqual(res.status_code, 401)

    # ── materials ────────────────────────────────────────────────────

    def test_materials_조회_성공(self):
        _inject_session()
        res = _make_client(FAKE_SESSION_ID).get("/api/lms/materials")
        self.assertEqual(res.status_code, 200)
        self.assertIn("materials", res.json())

    def test_materials_세션없으면_401(self):
        res = TestClient(app, raise_server_exceptions=False).get("/api/lms/materials")
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
