import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def parse_sse(text: str) -> list[dict]:
    events = []
    for line in text.split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


async def _fake_stream(*_, **__):
    yield "안녕"
    yield " 하세요"


class TestChatEndpoint(unittest.TestCase):

    def test_빈_메시지_400(self):
        res = client.post("/api/chat", json={"messages": [], "use_search": False})
        self.assertEqual(res.status_code, 400)

    @patch("app.routers.chat.stream_chat_response", side_effect=_fake_stream)
    def test_정상_요청_200(self, _):
        res = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "안녕"}],
            "use_search": False,
        })
        self.assertEqual(res.status_code, 200)

    @patch("app.routers.chat.stream_chat_response", side_effect=_fake_stream)
    def test_응답_미디어타입_event_stream(self, _):
        res = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "안녕"}],
            "use_search": False,
        })
        self.assertIn("text/event-stream", res.headers["content-type"])

    @patch("app.routers.chat.stream_chat_response", side_effect=_fake_stream)
    def test_cache_control_헤더(self, _):
        res = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "안녕"}],
            "use_search": False,
        })
        self.assertEqual(res.headers.get("cache-control"), "no-cache")

    @patch("app.routers.chat.stream_chat_response", side_effect=_fake_stream)
    def test_SSE_token_이벤트_포함(self, _):
        res = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "안녕"}],
            "use_search": False,
        })
        events = parse_sse(res.text)
        token_events = [e for e in events if e["type"] == "token"]
        self.assertGreater(len(token_events), 0)

    @patch("app.routers.chat.stream_chat_response", side_effect=_fake_stream)
    def test_SSE_done_이벤트_포함(self, _):
        res = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "안녕"}],
            "use_search": False,
        })
        events = parse_sse(res.text)
        self.assertEqual(events[-1]["type"], "done")


class TestChatEndpointWithSearch(unittest.TestCase):

    @patch("app.routers.chat.stream_chat_response", side_effect=_fake_stream)
    @patch("app.routers.chat.extract_unique_sources", return_value=["https://cbnu.ac.kr"])
    @patch("app.routers.chat.search_web", return_value=[{"title": "결과", "url": "https://cbnu.ac.kr", "content": "내용"}])
    @patch("app.routers.chat.optimize_search_query", new_callable=AsyncMock, return_value="충북대학교 입학")
    def test_웹검색_sources_이벤트_포함(self, *_):
        res = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "충북대 입학 알려줘"}],
            "use_search": True,
        })
        events = parse_sse(res.text)
        source_events = [e for e in events if e["type"] == "sources"]
        self.assertEqual(len(source_events), 1)
        self.assertIn("https://cbnu.ac.kr", source_events[0]["value"])

    @patch("app.routers.chat.stream_chat_response", side_effect=_fake_stream)
    @patch("app.routers.chat.extract_unique_sources", return_value=[])
    @patch("app.routers.chat.search_web", return_value=[])
    @patch("app.routers.chat.optimize_search_query", new_callable=AsyncMock, return_value="충북대학교 입학")
    def test_sources_없으면_sources_이벤트_없음(self, *_):
        res = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "충북대 입학"}],
            "use_search": True,
        })
        events = parse_sse(res.text)
        source_events = [e for e in events if e["type"] == "sources"]
        self.assertEqual(len(source_events), 0)


if __name__ == "__main__":
    unittest.main()
