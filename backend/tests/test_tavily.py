import unittest
from unittest.mock import MagicMock, patch

from app.services.tavily import _get_client


class TestGetClient(unittest.TestCase):

    def setUp(self):
        _get_client.cache_clear()

    def test_TavilyClient_반환(self):
        mock_client = MagicMock()
        with patch("app.services.tavily.TavilyClient", return_value=mock_client), \
             patch("app.services.tavily.os.getenv", return_value="test-key"):
            result = _get_client()
        self.assertIs(result, mock_client)

    def test_api_key_env에서_읽음(self):
        with patch("app.services.tavily.TavilyClient") as mock_cls, \
             patch("app.services.tavily.os.getenv", return_value="my-key"):
            _get_client()
        mock_cls.assert_called_once_with(api_key="my-key")

    def test_싱글톤_같은_인스턴스(self):
        mock_client = MagicMock()
        with patch("app.services.tavily.TavilyClient", return_value=mock_client), \
             patch("app.services.tavily.os.getenv", return_value="key"):
            r1 = _get_client()
            r2 = _get_client()
        self.assertIs(r1, r2)


class TestSearchWeb(unittest.TestCase):

    def setUp(self):
        _get_client.cache_clear()

    def _mock_client(self, results=None):
        client = MagicMock()
        client.search.return_value = {"results": results or []}
        return client

    def test_결과_리스트_반환(self):
        from app.services.tavily import search_web
        mock_results = [{"title": "충북대 공지", "url": "https://cbnu.ac.kr"}]
        client = self._mock_client(mock_results)
        with patch("app.services.tavily._get_client", return_value=client):
            result = search_web("충북대학교 입학")
        self.assertEqual(result, mock_results)

    def test_빈_결과_빈_리스트(self):
        from app.services.tavily import search_web
        client = self._mock_client([])
        with patch("app.services.tavily._get_client", return_value=client):
            result = search_web("검색어")
        self.assertEqual(result, [])

    def test_results_키_없으면_빈_리스트(self):
        from app.services.tavily import search_web
        client = self._mock_client()
        client.search.return_value = {}
        with patch("app.services.tavily._get_client", return_value=client):
            result = search_web("검색어")
        self.assertEqual(result, [])

    def test_search_depth_advanced(self):
        from app.services.tavily import search_web
        client = self._mock_client()
        with patch("app.services.tavily._get_client", return_value=client):
            search_web("충북대")
        call_kwargs = client.search.call_args[1]
        self.assertEqual(call_kwargs["search_depth"], "advanced")

    def test_query_전달(self):
        from app.services.tavily import search_web
        client = self._mock_client()
        with patch("app.services.tavily._get_client", return_value=client):
            search_web("충북대 도서관")
        call_kwargs = client.search.call_args[1]
        self.assertEqual(call_kwargs["query"], "충북대 도서관")

    def test_max_results_전달(self):
        from app.services.tavily import search_web
        client = self._mock_client()
        with patch("app.services.tavily._get_client", return_value=client):
            search_web("충북대", max_results=5)
        call_kwargs = client.search.call_args[1]
        self.assertEqual(call_kwargs["max_results"], 5)


if __name__ == "__main__":
    unittest.main()
