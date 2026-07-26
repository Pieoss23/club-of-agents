from __future__ import annotations

import json
from pathlib import Path

import pytest

from clubs.adapters.prompts import (
    implement_prompt, parse_json_response, plan_prompt, read_master_contract, review_prompt,
)
from clubs.initializer import initialize_club
from clubs.tasks import create_task
from clubs.missions import create_mission

from conftest import make_init_answers as answers


def test_read_master_contract_returns_generated_text(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    text = read_master_contract(tmp_path)
    assert "Master Contract" in text


def test_read_master_contract_returns_empty_string_when_no_club(tmp_path: Path) -> None:
    assert read_master_contract(tmp_path) == ""


def test_plan_prompt_includes_mission_fields() -> None:
    mission = {"title": "Add auth", "description": "Users must log in."}
    prompt = plan_prompt("CONTRACT TEXT", mission)
    assert "CONTRACT TEXT" in prompt
    assert "Add auth" in prompt
    assert "Users must log in." in prompt
    assert "title" in prompt and "objective" in prompt


def test_implement_prompt_includes_task_contract_fields(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function.")
    task = create_task(tmp_path, mission_id="MISSION-001", title="Add greet()", objective="Add a greet(name) function with tests.")
    prompt = implement_prompt("CONTRACT", task)
    assert task["objective"] in prompt
    assert task["acceptance_criteria"][0]["description"] in prompt
    assert "**" in prompt  # default allowed_paths


def test_review_prompt_includes_diff_and_criteria(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function.")
    task = create_task(tmp_path, mission_id="MISSION-001", title="Add greet()", objective="Add a greet(name) function with tests.")
    prompt = review_prompt("CONTRACT", task, "diff --git a/x b/x")
    assert "diff --git a/x b/x" in prompt
    assert task["acceptance_criteria"][0]["description"] in prompt
    assert "approved" in prompt


def test_parse_json_response_handles_plain_json() -> None:
    assert parse_json_response('{"a": 1}') == {"a": 1}


def test_parse_json_response_extracts_json_from_surrounding_text() -> None:
    text = 'Sure, here you go:\n{"title": "x", "objective": "y"}\nDone.'
    assert parse_json_response(text) == {"title": "x", "objective": "y"}


def test_parse_json_response_raises_on_no_json() -> None:
    with pytest.raises(ValueError):
        parse_json_response("no json here at all")
