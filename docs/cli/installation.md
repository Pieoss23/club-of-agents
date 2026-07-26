# Installation

## Requirements

- Python 3.12+
- Git (required for `club init`'s document pyramid; required at runtime for the Git
  worktree isolation described in [workflow.md](workflow.md) — without it, tasks still
  get assigned, just without a real branch/worktree, see that doc's fallback behavior)

## Install (editable, from a checkout of this repository)

```bash
pip install -e .
```

This registers the `club` command (see `[project.scripts]` in `pyproject.toml`) and
installs its dependencies: `pydantic`, `PyYAML`, `rich`, `typer`, `questionary`,
`pyfiglet`, `jsonschema`.

Verify it's on your PATH:

```bash
club --version
club --help
```

## Optional: real provider CLIs

`club agent start <id> --provider claude` or `--provider codex` shells out to the
`claude` or `codex` binary — install and authenticate those separately (see
[providers.md](providers.md)) before using anything other than the default `dummy`
provider. Nothing about installing `club` itself requires them.

## Running the test suite

```bash
pip install -e ".[dev]"
python -m pytest -q
```

No test ever invokes a real `claude`/`codex`/arbitrary shell subprocess — provider
adapter tests inject a fake subprocess call (see [architecture.md](architecture.md)).
