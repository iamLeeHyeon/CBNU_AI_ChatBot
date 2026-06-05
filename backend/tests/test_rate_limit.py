import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_app():
    from app.middleware.rate_limit import RateLimitMiddleware
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.post("/api/chat")
    async def chat():
        return {"message": "ok"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


class TestGetClientIp(unittest.TestCase):

    def _make_middleware(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        return RateLimitMiddleware(MagicMock())

    def test_forwarded_for_헤더_사용(self):
        middleware = self._make_middleware()
        request = MagicMock()
        request.headers.get = lambda key, default=None: "1.2.3.4, 5.6.7.8" if key == "X-Forwarded-For" else default
        request.client.host = "127.0.0.1"
        self.assertEqual(middleware._get_client_ip(request), "1.2.3.4")

    def test_공백_제거(self):
        middleware = self._make_middleware()
        request = MagicMock()
        request.headers.get = lambda key, default=None: "  1.2.3.4  , 5.6.7.8" if key == "X-Forwarded-For" else default
        request.client.host = "127.0.0.1"
        self.assertEqual(middleware._get_client_ip(request), "1.2.3.4")

    def test_client_host_폴백(self):
        middleware = self._make_middleware()
        request = MagicMock()
        request.headers.get = lambda key, default=None: default
        request.client.host = "192.168.0.1"
        self.assertEqual(middleware._get_client_ip(request), "192.168.0.1")

    def test_client_없으면_unknown(self):
        middleware = self._make_middleware()
        request = MagicMock()
        request.headers.get = lambda key, default=None: default
        request.client = None
        self.assertEqual(middleware._get_client_ip(request), "unknown")


class TestRateLimitDispatch(unittest.TestCase):

    def test_비제한_경로_통과(self):
        client = TestClient(make_app())
        self.assertEqual(client.get("/health").status_code, 200)

    def test_제한_이내_요청_통과(self):
        client = TestClient(make_app())
        self.assertEqual(client.post("/api/chat").status_code, 200)

    def test_제한_초과시_429(self):
        from app.middleware.rate_limit import RATE_LIMIT_REQUESTS
        client = TestClient(make_app())
        for _ in range(RATE_LIMIT_REQUESTS):
            client.post("/api/chat")
        res = client.post("/api/chat")
        self.assertEqual(res.status_code, 429)

    def test_429_메시지_포함(self):
        from app.middleware.rate_limit import RATE_LIMIT_REQUESTS
        client = TestClient(make_app())
        for _ in range(RATE_LIMIT_REQUESTS):
            client.post("/api/chat")
        res = client.post("/api/chat")
        self.assertIn("요청이 너무 많습니다", res.json()["detail"])

    def test_429_retry_after_헤더(self):
        from app.middleware.rate_limit import RATE_LIMIT_REQUESTS
        client = TestClient(make_app())
        for _ in range(RATE_LIMIT_REQUESTS):
            client.post("/api/chat")
        res = client.post("/api/chat")
        self.assertIn("retry-after", res.headers)


if __name__ == "__main__":
    unittest.main()
