import unittest
from unittest.mock import patch, MagicMock
from app.services.lms import (
    _rest, get_token, get_user_info, get_courses,
    get_assignments, get_submission_statuses,
    get_grades, get_materials,
)


class TestRest(unittest.TestCase):

    @patch("app.services.lms.httpx.post")
    def test_정상_응답(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key": "value"}
        mock_post.return_value = mock_resp
        result = _rest("token", "core_webservice_get_site_info")
        self.assertEqual(result, {"key": "value"})

    @patch("app.services.lms.httpx.post")
    def test_lms_exception_필드_있으면_ValueError(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "exception": "moodle_exception",
            "message": "접근 권한이 없습니다.",
        }
        mock_post.return_value = mock_resp
        with self.assertRaises(ValueError) as ctx:
            _rest("token", "some_function")
        self.assertIn("접근 권한", str(ctx.exception))


class TestGetToken(unittest.TestCase):

    @patch("app.services.lms.httpx.post")
    def test_토큰_발급_성공(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"token": "abc123"}
        mock_post.return_value = mock_resp
        token = get_token("2024001", "password")
        self.assertEqual(token, "abc123")

    @patch("app.services.lms.httpx.post")
    def test_토큰_발급_실패_ValueError(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": "아이디 또는 비밀번호를 확인하세요."}
        mock_post.return_value = mock_resp
        with self.assertRaises(ValueError):
            get_token("2024001", "wrong")


class TestGetUserInfo(unittest.TestCase):

    @patch("app.services.lms._rest")
    def test_사용자_정보_fullname(self, mock_rest):
        mock_rest.return_value = {"fullname": "홍길동", "userid": 999}
        info = get_user_info("token")
        self.assertEqual(info["user_name"], "홍길동")
        self.assertEqual(info["user_id"], 999)

    @patch("app.services.lms._rest")
    def test_사용자_정보_firstname_lastname(self, mock_rest):
        mock_rest.return_value = {"fullname": "", "firstname": "길동", "lastname": "홍", "userid": 1}
        info = get_user_info("token")
        self.assertEqual(info["user_name"], "홍길동")


class TestGetCourses(unittest.TestCase):

    @patch("app.services.lms._rest")
    def test_강좌_목록_리스트_응답(self, mock_rest):
        mock_rest.return_value = [
            {"id": 1, "fullname": "운영체제", "shortname": "OS"},
            {"id": 2, "fullname": "데이터베이스", "shortname": "DB"},
        ]
        courses = get_courses("token")
        self.assertEqual(len(courses), 2)
        self.assertEqual(courses[0]["short_name"], "OS")

    @patch("app.services.lms._rest")
    def test_강좌_목록_딕셔너리_응답(self, mock_rest):
        mock_rest.return_value = {
            "courses": [{"id": 3, "fullname": "알고리즘", "shortname": "AL"}]
        }
        courses = get_courses("token")
        self.assertEqual(courses[0]["full_name"], "알고리즘")


class TestGetAssignments(unittest.TestCase):

    @patch("app.services.lms._rest")
    def test_과제_목록_반환(self, mock_rest):
        mock_rest.return_value = {
            "courses": [{
                "fullname": "운영체제",
                "assignments": [
                    {"id": 10, "cmid": 20, "name": "과제1", "duedate": 9999999999}
                ]
            }]
        }
        result = get_assignments("token", [1])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "과제1")
        self.assertFalse(result[0]["submitted"])

    @patch("app.services.lms._rest")
    def test_빈_course_ids(self, mock_rest):
        result = get_assignments("token", [])
        self.assertEqual(result, [])
        mock_rest.assert_not_called()

    @patch("app.services.lms._rest")
    def test_마감일_0이면_None(self, mock_rest):
        mock_rest.return_value = {
            "courses": [{
                "fullname": "OS",
                "assignments": [{"id": 1, "cmid": 2, "name": "과제", "duedate": 0}]
            }]
        }
        result = get_assignments("token", [1])
        self.assertIsNone(result[0]["due_date"])


class TestGetSubmissionStatuses(unittest.TestCase):

    @patch("app.services.lms._rest")
    def test_제출_완료(self, mock_rest):
        mock_rest.return_value = {
            "lastattempt": {"submission": {"status": "submitted"}}
        }
        result = get_submission_statuses("token", [1])
        self.assertTrue(result[1])

    @patch("app.services.lms._rest")
    def test_미제출(self, mock_rest):
        mock_rest.return_value = {
            "lastattempt": {"submission": {"status": "draft"}}
        }
        result = get_submission_statuses("token", [1])
        self.assertFalse(result[1])

    @patch("app.services.lms._rest")
    def test_오류_시_False(self, mock_rest):
        mock_rest.side_effect = Exception("API 오류")
        result = get_submission_statuses("token", [1])
        self.assertFalse(result[1])


class TestGetGrades(unittest.TestCase):

    @patch("app.services.lms._rest")
    def test_성적_반환(self, mock_rest):
        mock_rest.return_value = {
            "grades": [
                {"courseid": 1, "coursefullname": "운영체제", "grade": "A+"}
            ]
        }
        result = get_grades("token", 999)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["grade"], "A+")
        self.assertEqual(result[0]["item_name"], "최종 성적")

    @patch("app.services.lms._rest")
    def test_빈_성적(self, mock_rest):
        mock_rest.return_value = {"grades": []}
        result = get_grades("token", 999)
        self.assertEqual(result, [])


class TestGetMaterials(unittest.TestCase):

    @patch("app.services.lms._rest")
    def test_강의자료_반환(self, mock_rest):
        mock_rest.return_value = [
            {
                "modules": [
                    {"modname": "resource", "name": "강의PPT", "url": "https://lms/file"},
                    {"modname": "quiz", "name": "퀴즈", "url": "https://lms/quiz"},
                ]
            }
        ]
        result = get_materials("token", [1])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "강의PPT")

    @patch("app.services.lms._rest")
    def test_오류_강좌는_스킵(self, mock_rest):
        mock_rest.side_effect = Exception("오류")
        result = get_materials("token", [1, 2])
        self.assertEqual(result, [])

    @patch("app.services.lms._rest")
    def test_빈_course_ids(self, mock_rest):
        result = get_materials("token", [])
        self.assertEqual(result, [])
        mock_rest.assert_not_called()


if __name__ == "__main__":
    unittest.main()
