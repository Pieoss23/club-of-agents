"""Minimal stdlib HTTP client for the plain chat-completion providers
(Ollama/OpenAI/OpenRouter/Gemini) -- no new dependency, just urllib.

Every function takes an injectable `fetch` (defaults to urllib.request.urlopen)
so tests never make a real network call, the same pattern the subprocess-based
adapters use for `run`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable

from clubs.adapters.errors import ProviderError

Fetch = Callable[[urllib.request.Request], object]


def _post_json(url: str, *, headers: dict[str, str], body: dict, timeout: int, fetch: Fetch) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with fetch(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.URLError as error:
        raise ProviderError(f"HTTP request to {url} failed: {error}") from error
    except TimeoutError as error:
        raise ProviderError(f"HTTP request to {url} timed out after {timeout}s") from error
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise ProviderError(f"Non-JSON response from {url}: {raw[:200]!r}") from error


def openai_compatible_complete(
    base_url: str, *, api_key: str, model: str, prompt: str, timeout: int, fetch: Fetch = urllib.request.urlopen,
) -> str:
    """Works for Ollama, OpenAI, and OpenRouter -- all speak the same
    /chat/completions request/response shape."""
    payload = _post_json(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        body={"model": model, "messages": [{"role": "user", "content": prompt}]},
        timeout=timeout, fetch=fetch,
    )
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError(f"Unexpected chat-completion response shape: {payload}") from error


def gemini_complete(*, model: str, api_key: str, prompt: str, timeout: int, fetch: Fetch = urllib.request.urlopen) -> str:
    payload = _post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": api_key},
        body={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
        timeout=timeout, fetch=fetch,
    )
    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError(f"Unexpected Gemini response shape: {payload}") from error
