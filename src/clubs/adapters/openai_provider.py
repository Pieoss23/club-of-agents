"""OpenAI adapter: plain Chat Completions API (api.openai.com/v1/chat/completions).
plan/review/configure only, see text_judgment.py; implement() is unsupported
(no file-editing agency)."""

from __future__ import annotations

import os
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

from clubs.adapters.errors import ProviderError
from clubs.adapters.http_client import openai_compatible_complete
from clubs.adapters.mechanical import MechanicalAssignMergeMixin
from clubs.adapters.text_judgment import TextJudgmentMixin


@dataclass(frozen=True)
class OpenAIProvider(TextJudgmentMixin, MechanicalAssignMergeMixin):
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    timeout: int = 600
    fetch: Callable = field(default=urllib.request.urlopen)

    def _complete(self, prompt: str) -> str:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError("OPENAI_API_KEY is not set.")
        return openai_compatible_complete(
            self.base_url, api_key=api_key, model=self.model,
            prompt=prompt, timeout=self.timeout, fetch=self.fetch,
        )
