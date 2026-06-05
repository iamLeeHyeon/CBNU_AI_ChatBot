import unittest
from unittest.mock import MagicMock, patch


class TestGetModel(unittest.TestCase):

    @patch("app.services.gemini_client.genai")
    def test_configure_api_key_호출(self, mock_genai):
        from app.services.gemini_client import get_model
        mock_genai.GenerativeModel.return_value = MagicMock()
        with patch("app.services.gemini_client.os.getenv", return_value="test-api-key"):
            get_model({"temperature": 0.2})
        mock_genai.configure.assert_called_once_with(api_key="test-api-key")

    @patch("app.services.gemini_client.genai")
    def test_system_instruction_없으면_kwargs에_미포함(self, mock_genai):
        from app.services.gemini_client import get_model
        mock_genai.GenerativeModel.return_value = MagicMock()
        get_model({"temperature": 0.2})
        call_kwargs = mock_genai.GenerativeModel.call_args[1]
        self.assertNotIn("system_instruction", call_kwargs)

    @patch("app.services.gemini_client.genai")
    def test_system_instruction_있으면_kwargs에_포함(self, mock_genai):
        from app.services.gemini_client import get_model
        mock_genai.GenerativeModel.return_value = MagicMock()
        get_model({"temperature": 0.2}, system_instruction="시스템 프롬프트")
        call_kwargs = mock_genai.GenerativeModel.call_args[1]
        self.assertEqual(call_kwargs["system_instruction"], "시스템 프롬프트")

    @patch("app.services.gemini_client.genai")
    def test_generation_config_전달(self, mock_genai):
        from app.services.gemini_client import get_model
        mock_genai.GenerativeModel.return_value = MagicMock()
        config = {"temperature": 0.5, "max_output_tokens": 1024}
        get_model(config)
        call_kwargs = mock_genai.GenerativeModel.call_args[1]
        self.assertEqual(call_kwargs["generation_config"], config)

    @patch("app.services.gemini_client.genai")
    def test_GenerativeModel_반환(self, mock_genai):
        from app.services.gemini_client import get_model
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        result = get_model({})
        self.assertIs(result, mock_model)


if __name__ == "__main__":
    unittest.main()
