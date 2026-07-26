from __future__ import annotations

import json
import urllib.error

import pytest

from clubs.adapters import http_client
from clubs.adapters.errors import ProviderError


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _fake_fetch(body: dict):
    def fetch(request, timeout=None):
        return _FakeResponse(json.dumps(body).encode("utf-8"))
    return fetch


def test_openai_compatible_complete_returns_message_content() -> None:
    fetch = _fake_fetch({"choices": [{"message": {"content": "hello"}}]})
    result = http_client.openai_compatible_complete(
        "http://x", api_key="k", model="m", prompt="p", timeout=5, fetch=fetch,
    )
    assert result == "hello"


def test_openai_compatible_complete_raises_on_unexpected_shape() -> None:
    fetch = _fake_fetch({"unexpected": True})
    with pytest.raises(ProviderError):
        http_client.openai_compatible_complete("http://x", api_key="k", model="m", prompt="p", timeout=5, fetch=fetch)


def test_openai_compatible_complete_raises_on_url_error() -> None:
    def fetch(request, timeout=None):
        raise urllib.error.URLError("boom")
    with pytest.raises(ProviderError):
        http_client.openai_compatible_complete("http://x", api_key="k", model="m", prompt="p", timeout=5, fetch=fetch)


def test_openai_compatible_complete_raises_on_non_json_body() -> None:
    def fetch(request, timeout=None):
        return _FakeResponse(b"not json")
    with pytest.raises(ProviderError):
        http_client.openai_compatible_complete("http://x", api_key="k", model="m", prompt="p", timeout=5, fetch=fetch)


def test_gemini_complete_returns_text() -> None:
    fetch = _fake_fetch({"candidates": [{"content": {"parts": [{"text": "hi"}]}}]})
    result = http_client.gemini_complete(model="m", api_key="k", prompt="p", timeout=5, fetch=fetch)
    assert result == "hi"


def test_gemini_complete_raises_on_unexpected_shape() -> None:
    fetch = _fake_fetch({"unexpected": True})
    with pytest.raises(ProviderError):
        http_client.gemini_complete(model="m", api_key="k", prompt="p", timeout=5, fetch=fetch)
