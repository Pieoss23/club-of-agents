"""Shared coverage for the four text-only providers (Ollama/OpenAI/OpenRouter/Gemini):
same plan/review/implement contract, different wire format. Every test injects a fake
`fetch` -- none of these ever make a real network call."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clubs import tasks, workflow
from clubs.adapters.errors import ProviderError
from clubs.adapters.gemini import GeminiProvider
from clubs.adapters.ollama import OllamaProvider
from clubs.adapters.openai_provider import OpenAIProvider
from clubs.adapters.openrouter import OpenRouterProvider
from clubs.initializer import initialize_club
from clubs.missions import create_mission

from conftest import make_init_answers as answers


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _openai_shaped_fetch(text: str):
    def fetch(request, timeout=None):
        return _FakeResponse(json.dumps({"choices": [{"message": {"content": text}}]}).encode("utf-8"))
    return fetch


def _gemini_shaped_fetch(text: str):
    def fetch(request, timeout=None):
        return _FakeResponse(json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode("utf-8"))
    return fetch


PROVIDERS = {
    "ollama": (OllamaProvider, _openai_shaped_fetch, {}),
    "openai": (OpenAIProvider, _openai_shaped_fetch, {"OPENAI_API_KEY": "test-key"}),
    "openrouter": (OpenRouterProvider, _openai_shaped_fetch, {"OPENROUTER_API_KEY": "test-key"}),
    "gemini": (GeminiProvider, _gemini_shaped_fetch, {"GEMINI_API_KEY": "test-key"}),
}
NEEDS_ENV_VAR = {"openai": "OPENAI_API_KEY", "openrouter": "OPENROUTER_API_KEY", "gemini": "GEMINI_API_KEY"}


@pytest.mark.parametrize("name", list(PROVIDERS))
def test_plan_creates_task_from_provider_response(name, tmp_path: Path, monkeypatch) -> None:
    cls, fetch_factory, env = PROVIDERS[name]
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    reply = json.dumps({"title": "Add greet()", "objective": "Add a greet(name) function with tests."})
    provider = cls(fetch=fetch_factory(reply))

    provider.plan(tmp_path, "planner")

    assert len(list((tmp_path / "tasks/backlog").glob("TASK-*.json"))) == 1
    assert (tmp_path / "logs/agents/planner/MISSION-001-plan.log").is_file()


@pytest.mark.parametrize("name", list(PROVIDERS))
def test_implement_always_raises_provider_error(name, tmp_path: Path, monkeypatch) -> None:
    cls, fetch_factory, env = PROVIDERS[name]
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    provider = cls(fetch=fetch_factory("irrelevant"))
    with pytest.raises(ProviderError, match="no file-editing agency"):
        provider.implement(tmp_path, "developer")


@pytest.mark.parametrize("name", list(NEEDS_ENV_VAR))
def test_missing_env_var_raises_provider_error(name, tmp_path: Path, monkeypatch) -> None:
    cls, fetch_factory, _ = PROVIDERS[name]
    monkeypatch.delenv(NEEDS_ENV_VAR[name], raising=False)
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    provider = cls(fetch=fetch_factory("{}"))
    with pytest.raises(ProviderError, match="not set"):
        provider.plan(tmp_path, "planner")


@pytest.mark.parametrize("name", list(PROVIDERS))
def test_review_approves_and_marks_criteria_verified(name, git_repo: Path, monkeypatch) -> None:
    cls, fetch_factory, env = PROVIDERS[name]
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    initialize_club(answers(git_repo))
    task = tasks.create_task(git_repo, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(git_repo, "coordinator", task, "developer", "developer")
    tasks.move_task(git_repo, task["id"], from_stage="active", to_stage="review")
    verdict = json.dumps({"approved": True, "findings": []})
    provider = cls(fetch=fetch_factory(verdict))

    provider.review(git_repo, "reviewer")

    saved = tasks.load_task(git_repo / "tasks/review" / f"{task['id']}.json")
    assert saved["review_approved"] is True
    assert all(c["verified"] for c in saved["acceptance_criteria"])


@pytest.mark.parametrize("name", list(PROVIDERS))
def test_review_rejects_back_to_active(name, git_repo: Path, monkeypatch) -> None:
    cls, fetch_factory, env = PROVIDERS[name]
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    initialize_club(answers(git_repo))
    task = tasks.create_task(git_repo, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(git_repo, "coordinator", task, "developer", "developer")
    tasks.move_task(git_repo, task["id"], from_stage="active", to_stage="review")
    verdict = json.dumps({"approved": False, "findings": ["Missing tests."]})
    provider = cls(fetch=fetch_factory(verdict))

    provider.review(git_repo, "reviewer")

    assert not (git_repo / "tasks/review" / f"{task['id']}.json").exists()
    saved = tasks.load_task(git_repo / "tasks/active" / f"{task['id']}.json")
    assert saved["review_approved"] is False
    assert any("Missing tests." in note for note in saved["notes"])
