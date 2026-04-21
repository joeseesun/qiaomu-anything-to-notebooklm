"""Unit tests for minimax_provider.py"""
import importlib
import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# Ensure the repo root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_openai_mock(content: str = "Test answer"):
    """Return a minimal mock that looks like openai.OpenAI."""
    mock_client = MagicMock()
    choice = MagicMock()
    choice.message.content = content
    mock_client.chat.completions.create.return_value = MagicMock(choices=[choice])
    return mock_client


# ---------------------------------------------------------------------------
# _get_client tests
# ---------------------------------------------------------------------------

class TestGetClient:
    def test_raises_when_no_api_key(self):
        """_get_client must raise ValueError when no key is available."""
        import minimax_provider
        with patch.dict(os.environ, {}, clear=True):
            # Remove MINIMAX_API_KEY from env if present
            env = {k: v for k, v in os.environ.items() if k != "MINIMAX_API_KEY"}
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises((ValueError, Exception)):
                    minimax_provider._get_client()

    def test_uses_env_api_key(self):
        """_get_client reads MINIMAX_API_KEY from environment."""
        import minimax_provider
        mock_openai_cls = MagicMock(return_value=MagicMock())
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "env-key-123"}):
            with patch("minimax_provider.OpenAI", mock_openai_cls, create=True):
                # Patch the import inside the function
                with patch.dict(sys.modules, {"openai": types.ModuleType("openai")}):
                    sys.modules["openai"].OpenAI = mock_openai_cls
                    client = minimax_provider._get_client()
                    mock_openai_cls.assert_called_once()
                    call_kwargs = mock_openai_cls.call_args[1]
                    assert call_kwargs.get("api_key") == "env-key-123"

    def test_uses_explicit_api_key(self):
        """_get_client uses the explicitly passed api_key."""
        import minimax_provider
        mock_openai_cls = MagicMock(return_value=MagicMock())
        with patch.dict(sys.modules, {"openai": types.ModuleType("openai")}):
            sys.modules["openai"].OpenAI = mock_openai_cls
            minimax_provider._get_client(api_key="explicit-key", base_url="https://api.minimax.io/v1")
            call_kwargs = mock_openai_cls.call_args[1]
            assert call_kwargs.get("api_key") == "explicit-key"

    def test_default_base_url(self):
        """_get_client defaults to MINIMAX_BASE_URL."""
        import minimax_provider
        mock_openai_cls = MagicMock(return_value=MagicMock())
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "key"}, clear=False):
            env_no_base = {k: v for k, v in os.environ.items() if k != "MINIMAX_BASE_URL"}
            with patch.dict(os.environ, env_no_base, clear=True):
                with patch.dict(os.environ, {"MINIMAX_API_KEY": "key"}):
                    with patch.dict(sys.modules, {"openai": types.ModuleType("openai")}):
                        sys.modules["openai"].OpenAI = mock_openai_cls
                        minimax_provider._get_client(api_key="key")
                        call_kwargs = mock_openai_cls.call_args[1]
                        assert call_kwargs.get("base_url") == minimax_provider.MINIMAX_BASE_URL

    def test_custom_base_url(self):
        """_get_client respects an explicitly passed base_url."""
        import minimax_provider
        mock_openai_cls = MagicMock(return_value=MagicMock())
        custom_url = "https://custom.minimax.io/v1"
        with patch.dict(sys.modules, {"openai": types.ModuleType("openai")}):
            sys.modules["openai"].OpenAI = mock_openai_cls
            minimax_provider._get_client(api_key="key", base_url=custom_url)
            call_kwargs = mock_openai_cls.call_args[1]
            assert call_kwargs.get("base_url") == custom_url


# ---------------------------------------------------------------------------
# analyze_content tests
# ---------------------------------------------------------------------------

class TestAnalyzeContent:
    def _patch_client(self, mock_client, monkeypatch):
        import minimax_provider
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)

    def test_returns_one_answer_per_question(self, monkeypatch):
        import minimax_provider
        mock_client = _make_openai_mock("answer")
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)
        answers = minimax_provider.analyze_content(
            content="Some article text.",
            questions=["Q1", "Q2", "Q3"],
        )
        assert len(answers) == 3

    def test_answer_text_is_returned(self, monkeypatch):
        import minimax_provider
        mock_client = _make_openai_mock("Expected answer")
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)
        answers = minimax_provider.analyze_content("content", ["single question"])
        assert answers[0] == "Expected answer"

    def test_default_model_is_minimax_m27(self, monkeypatch):
        import minimax_provider
        mock_client = _make_openai_mock("ok")
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)
        minimax_provider.analyze_content("text", ["q"])
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "MiniMax-M2.7"

    def test_custom_model_is_passed(self, monkeypatch):
        import minimax_provider
        mock_client = _make_openai_mock("ok")
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)
        minimax_provider.analyze_content("text", ["q"], model="MiniMax-M2.7-highspeed")
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "MiniMax-M2.7-highspeed"

    def test_temperature_is_1(self, monkeypatch):
        """MiniMax requires temperature in (0.0, 1.0]; we always send 1.0."""
        import minimax_provider
        mock_client = _make_openai_mock("ok")
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)
        minimax_provider.analyze_content("text", ["q"])
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 1.0

    def test_content_truncated_to_max_length(self, monkeypatch):
        import minimax_provider
        mock_client = _make_openai_mock("ok")
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)
        long_content = "x" * (minimax_provider.MAX_CONTENT_LENGTH + 5000)
        minimax_provider.analyze_content(long_content, ["q"])
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        system_msg = next(
            m["content"] for m in call_kwargs["messages"] if m["role"] == "system"
        )
        # The truncated content must appear in the system message
        assert "x" * minimax_provider.MAX_CONTENT_LENGTH in system_msg
        # But NOT beyond the limit
        assert "x" * (minimax_provider.MAX_CONTENT_LENGTH + 1) not in system_msg

    def test_empty_questions_returns_empty_list(self, monkeypatch):
        import minimax_provider
        mock_client = _make_openai_mock("ok")
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)
        answers = minimax_provider.analyze_content("text", [])
        assert answers == []
        mock_client.chat.completions.create.assert_not_called()

    def test_none_response_becomes_empty_string(self, monkeypatch):
        import minimax_provider
        mock_client = MagicMock()
        choice = MagicMock()
        choice.message.content = None
        mock_client.chat.completions.create.return_value = MagicMock(choices=[choice])
        monkeypatch.setattr(minimax_provider, "_get_client", lambda **kw: mock_client)
        answers = minimax_provider.analyze_content("text", ["q"])
        assert answers == [""]


# ---------------------------------------------------------------------------
# Module-level constants tests
# ---------------------------------------------------------------------------

class TestConstants:
    def test_default_model_is_defined(self):
        import minimax_provider
        assert minimax_provider.MINIMAX_DEFAULT_MODEL == "MiniMax-M2.7"

    def test_models_list_contains_expected_models(self):
        import minimax_provider
        assert "MiniMax-M2.7" in minimax_provider.MINIMAX_MODELS
        assert "MiniMax-M2.7-highspeed" in minimax_provider.MINIMAX_MODELS

    def test_base_url_uses_api_minimax_io(self):
        import minimax_provider
        assert minimax_provider.MINIMAX_BASE_URL.startswith("https://api.minimax.io")

    def test_no_minimax_embedding_model(self):
        """Ensure we have NOT added any embedding model (MiniMax has none)."""
        import minimax_provider
        for attr in dir(minimax_provider):
            assert "embed" not in attr.lower(), (
                f"Unexpected embedding-related attribute found: {attr}"
            )
