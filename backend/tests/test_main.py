import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint(unittest.TestCase):

    def test_헬스체크_200(self):
        res = client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
