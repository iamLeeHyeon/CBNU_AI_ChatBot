"""
tests/test_notice_crawler.py
app/crawler/notice_crawler.py 유닛 테스트
"""
import pytest
from unittest.mock import MagicMock, patch

from app.crawler.notice_crawler import (
    is_allowed_url,
    _get_client,
    search_notices,
    search_academic_calendar,
    filter_by_allowed_domain,
    ALLOWED_DOMAINS,
)


# ════════════════════════════════════════════════════════════════
# 1. is_allowed_url
# ════════════════════════════════════════════════════════════════
class TestIsAllowedUrl:

    def test_허용_도메인_포함(self):
        assert is_allowed_url("https://www.cbnu.ac.kr/www/index.do") is True

    def test_허용_도메인_하위_경로(self):
        assert is_allowed_url("https://www.cbnu.ac.kr/service/index.do?lang=ko") is True

    def test_cbnu_루트(self):
        assert is_allowed_url("https://www.cbnu.ac.kr/some/page") is True

    def test_비허용_도메인(self):
        assert is_allowed_url("https://www.google.com") is False

    def test_빈_문자열(self):
        assert is_allowed_url("") is False

    def test_유사하지만_다른_도메인(self):
        assert is_allowed_url("https://fake-cbnu.ac.kr") is False

    def test_allowed_domains_상수_모두_통과(self):
        for domain in ALLOWED_DOMAINS:
            assert is_allowed_url(domain) is True


# ════════════════════════════════════════════════════════════════
# 2. _get_client
# ════════════════════════════════════════════════════════════════
class TestGetClient:

    @patch("app.crawler.notice_crawler.TavilyClient")
    def test_클라이언트_반환(self, mock_client_cls, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        _get_client()
        mock_client_cls.assert_called_once_with(api_key="test-key")

    def test_키_없으면_ValueError(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            _get_client()

    @patch("app.crawler.notice_crawler.TavilyClient")
    def test_키_있으면_예외_없음(self, mock_client_cls, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "valid-key")
        client = _get_client()
        assert client is not None


# ════════════════════════════════════════════════════════════════
# 3. search_notices
# ════════════════════════════════════════════════════════════════
class TestSearchNotices:

    def _mock_client(self, results):
        client = MagicMock()
        client.search.return_value = {"results": results}
        return client

    @patch("app.crawler.notice_crawler._get_client")
    def test_결과_반환(self, mock_get_client):
        mock_get_client.return_value = self._mock_client([
            {"url": "https://www.cbnu.ac.kr/notice/1", "title": "공지1"},
        ])
        result = search_notices()
        assert len(result) == 1
        assert result[0]["title"] == "공지1"

    @patch("app.crawler.notice_crawler._get_client")
    def test_올바른_쿼리_사용(self, mock_get_client):
        client = self._mock_client([])
        mock_get_client.return_value = client
        search_notices(max_results=3)
        _, kwargs = client.search.call_args
        assert "공지사항" in kwargs.get("query", "")
        assert kwargs.get("max_results") == 3

    @patch("app.crawler.notice_crawler._get_client")
    def test_results_키_없으면_빈_리스트(self, mock_get_client):
        client = MagicMock()
        client.search.return_value = {}
        mock_get_client.return_value = client
        assert search_notices() == []

    @patch("app.crawler.notice_crawler._get_client")
    def test_max_results_기본값_5(self, mock_get_client):
        client = self._mock_client([])
        mock_get_client.return_value = client
        search_notices()
        _, kwargs = client.search.call_args
        assert kwargs.get("max_results") == 5


# ════════════════════════════════════════════════════════════════
# 4. search_academic_calendar
# ════════════════════════════════════════════════════════════════
class TestSearchAcademicCalendar:

    def _mock_client(self, results):
        client = MagicMock()
        client.search.return_value = {"results": results}
        return client

    @patch("app.crawler.notice_crawler._get_client")
    def test_결과_반환(self, mock_get_client):
        mock_get_client.return_value = self._mock_client([
            {"url": "https://www.cbnu.ac.kr/calendar", "title": "학사일정"},
        ])
        result = search_academic_calendar()
        assert len(result) == 1

    @patch("app.crawler.notice_crawler._get_client")
    def test_올바른_쿼리_사용(self, mock_get_client):
        client = self._mock_client([])
        mock_get_client.return_value = client
        search_academic_calendar()
        _, kwargs = client.search.call_args
        assert "학사일정" in kwargs.get("query", "")

    @patch("app.crawler.notice_crawler._get_client")
    def test_results_키_없으면_빈_리스트(self, mock_get_client):
        client = MagicMock()
        client.search.return_value = {}
        mock_get_client.return_value = client
        assert search_academic_calendar() == []

    @patch("app.crawler.notice_crawler._get_client")
    def test_max_results_전달(self, mock_get_client):
        client = self._mock_client([])
        mock_get_client.return_value = client
        search_academic_calendar(max_results=10)
        _, kwargs = client.search.call_args
        assert kwargs.get("max_results") == 10


# ════════════════════════════════════════════════════════════════
# 5. filter_by_allowed_domain
# ════════════════════════════════════════════════════════════════
class TestFilterByAllowedDomain:

    def test_허용_도메인만_남김(self):
        results = [
            {"url": "https://www.cbnu.ac.kr/notice/1"},
            {"url": "https://www.google.com/search"},
        ]
        filtered = filter_by_allowed_domain(results)
        assert len(filtered) == 1
        assert filtered[0]["url"].startswith("https://www.cbnu.ac.kr")

    def test_허용_결과_없으면_원본_반환(self):
        results = [
            {"url": "https://www.google.com"},
            {"url": "https://naver.com"},
        ]
        assert filter_by_allowed_domain(results) == results

    def test_빈_리스트_입력(self):
        assert filter_by_allowed_domain([]) == []

    def test_전체_허용_도메인이면_전부_통과(self):
        results = [
            {"url": "https://www.cbnu.ac.kr/page1"},
            {"url": "https://www.cbnu.ac.kr/page2"},
        ]
        assert len(filter_by_allowed_domain(results)) == 2

    def test_url_키_없는_항목_처리(self):
        results = [{"title": "url 없음"}]
        assert filter_by_allowed_domain(results) == results

    def test_혼합_결과_필터링(self):
        results = [
            {"url": "https://www.cbnu.ac.kr/notice"},
            {"url": "https://other.com"},
            {"url": "https://www.cbnu.ac.kr/calendar"},
        ]
        filtered = filter_by_allowed_domain(results)
        assert len(filtered) == 2
        for r in filtered:
            assert r["url"].startswith("https://www.cbnu.ac.kr")
