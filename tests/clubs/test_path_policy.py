from __future__ import annotations

from clubs import path_policy


def test_no_violation_when_path_matches_allowed() -> None:
    violations = path_policy.check(["src/clubs/cli.py"], ["src/clubs/**"], [])
    assert violations == []


def test_violation_when_path_not_covered_by_allowed() -> None:
    violations = path_policy.check(["docs/other.md"], ["src/clubs/**"], [])
    assert len(violations) == 1
    assert "docs/other.md" in violations[0]


def test_forbidden_wins_even_if_also_allowed() -> None:
    violations = path_policy.check([".github/workflows/ci.yml"], ["**"], [".github/workflows/**"])
    assert len(violations) == 1
    assert "forbidden" in violations[0]


def test_empty_allowed_list_means_no_restriction() -> None:
    violations = path_policy.check(["anything/at/all.py"], [], [])
    assert violations == []


def test_multiple_changed_paths_each_checked_independently() -> None:
    violations = path_policy.check(
        ["src/ok.py", "database/migrations/0001.sql"], ["src/**"], ["database/**"],
    )
    assert len(violations) == 1
    assert "database/migrations/0001.sql" in violations[0]
