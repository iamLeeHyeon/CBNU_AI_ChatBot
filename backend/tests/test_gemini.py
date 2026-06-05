import json
import unittest
from unittest.mock import MagicMock, patch

from app.models.schemas import Message


def _msg(role, content):
    return Message(role=role, content=content)


def _make_response(finish_reason, text="응답"):
    candidate = MagicMock()
    candidate.finish_reason.name = finish_reason
    resp = MagicMock()
    resp.text = text
    resp.candidates = [candidate]
    return resp


class TestFormatMessagesAsHistory(unittest.TestCase):

    def test_user_role_유지(self):
        from app.services.gemini import _format_messages_as_history
        result = _format_messages_as_history([_msg("user", "안녕")])
        self.assertEqual(result[0]["role"], "user")

    def test_assistant_role_model로_변환(self):
        from app.services.gemini import _format_messages_as_history
        result = _format_messages_as_history([_msg("assistant", "반가워")])
        self.assertEqual(result[0]["role"], "model")

    def test_content_parts에_포함(self):
        from app.services.gemini import _format_messages_as_history
        result = _format_messages_as_history([_msg("user", "질문")])
        self.assertEqual(result[0]["parts"], ["질문"])

    def test_빈_리스트_반환(self):
        from app.services.gemini import _format_messages_as_history
        self.assertEqual(_format_messages_as_history([]), [])

    def test_순서_유지(self):
        from app.services.gemini import _format_messages_as_history
        msgs = [_msg("user", "A"), _msg("assistant", "B"), _msg("user", "C")]
        roles = [r["role"] for r in _format_messages_as_history(msgs)]
        self.assertEqual(roles, ["user", "model", "user"])


class TestSummarizeHistory(unittest.TestCase):

    @patch("app.services.gemini.get_model")
    def test_요약_prefix_포함(self, mock_get_model):
        from app.services.gemini import _summarize_history
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text="핵심 요약")
        mock_get_model.return_value = mock_model
        result = _summarize_history([_msg("user", "A"), _msg("assistant", "B")])
        self.assertTrue(result.startswith("[이전 대화 요약]:"))

    @patch("app.services.gemini.get_model")
    def test_요약_내용_포함(self, mock_get_model):
        from app.services.gemini import _summarize_history
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text="학과 일정 안내")
        mock_get_model.return_value = mock_model
        result = _summarize_history([_msg("user", "질문")])
        self.assertIn("학과 일정 안내", result)


class TestBuildHistory(unittest.TestCase):

    @patch("app.services.gemini._summarize_history")
    @patch("app.services.gemini._format_messages_as_history", return_value=[])
    def test_짧은_히스토리_요약_안함(self, _, mock_sum):
        from app.services.gemini import _build_history
        _build_history([_msg("user", "질문")] * 4)
        mock_sum.assert_not_called()

    @patch("app.services.gemini._summarize_history", return_value="[이전 대화 요약]: 요약")
    @patch("app.services.gemini._format_messages_as_history", return_value=[])
    def test_긴_히스토리_요약_호출(self, _, mock_sum):
        from app.services.gemini import _build_history
        _build_history([_msg("user", "A"), _msg("assistant", "B")] * 10)
        mock_sum.assert_called_once()

    @patch("app.services.gemini._summarize_history", return_value="[이전 대화 요약]: 요약내용")
    @patch("app.services.gemini._format_messages_as_history", return_value=[])
    def test_긴_히스토리_첫항목이_요약(self, _, __):
        from app.services.gemini import _build_history
        history = _build_history([_msg("user", "A"), _msg("assistant", "B")] * 10)
        self.assertEqual(history[0]["role"], "user")
        self.assertIn("[이전 대화 요약]", history[0]["parts"][0])


class TestBuildUserMessage(unittest.TestCase):

    @patch("app.services.gemini.preprocess_context", return_value="관련 내용")
    def test_컨텍스트_있으면_참고자료_포함(self, _):
        from app.services.gemini import _build_user_message
        result = _build_user_message("질문", [{"title": "x"}])
        self.assertIn("[참고 자료]", result)
        self.assertIn("질문", result)

    @patch("app.services.gemini.preprocess_context", return_value="")
    def test_컨텍스트_없으면_참고자료없음_표시(self, _):
        from app.services.gemini import _build_user_message
        result = _build_user_message("질문", [])
        self.assertIn("[참고 자료 없음]", result)

    @patch("app.services.gemini.preprocess_context", return_value="")
    def test_질문_항상_포함(self, _):
        from app.services.gemini import _build_user_message
        result = _build_user_message("충북대 입학처", [])
        self.assertIn("충북대 입학처", result)


class TestSendWithRetry(unittest.TestCase):

    def test_STOP_즉시_반환(self):
        from app.services.gemini import _send_with_retry
        chat = MagicMock()
        chat.send_message.return_value = _make_response("STOP", "정상 응답")
        self.assertEqual(_send_with_retry(chat, "안녕"), "정상 응답")
        self.assertEqual(chat.send_message.call_count, 1)

    def test_MAX_TOKENS_이어쓰기(self):
        from app.services.gemini import _send_with_retry
        chat = MagicMock()
        chat.send_message.side_effect = [
            _make_response("MAX_TOKENS", "첫 번째"),
            _make_response("STOP", " 이어진"),
        ]
        result = _send_with_retry(chat, "질문")
        self.assertIn("첫 번째", result)
        self.assertIn("이어진", result)

    def test_SAFETY_사과문_반환(self):
        from app.services.gemini import _send_with_retry
        chat = MagicMock()
        chat.send_message.return_value = _make_response("SAFETY")
        self.assertIn("답변이 어렵습니다", _send_with_retry(chat, "질문"))

    def test_RECITATION_사과문_반환(self):
        from app.services.gemini import _send_with_retry
        chat = MagicMock()
        chat.send_message.return_value = _make_response("RECITATION")
        self.assertIn("답변이 어렵습니다", _send_with_retry(chat, "질문"))

    @patch("app.services.gemini.time.sleep")
    def test_UNKNOWN_재시도(self, _):
        from app.services.gemini import _send_with_retry
        chat = MagicMock()
        chat.send_message.return_value = _make_response("UNKNOWN", "재시도 응답")
        result = _send_with_retry(chat, "질문")
        self.assertEqual(result, "재시도 응답")


class TestBuildChatResponse(unittest.TestCase):

    def _setup_model(self):
        model = MagicMock()
        model.count_tokens.return_value = MagicMock(total_tokens=100)
        model.start_chat.return_value = MagicMock()
        return model

    @patch("app.services.gemini._send_with_retry", return_value="정상 응답")
    @patch("app.services.gemini._build_history", return_value=[])
    @patch("app.services.gemini.get_model")
    def test_정상_응답_반환(self, mock_get_model, _, __):
        from app.services.gemini import build_chat_response
        mock_get_model.return_value = self._setup_model()
        result = build_chat_response([_msg("user", "A"), _msg("assistant", "B"), _msg("user", "C")])
        self.assertEqual(result, "정상 응답")

    @patch("app.services.gemini.get_model", side_effect=Exception("API 오류"))
    def test_오류시_사과문_반환(self, _):
        from app.services.gemini import build_chat_response
        result = build_chat_response([_msg("user", "A"), _msg("assistant", "B")])
        self.assertIn("죄송합니다", result)

    @patch("app.services.gemini._send_with_retry", return_value="ok")
    @patch("app.services.gemini._build_history", return_value=[])
    @patch("app.services.gemini.get_model")
    def test_search_results_None_처리(self, mock_get_model, _, __):
        from app.services.gemini import build_chat_response
        mock_get_model.return_value = self._setup_model()
        result = build_chat_response([_msg("user", "A"), _msg("assistant", "B")], search_results=None)
        self.assertEqual(result, "ok")


class TestOptimizeSearchQuery(unittest.TestCase):

    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    @patch("app.services.gemini.get_model")
    def test_최적화_쿼리_반환(self, mock_get_model):
        from app.services.gemini import optimize_search_query
        mock_model = MagicMock()
        mock_model.generate_content.return_value = _make_response("STOP", "충북대학교 컴공 입학 요강")
        mock_get_model.return_value = mock_model
        result = self._run(optimize_search_query("컴공 입학 어때?", [_msg("user", "질문")]))
        self.assertEqual(result, "충북대학교 컴공 입학 요강")

    @patch("app.services.gemini.get_model", side_effect=Exception("오류"))
    def test_cbnu_키워드_있으면_폴백_원문(self, _):
        from app.services.gemini import optimize_search_query
        result = self._run(optimize_search_query("충북대학교 도서관", [_msg("user", "질문")]))
        self.assertEqual(result, "충북대학교 도서관")

    @patch("app.services.gemini.get_model", side_effect=Exception("오류"))
    def test_cbnu_키워드_없으면_prefix_추가(self, _):
        from app.services.gemini import optimize_search_query
        result = self._run(optimize_search_query("도서관 운영시간", [_msg("user", "질문")]))
        self.assertTrue(result.startswith("충북대학교"))

    @patch("app.services.gemini.get_model")
    def test_finish_reason_not_stop_폴백(self, mock_get_model):
        from app.services.gemini import optimize_search_query
        mock_model = MagicMock()
        mock_model.generate_content.return_value = _make_response("SAFETY", "충북대학교 입학정보")
        mock_get_model.return_value = mock_model
        result = self._run(optimize_search_query("입학정보", [_msg("user", "질문")]))
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("app.services.gemini.get_model")
    def test_결과_너무_짧으면_폴백(self, mock_get_model):
        from app.services.gemini import optimize_search_query
        mock_model = MagicMock()
        mock_model.generate_content.return_value = _make_response("STOP", "짧음")  # 3자 < 10
        mock_get_model.return_value = mock_model
        result = self._run(optimize_search_query("충북대 입학", [_msg("user", "질문")]))
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestEvaluateAndRankResults(unittest.TestCase):

    def _raw(self, n=3):
        return [{"title": f"충북대 결과{i}", "url": f"https://cbnu.ac.kr/{i}", "content": f"내용{i}"} for i in range(n)]

    def _mock_model(self, rankings):
        resp = MagicMock()
        resp.text = json.dumps(rankings)
        model = MagicMock()
        model.generate_content.return_value = resp
        return model

    def test_빈_결과_빈_리스트(self):
        from app.services.gemini import evaluate_and_rank_results
        self.assertEqual(evaluate_and_rank_results("쿼리", []), [])

    @patch("app.services.gemini.get_model")
    def test_고점수_결과_반환(self, mock_get_model):
        from app.services.gemini import evaluate_and_rank_results
        mock_get_model.return_value = self._mock_model([
            {"index": 0, "score": 25, "reason": "공식"},
            {"index": 1, "score": 20, "reason": "뉴스"},
        ])
        result = evaluate_and_rank_results("충북대", self._raw(3))
        self.assertGreater(len(result), 0)

    @patch("app.services.gemini.get_model")
    def test_점수_내림차순_정렬(self, mock_get_model):
        from app.services.gemini import evaluate_and_rank_results
        mock_get_model.return_value = self._mock_model([
            {"index": 2, "score": 28, "reason": "최고"},
            {"index": 0, "score": 20, "reason": "보통"},
            {"index": 1, "score": 24, "reason": "좋음"},
        ])
        result = evaluate_and_rank_results("쿼리", self._raw(3))
        self.assertEqual(result[0]["title"], "충북대 결과2")

    @patch("app.services.gemini.get_model", side_effect=Exception("오류"))
    def test_오류시_전체_결과_반환(self, _):
        from app.services.gemini import evaluate_and_rank_results
        raw = self._raw(3)
        self.assertEqual(evaluate_and_rank_results("쿼리", raw), raw)

    @patch("app.services.gemini.get_model")
    def test_저점수_기준미달_전체_반환(self, mock_get_model):
        from app.services.gemini import evaluate_and_rank_results
        mock_get_model.return_value = self._mock_model([
            {"index": 0, "score": 5, "reason": "관련없음"},
        ])
        raw = self._raw(2)
        result = evaluate_and_rank_results("쿼리", raw)
        self.assertEqual(result, raw)


class TestStreamChatResponse(unittest.TestCase):

    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    async def _collect(self, gen):
        result = []
        async for chunk in gen:
            result.append(chunk)
        return result

    def _setup_model(self, chunks):
        model = MagicMock()
        model.count_tokens.return_value = MagicMock(total_tokens=100)
        chat = MagicMock()
        chat.send_message.return_value = iter(chunks)
        model.start_chat.return_value = chat
        return model

    @patch("app.services.gemini._build_history", return_value=[])
    @patch("app.services.gemini._build_user_message", return_value="질문")
    @patch("app.services.gemini.get_model")
    def test_청크_스트리밍(self, mock_get_model, _, __):
        from app.services.gemini import stream_chat_response
        mock_get_model.return_value = self._setup_model([
            MagicMock(text="안녕 "), MagicMock(text="하세요")
        ])
        messages = [_msg("user", "A"), _msg("assistant", "B"), _msg("user", "C")]
        result = self._run(self._collect(stream_chat_response(messages)))
        self.assertGreater(len(result), 0)
        self.assertNotEqual("".join(result).strip(), "")

    @patch("app.services.gemini._build_history", return_value=[])
    @patch("app.services.gemini._build_user_message", return_value="질문")
    @patch("app.services.gemini.get_model")
    def test_빈_청크_스킵(self, mock_get_model, _, __):
        from app.services.gemini import stream_chat_response
        mock_get_model.return_value = self._setup_model([
            MagicMock(text=""), MagicMock(text="응답"), MagicMock(text="")
        ])
        messages = [_msg("user", "A"), _msg("assistant", "B"), _msg("user", "C")]
        result = self._run(self._collect(stream_chat_response(messages)))
        self.assertTrue(any("응답" in c for c in result))

    @patch("app.services.gemini.get_model", side_effect=Exception("스트림 오류"))
    def test_오류시_사과문(self, _):
        from app.services.gemini import stream_chat_response
        messages = [_msg("user", "A"), _msg("assistant", "B")]
        result = self._run(self._collect(stream_chat_response(messages)))
        self.assertIn("죄송합니다", "".join(result))

    @patch("app.services.gemini._build_history", return_value=[])
    @patch("app.services.gemini._build_user_message", return_value="질문")
    @patch("app.services.gemini.get_model")
    def test_search_results_전달(self, mock_get_model, _, __):
        from app.services.gemini import stream_chat_response
        mock_get_model.return_value = self._setup_model([MagicMock(text="검색 결과 응답")])
        messages = [_msg("user", "A"), _msg("assistant", "B"), _msg("user", "C")]
        result = self._run(self._collect(stream_chat_response(messages, search_results=[{"title": "test"}])))
        self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
