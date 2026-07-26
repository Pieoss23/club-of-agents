"""Ollama adapter: local models via Ollama's OpenAI-compatible endpoint
(docs.ollama.com/api/openai-compatibility). No real API key needed locally --
any non-empty string works. plan/review/configure only, see text_judgment.py;
implement() is unsupported (no file-editing agency)."""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field
from typing import Callable

from clubs.adapters.http_client import openai_compatible_complete
from clubs.adapters.mechanical import MechanicalAssignMergeMixin
from clubs.adapters.text_judgment import TextJudgmentMixin


@dataclass(frozen=True)
class OllamaProvider(TextJudgmentMixin, MechanicalAssignMergeMixin):
    model: str = "llama3.1"
    base_url: str = "http://localhost:11434/v1"
    timeout: int = 600
    fetch: Callable = field(default=urllib.request.urlopen)

    def _complete(self, prompt: str) -> str:
        return openai_compatible_complete(
            self.base_url, api_key="ollama", model=self.model,
            prompt=prompt, timeout=self.timeout, fetch=self.fetch,
        )
