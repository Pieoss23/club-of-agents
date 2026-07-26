"""Gemini adapter: Google's generateContent REST API
(generativelanguage.googleapis.com/v1beta/models/{model}:generateContent).
plan/review/configure only, see text_judgment.py; implement() is unsupported
(no file-editing agency)."""

from __future__ import annotations

import os
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

from clubs.adapters.errors import ProviderError
from clubs.adapters.http_client import gemini_complete
from clubs.adapters.mechanical import MechanicalAssignMergeMixin
from clubs.adapters.text_judgment import TextJudgmentMixin


@dataclass(frozen=True)
class GeminiProvider(TextJudgmentMixin, MechanicalAssignMergeMixin):
    model: str = "gemini-2.0-flash"
    timeout: int = 600
    fetch: Callable = field(default=urllib.request.urlopen)

    def _complete(self, prompt: str) -> str:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is not set.")
        return gemini_complete(
            model=self.model, api_key=api_key, prompt=prompt, timeout=self.timeout, fetch=self.fetch,
        )
