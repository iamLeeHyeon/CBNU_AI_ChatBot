import time
import unittest
from app.services.lms_context import build_lms_context


class TestBuildLmsContext(unittest.TestCase):

    def test_빈_데이터는_빈_문자열_반환(self):
        self.assertEqual(build_lms_context({}), "")

    def test_수강_과목_포함(self):
        data = {"courses": [
            {"short_name": "OS", "full_name": "운영체제"},
            {"short_name": "DB", "full_name": "데이터베이스"},
        ]}
        result = build_lms_context(data)
        self.assertIn("OS", result)
        self.assertIn("DB", result)

    def test_미제출_임박_과제_D표시(self):
        due = int(time.time()) + int(2.5 * 86400)  # 2.5일 후 → D-2 보장
        data = {"assignments": [
            {"course_name": "알고리즘", "name": "과제1", "due_date": due, "submitted": False}
        ]}
        result = build_lms_context(data)
        self.assertIn("D-2", result)
        self.assertIn("과제1", result)

    def test_제출된_과제는_포함_안됨(self):
        due = int(time.time()) + 86400
        data = {"assignments": [
            {"course_name": "알고리즘", "name": "제출완료과제", "due_date": due, "submitted": True}
        ]}
        result = build_lms_context(data)
        self.assertNotIn("제출완료과제", result)

    def test_기한초과_과제_표시(self):
        due = int(time.time()) - 86400  # 어제
        data = {"assignments": [
            {"course_name": "알고리즘", "name": "늦은과제", "due_date": due, "submitted": False}
        ]}
        result = build_lms_context(data)
        self.assertIn("기한 초과", result)
        self.assertIn("늦은과제", result)

    def test_성적_포함(self):
        data = {"grades": [
            {"course_name": "운영체제", "item_name": "최종 성적", "grade": "A+", "max_grade": None}
        ]}
        result = build_lms_context(data)
        self.assertIn("A+", result)
        self.assertIn("운영체제", result)

    def test_성적_미공개(self):
        data = {"grades": [
            {"course_name": "데이터베이스", "item_name": "최종 성적", "grade": None, "max_grade": None}
        ]}
        result = build_lms_context(data)
        self.assertIn("미공개", result)


if __name__ == "__main__":
    unittest.main()
