from __future__ import annotations

from pathlib import Path

import yaml

from clubs import runtime
from clubs.initializer import initialize_club

from conftest import make_init_answers as answers


def test_missing_provider_timeout_uses_documented_default(tmp_path: Path) -> None:
    """Older initialized clubs can still start agents after the timeout was added."""
    initialize_club(answers(tmp_path))
    config_path = tmp_path / ".clubs/club.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    del config["runtime"]["provider_timeout_seconds"]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    assert runtime.load_provider_timeout_seconds(tmp_path) == 600
