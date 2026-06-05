import unittest
from app.services.utils import normalize_url, is_cbnu_related, preprocess_context, extract_unique_sources


class TestNormalizeUrl(unittest.TestCase):

    def test_www_제거(self):
        result = normalize_url("https://www.cbnu.ac.kr")
        self.assertNotIn("www.", result)

    def test_소문자_변환(self):
        result = normalize_url("https://CBNU.ac.kr/Page")
        self.assertEqual(result, result.lower())

    def test_trailing_slash_제거(self):
        a = normalize_url("https://cbnu.ac.kr/notice/")
        b = normalize_url("https://cbnu.ac.kr/notice")
        self.assertEqual(a, b)

    def test_공백_제거(self):
        result = normalize_url("  https://cbnu.ac.kr  ")
        self.assertEqual(result, normalize_url("https://cbnu.ac.kr"))

    def test_같은_URL_동일하게_정규화(self):
        a = normalize_url("https://www.cbnu.ac.kr/")
        b = normalize_url("https://cbnu.ac.kr")
        self.assertEqual(a, b)


class TestIsCbnuRelated(unittest.TestCase):

    def test_제목에_키워드(self):
        self.assertTrue(is_cbnu_related("충북대학교 공지사항", "", ""))

    def test_내용에_키워드(self):
        self.assertTrue(is_cbnu_related("", "충북대 입학 안내", ""))

    def test_URL에_키워드(self):
        self.assertTrue(is_cbnu_related("", "", "https://cbnu.ac.kr"))

    def test_키워드_없으면_False(self):
        self.assertFalse(is_cbnu_related("서울대학교", "입학 안내", "https://snu.ac.kr"))

    def test_충북대_단축어(self):
        self.assertTrue(is_cbnu_related("충북대 소식", "", ""))


class TestPreprocessContext(unittest.TestCase):

    def _result(self, title="충북대학교 공지", url="https://cbnu.ac.kr", content="충북대 관련 내용", date=""):
        return {"title": title, "url": url, "content": content, "published_date": date}

    def test_빈_결과_빈_문자열(self):
        self.assertEqual(preprocess_context([]), "")

    def test_충북대_무관_필터링(self):
        result = preprocess_context([{"title": "서울대", "url": "https://snu.ac.kr", "content": "서울대 내용"}])
        self.assertEqual(result, "")

    def test_충북대_결과_포함(self):
        result = preprocess_context([self._result()])
        self.assertIn("충북대학교 공지", result)

    def test_URL_중복_제거(self):
        results = [
            self._result(url="https://cbnu.ac.kr/notice", content="충북대 내용 A"),
            self._result(url="https://cbnu.ac.kr/notice/", content="충북대 내용 B"),
        ]
        result = preprocess_context(results)
        self.assertEqual(result.count("[출처"), 1)

    def test_내용_길이_제한(self):
        long_content = "충북대 " + "가" * 2000
        result = preprocess_context([self._result(content=long_content)], max_chars_per_result=100)
        self.assertTrue(result.endswith("..."))

    def test_날짜_있으면_포함(self):
        result = preprocess_context([self._result(date="2024-01-01")])
        self.assertIn("2024-01-01", result)


class TestExtractUniqueSources(unittest.TestCase):

    def _result(self, url, title="충북대학교", content="충북대 내용"):
        return {"url": url, "title": title, "content": content}

    def test_빈_결과_빈_리스트(self):
        self.assertEqual(extract_unique_sources([]), [])

    def test_충북대_무관_제외(self):
        result = extract_unique_sources([{"url": "https://snu.ac.kr", "title": "서울대", "content": "서울대 내용"}])
        self.assertEqual(result, [])

    def test_충북대_URL_포함(self):
        result = extract_unique_sources([self._result("https://cbnu.ac.kr/notice")])
        self.assertIn("https://cbnu.ac.kr/notice", result)

    def test_중복_URL_제거(self):
        results = [
            self._result("https://cbnu.ac.kr/notice"),
            self._result("https://cbnu.ac.kr/notice/"),
        ]
        result = extract_unique_sources(results)
        self.assertEqual(len(result), 1)

    def test_여러_고유_URL_모두_포함(self):
        results = [
            self._result("https://cbnu.ac.kr/notice"),
            self._result("https://cbnu.ac.kr/news"),
        ]
        result = extract_unique_sources(results)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
