import os
from unittest.mock import MagicMock, patch

import pytest
from backend.translation_layer import (
    _translate_riva,
    detect_input_language,
    get_active_translation_provider,
    translate,
)


def test_get_active_translation_provider(monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "test-key-123")
    monkeypatch.setenv("NVIDIA_RIVA_MODEL", "nvidia/riva-translate-4b-instruct-v2")
    monkeypatch.setenv("TRANSLATION_BACKEND", "auto")

    info = get_active_translation_provider()
    assert info["active_provider"] == "riva"
    assert info["riva_model"] == "nvidia/riva-translate-4b-instruct-v2"
    assert info["riva_configured"] is True


def test_translate_riva_success(monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-testkey")
    monkeypatch.setenv("NVIDIA_RIVA_MODEL", "nvidia/riva-translate-4b-instruct-v2")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Der Patient klagte über Brustschmerzen."
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = _translate_riva("The patient complained of chest pain.", src_lang="en", target_lang="de")
        assert result == "Der Patient klagte über Brustschmerzen."

        assert mock_post.called
        kwargs = mock_post.call_args[1]
        assert kwargs["json"]["model"] == "nvidia/riva-translate-4b-instruct-v2"
        assert kwargs["json"]["messages"][0]["role"] == "system"
        assert "en-de" in kwargs["json"]["messages"][0]["content"]


def test_translate_fallback_on_riva_failure(monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-testkey")
    monkeypatch.setenv("TRANSLATION_BACKEND", "auto")

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("requests.post", return_value=mock_response):
        # Should attempt Riva, fail, and fall back to MarianMT (or handle cleanly)
        with patch("backend.translation_layer._load_model") as mock_marian:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            mock_marian.return_value = (mock_tokenizer, mock_model)
            mock_tokenizer.return_value = {"input_ids": [1, 2, 3]}
            mock_model.generate.return_value = [[10, 20]]
            mock_tokenizer.decode.return_value = "Translated fallback text"

            res = translate("Guten Tag", src_lang="de", to_english=True)
            assert res == "Translated fallback text"
