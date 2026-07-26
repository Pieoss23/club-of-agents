# Architecture (contributor guide)

## Module map

```text
src/clubs/
├── cli.py            Typer app: every `club ...` command, the wizard prompts, the
│                      interactive menu. Thin — delegates everything to the modules below.
├── models.py          Pydantic models for club.yaml (ClubConfig/AgentConfig/...) and Mission.
├── initializer.py     InitAnswers -> ClubConfig, writes the generated files/folders,
│                      never silently overwrites (InitializationError instead).
├── templates.py       Loads the bundled document-pyramid templates.
├── validator.py       validate_club(root) -> ValidationResult; every other command
│                      (status, missions, tasks, agent start) calls this first.
├── patterns.py         One builder function per collaboration pattern -> dict[str, AgentConfig].
├── interactive.py      questionary-backed pickers with a non-tty fallback to plain
│                       typer.prompt (so CliRunner-based tests never need a real terminal).
├── banner.py           The post-init ASCII animation (skipped when non-interactive).
├── status.py            collect_status(root) -> agents/tasks/missions snapshot.
├── missions.py          create_mission, next_mission_id.
├── tasks.py              create_task/load_task/save_task/move_task/find_task/
│                         list_tasks/find_task_by_id, validated against the bundled
│                         task.schema.json.
├── messaging.py          send_message/route_messages (outbox -> inbox) + emit_event
│                         (the shared .clubs/runtime/events/events.jsonl log).
├── runtime.py            AgentState read/write, load_agents/load_polling_interval/
│                         load_main_branch/load_provider_timeout_seconds, and
│                         run_agent_tick -- the one fully-unit-testable poll cycle
│                         (the `while True: sleep()` wrapper only exists in cli.py).
├── workflow.py           The provider-agnostic mechanics of every stage transition:
│                         assign_task/submit_for_review/approve_review/integrate,
│                         eligible_assignee, decompose_mission, real_worktree. See
│                         docs/cli/workflow.md.
├── git_ops.py            Thin subprocess wrapper: is_git_repo/create_worktree/
│                         remove_worktree/changed_paths/diff_text/commit_all.
│                         Raises GitError; callers decide whether that's fatal.
├── path_policy.py        check(changed, allowed, forbidden) -> warn-only violations.
└── adapters/
    ├── base.py            The Provider Protocol (plan/assign/implement/review/merge).
    ├── mechanical.py       MechanicalAssignMergeMixin (assign/merge) + pending_missions,
    │                       shared by every provider.
    ├── dummy.py            DummyProvider: mechanical only, no real code generation.
    ├── errors.py           ProviderError.
    ├── prompts.py          Shared prompt assembly (reads the Master Contract, builds
    │                       plan/implement/review prompts) + parse_json_response.
    ├── audit_log.py        write_log(...) -> logs/agents/<id>/<item>-<capability>.log.
    ├── claude.py            ClaudeProvider (real, subprocess-based, agentic -- can implement()).
    ├── codex.py             CodexProvider (real, subprocess-based, agentic -- can implement()).
    ├── shell.py             ShellProvider (real, subprocess-based, fully generic, agentic).
    ├── http_client.py       openai_compatible_complete/gemini_complete -- stdlib urllib,
    │                        injectable `fetch` (no test ever hits the real network).
    ├── text_judgment.py      TextJudgmentMixin: shared plan/review/configure for any
    │                         provider that's text-only (implement() always raises).
    ├── ollama.py             OllamaProvider (text-only, local, no API key).
    ├── openai_provider.py    OpenAIProvider (text-only, OPENAI_API_KEY).
    ├── openrouter.py         OpenRouterProvider (text-only, OPENROUTER_API_KEY).
    └── gemini.py             GeminiProvider (text-only, GEMINI_API_KEY).
```

## The poll tick

`runtime.run_agent_tick(root, agent_id, provider)` is the whole story for one agent,
one cycle:

1. Write state `working`, route pending messages.
2. For each capability the agent's `AgentConfig` grants (`can_plan`/`can_assign`/
   `can_code`/`can_review`/`can_merge`), call the matching `Provider` method, wrapped
   in `_safe_call` — a `ProviderError` gets logged as a `provider.failed` event
   instead of propagating (real providers can genuinely fail: timeouts, bad output,
   missing binaries; the dummy provider never raises this).
3. Route messages again, write state `idle` (with whatever task, if any, is now
   `active` and owned by this agent).

`cli._run_agent_start` just wraps this in `while True: ...; time.sleep(interval)` with
a `KeyboardInterrupt` handler — everything above it is intentionally free of any
"loop forever" logic so it stays a single, fast, deterministic unit test.

## Adding a new collaboration pattern

1. Add the id to `patterns.PATTERN_IDS` and a label to `patterns.PATTERN_LABELS`.
2. Write a builder function returning `dict[str, AgentConfig]` (see the existing five
   for the shape — capabilities come from the `can_*` booleans on `AgentConfig`).
3. Wire it into `cli._build_agents_for_pattern`, adding whatever wizard follow-up
   questions it needs (reuse `interactive.text`/`.checkbox`/`.text_loop`/`.select_one`
   — every one of them already has a non-interactive fallback, don't call
   `questionary` directly from `cli.py`).
4. `validator.py` needs no change — it already validates against `PATTERN_IDS` and
   the generic role-name/capability rules, not per-pattern shape.

## Adding a new provider

Implement the `Provider` protocol (`plan`/`assign`/`implement`/`review`/`merge`),
inheriting `MechanicalAssignMergeMixin` for the mechanical two. Reuse
`adapters.prompts` for prompt text, `adapters.audit_log.write_log` for the transcript,
and raise `adapters.errors.ProviderError` (never let a raw exception escape — the
runtime only catches `ProviderError`). Wire the type string into
`cli._build_provider` and `models.PROVIDER_TYPES`/`validator.py`'s check.

**If the new provider is text-only** (a chat-completion API with no file-editing
agency — the shape `ollama.py`/`openai_provider.py`/`openrouter.py`/`gemini.py` follow):
inherit `TextJudgmentMixin` (`adapters/text_judgment.py`) instead of writing
`plan`/`review`/`configure`/`implement` yourself — just implement `_complete(prompt) ->
str`. If it talks HTTP, reuse or extend `adapters/http_client.py` (injectable `fetch`,
same pattern as the subprocess `run` injection). Add it to
`models.TEXT_ONLY_PROVIDER_TYPES` too, or `validator.py` won't let `can_bootstrap` or
the `can_code` guard recognize it correctly.

## Testing conventions

- Every test that needs an initialized club uses the shared `make_init_answers`
  helper in `tests/clubs/conftest.py` (not a locally re-defined one).
- Tests needing a **real git repo** (worktree creation, commits, diffs) use the
  `git_repo` fixture in the same `conftest.py` — `git init`, repo-local
  `user.name`/`user.email`, one commit, branch renamed to `main`. Everything else uses
  plain `tmp_path`, which deliberately is *not* a git repo, to prove the graceful
  fallback in `workflow.assign_task` never regresses.
- **No test ever calls a real `claude`/`codex`/arbitrary shell subprocess, or a real
  HTTP endpoint.** Every subprocess-based provider test injects `run=<fake callable>`
  returning a canned `subprocess.CompletedProcess`; every HTTP-based provider test
  injects `fetch=<fake callable>` returning a fake response with `.read()`. If you add
  a test that needs a new response shape, add a fake, don't loosen this.
- `python -m pytest -q` — 169 tests as of the provider-expansion/bootstrap round, all
  fast (no real subprocess, no real network, no `time.sleep` beyond what a couple of
  dummy-provider demo tests use for a watchable multi-terminal run, and even those
  default to `work_seconds=0`).
