"""TextJudgmentMixin.configure(): the autonomous club-bootstrap flow. Uses OllamaProvider
as the concrete example (needs no env var) with a fake `fetch` -- never a real network call."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from clubs.adapters.errors import ProviderError
from clubs.adapters.ollama import OllamaProvider
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


def _fetch_returning(text: str, calls: list):
    def fetch(request, timeout=None):
        calls.append(request)
        return _FakeResponse(json.dumps({"choices": [{"message": {"content": text}}]}).encode("utf-8"))
    return fetch


def _load_club_yaml(root: Path) -> dict:
    return yaml.safe_load((root / ".clubs/club.yaml").read_text(encoding="utf-8"))


def test_configure_is_a_noop_without_a_pending_mission(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    calls: list = []
    provider = OllamaProvider(fetch=_fetch_returning("{}", calls))

    provider.configure(tmp_path, "master")

    assert calls == []
    assert _load_club_yaml(tmp_path)["club"]["bootstrapped"] is False


def test_configure_rewrites_roster_from_pending_mission(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Build API", description="A small Flask API with auth.")
    reply = json.dumps({"roles": [
        {"id": "backend", "capabilities": ["code"]},
        {"id": "reviewer", "capabilities": ["review", "merge"]},
    ]})
    provider = OllamaProvider(fetch=_fetch_returning(reply, []))

    provider.configure(tmp_path, "master")

    raw = _load_club_yaml(tmp_path)
    assert raw["club"]["bootstrapped"] is True
    assert set(raw["agents"]) == {"backend", "reviewer", "master"}
    assert raw["agents"]["backend"]["can_code"] is True
    assert raw["agents"]["reviewer"]["can_review"] is True
    assert raw["agents"]["reviewer"]["can_merge"] is True
    assert raw["agents"]["master"]["role"] == "master"

    events = [
        json.loads(line)
        for line in (tmp_path / ".clubs/runtime/events/events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert any(event["type"] == "club.bootstrapped" for event in events)


def test_configure_preserves_bootstrapping_role_even_when_llm_response_includes_it(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Build API", description="A small Flask API with auth.")
    reply = json.dumps({"roles": [
        {"id": "master", "capabilities": ["plan", "assign"]},
        {"id": "backend", "capabilities": ["code", "review", "merge"]},
    ]})
    provider = OllamaProvider(fetch=_fetch_returning(reply, []))

    provider.configure(tmp_path, "master")

    raw = _load_club_yaml(tmp_path)
    assert raw["agents"]["master"]["can_plan"] is True
    assert raw["agents"]["master"]["can_assign"] is True


def test_configure_is_idempotent_after_bootstrap(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Build API", description="A small Flask API with auth.")
    reply = json.dumps({"roles": [{"id": "backend", "capabilities": ["code", "assign", "merge"]}]})
    calls: list = []
    provider = OllamaProvider(fetch=_fetch_returning(reply, calls))
    provider.configure(tmp_path, "master")
    assert len(calls) == 1

    provider.configure(tmp_path, "master")

    assert len(calls) == 1


def test_configure_raises_provider_error_on_unparsable_response(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Build API", description="A small Flask API with auth.")
    provider = OllamaProvider(fetch=_fetch_returning("not json at all", []))

    with pytest.raises(ProviderError):
        provider.configure(tmp_path, "master")
