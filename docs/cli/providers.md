# Providers: dummy, shell, Claude, Codex, Ollama, OpenAI, Gemini, OpenRouter

A "provider" supplies the actual judgment behind `plan`/`assign`/`implement`/`review`/
`merge` (the `Provider` protocol in `src/clubs/adapters/base.py`). `assign` and `merge`
are pure mechanical role-matching — every provider shares the same implementation
(`MechanicalAssignMergeMixin`, `src/clubs/adapters/mechanical.py`). `plan`, `implement`,
and `review` are where a real provider actually does something.

Configured per-agent in `club.yaml`: `agents.<id>.provider` (`dummy`/`shell`/`claude`/
`codex`/`ollama`/`openai`/`gemini`/`openrouter`), `agents.<id>.provider_command` (`shell`
only), and `agents.<id>.provider_model`/`provider_base_url` (optional overrides for the
four text-only providers below). Override for one run with `club agent start <id>
--provider <name>` without editing the file.

## ⚠️ Read this before using anything but `dummy`

`shell`, `claude`, and `codex` invoke a **real, unattended subprocess** — with
`claude`/`codex` that's a real AI coding agent that can edit files and run shell
commands with no human approving each step, and it **spends real API credits**.
`club agent start` prints a yellow warning banner before the loop starts for exactly
this reason; don't script around it or ignore it. Start on a low-stakes task, with a
short `provider_timeout_seconds`, and watch `logs/agents/` while it runs.

**This project's own test suite never invokes a real `claude`/`codex`/shell command,
and never makes a real HTTP request** — every adapter test injects a fake subprocess
call or a fake `fetch`. The first live run against a real CLI or API is something you
trigger deliberately, not something that's been "tested" for you beyond the mocked
contract.

## `dummy` (default)

`DummyProvider` (`src/clubs/adapters/dummy.py`) — mechanical only, proves the
orchestration without generating real code: `plan()` copies a mission's title/
description 1:1 into one task; `implement()` marks every acceptance criterion
`verified: true` with evidence `"dummy provider"` and, if the task has a real
worktree, appends a line to `NOTES.md` there so there's something real to commit;
`review()` always approves. Safe to run indefinitely, no external calls, no cost.

## `shell` — the generic escape hatch

Runs `provider_command` (from `club.yaml`) with a JSON payload **on stdin**:
`{"capability": "plan"|"implement"|"review", "agent_id", "root", "worktree"?, "task"?
or "mission"?, "diff"? }`, cwd = the task's worktree for `implement`/`review` (raises
`ProviderError` if there is no real worktree yet — see [workflow.md](workflow.md)'s
fallback behavior), or the club root for `plan`.

- `plan`/`review` must print **a single JSON object** to stdout:
  `{"title": "...", "objective": "..."}` for plan, `{"approved": bool, "findings": [...]}`
  for review (`adapters/prompts.parse_json_response` tolerates surrounding prose —
  it finds the first `{...}` block).
- `implement` just prints free text — recorded verbatim (truncated to 500 chars) as a
  task note.
- Non-zero exit, a timeout, or a missing command all raise `ProviderError`.

This is how you'd plug in anything not built in here: a different LLM CLI, a wrapper
script, a Slack notification that waits for a human to reply.

## `claude`

`ClaudeProvider` (`src/clubs/adapters/claude.py`), confirmed against
[code.claude.com/docs/en/headless.md](https://code.claude.com/docs/en/headless.md):

```bash
claude -p "<prompt>" --output-format json                         # plan/review (read-only)
claude -p "<prompt>" --output-format json --permission-mode acceptEdits   # implement
```

- Working directory is set purely via the subprocess `cwd` — there is no `--cwd` flag.
- `--permission-mode acceptEdits` auto-approves file edits and basic filesystem
  commands (`mkdir`/`touch`/`mv`/`cp`), denies everything else. **There is no
  `--dangerously-skip-permissions` flag** — don't go looking for one.
- The reply text is `json.loads(stdout)["result"]`.
- No CLI timeout flag; `club.yaml`'s `runtime.provider_timeout_seconds` (default 600)
  is enforced by Python's `subprocess.run(..., timeout=...)`.
- Needs `ANTHROPIC_API_KEY` (or however your `claude` install normally authenticates)
  available in the environment `club` runs in.
- `implement`/`review` both **require** a real worktree (`ProviderError` otherwise) —
  Claude only ever runs inside the task's isolated directory, never the shared repo
  root.

## `codex`

`CodexProvider` (`src/clubs/adapters/codex.py`):

```bash
codex exec "<prompt>" --sandbox read-only        # plan/review
codex exec "<prompt>" --sandbox workspace-write  # implement
```

- `--sandbox workspace-write` is a real OS-level write sandbox scoped to the cwd — a
  stronger guarantee than Claude's tool-gating for what `implement` is allowed to
  touch.
- Progress streams to stderr; only the final agent message goes to stdout, so no
  `--json` flag is needed here — `result.stdout.strip()` is the reply.
- Same worktree requirement, same timeout mechanism, same auth-via-environment
  expectation (`OPENAI_API_KEY`/`codex login`) as Claude.

## Ollama / OpenAI / Gemini / OpenRouter — text-only judgment providers

These four are plain chat-completion APIs, not agentic coding tools like Claude Code
or Codex CLI — they have **no built-in file-editing or shell agency**. Scope is
deliberately limited to `plan`/`review`/`configure` (see below); `implement()` always
raises `ProviderError` ("no file-editing agency") — `club validate` catches this
earlier if `can_code` is ever set alongside one of these four. Pair them with
`shell`/`claude`/`codex` on whichever role actually needs `can_code`.

All four share one implementation, `TextJudgmentMixin` (`src/clubs/adapters/
text_judgment.py`) — every subclass only supplies `_complete(prompt) -> str`.
HTTP requests go through stdlib `urllib.request` (`src/clubs/adapters/http_client.py`,
no extra dependency), with an injectable `fetch` the same way `claude.py`/`codex.py`
inject `run` — every test uses a fake `fetch`, never a real network call.

| Provider | Endpoint | Auth | Default model |
|---|---|---|---|
| `ollama` | `http://localhost:11434/v1/chat/completions` (OpenAI-compatible) | none (local) | `llama3.1` |
| `openai` | `https://api.openai.com/v1/chat/completions` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `openrouter` | `https://openrouter.ai/api/v1/chat/completions` (OpenAI-compatible aggregator) | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` | `GEMINI_API_KEY` | `gemini-2.0-flash` |

Override the model with `agents.<id>.provider_model`; override Ollama's base URL with
`agents.<id>.provider_base_url` (e.g. a remote Ollama host). Missing API keys raise a
clear `ProviderError` ("... is not set") rather than a confusing HTTP failure.

## Autonomous bootstrap (`can_bootstrap`)

A designated agent — conventionally called "master", but it can be any role — can
organize the rest of the club's roster **while running live**, no separate `init --ai`
mode. Set `can_bootstrap: true` plus a real text-judgment provider (`ollama`/`openai`/
`gemini`/`openrouter` for now — `club validate` rejects any other provider paired
with `can_bootstrap`, since only these implement `configure()`):

1. `club init` as usual (any pattern — its roster gets replaced once bootstrap runs).
2. `club mission create` — describe the actual project in plain language. This is
   the brief the bootstrap step reads (reusing the same "first pending mission"
   lookup `plan()` already uses).
3. Hand-edit `club.yaml`: give one role `can_bootstrap: true` and `provider: ollama`
   (or whichever text-judgment provider you have credentials for).
4. `club agent start <that-role>`. On its first tick, it reads the mission, asks the
   model to decide `{"roles": [{"id": ..., "capabilities": [...]}, ...]}`, and
   **rewrites `club.yaml`'s entire `agents` section** to match — then sets
   `club.bootstrapped: true` so it never runs again, and emits a `club.bootstrapped`
   event.

**What it will not do**: assign real providers to the roles it creates. Every new role
comes out as `provider: dummy` — turning one into `claude`/`codex`/a real text-judgment
provider is still a separate, explicit edit you make afterward. Bootstrap organizes
*who does what*; it never autonomously decides to spend anyone's API credits.

The bootstrapping agent's own id is always preserved in the new roster (even if the
model's proposed roles don't mention it) — otherwise the running `club agent start`
process would raise `UnknownAgentError` on its very next tick.

## What happens when a real provider fails

`runtime.run_agent_tick` catches `ProviderError` per-capability (subprocess failure,
timeout, unparsable JSON) — it emits a `provider.failed` event
(`.clubs/runtime/events/events.jsonl`) and leaves the agent idle instead of crashing
the whole poll loop. It'll just retry next tick. Check the event log and
`logs/agents/<id>/` if an agent seems stuck.

## Auditability

Every real-provider call (`shell`/`claude`/`codex`/`ollama`/`openai`/`gemini`/
`openrouter`) writes its full prompt and stdout/stderr to
`logs/agents/<agent-id>/<task-or-mission-id>-<capability>.log` — `logs/agents/` exists
in every club from `init` but nothing wrote to it before real providers existed.
