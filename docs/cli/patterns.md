# Collaboration patterns

Chosen during `club init`'s "Collaboration pattern" step (arrow-key picker), stored as
`workflow.pattern` in `club.yaml`. Each pattern is a small builder function in
`src/clubs/patterns.py` that turns your answers into a `dict[str, AgentConfig]` — the
one part of `club.yaml` that actually differs between patterns.

| id | Label shown in the wizard | Follow-up questions |
|---|---|---|
| `planner-developer-reviewer-coordinator` | Planner -> Developer -> Reviewer -> Coordinator | number of shells, role name per shell |
| `master-workers` | Master -> Workers | number of workers |
| `architect-frontend-backend-reviewer` | Architect -> Frontend -> Backend -> Reviewer | none — fixed 4 roles |
| `swarm-by-component` | Swarm by component | component names (one prompt per component, blank to finish) |
| `custom` | Custom | role name + capability checkboxes, repeated until you leave a role name blank |

## 1. Planner → Developer → Reviewer → Coordinator (default)

The master design brief's recommended default. Capabilities are assigned by
**canonical role name**, so if you rename a shell away from `planner`/`developer`/
`reviewer`/`coordinator` it gets *no* capabilities (an agent with no `can_*` flags set
does nothing when started — `club validate` won't catch this, only `club status`
showing it permanently idle will):

| role | can_plan | can_code | can_review | can_assign | can_merge |
|---|---|---|---|---|---|
| `planner` | x | | | | |
| `developer` | | x | | | |
| `reviewer` | | | x | | |
| `coordinator` | | | | x | x |

## 2. Master → Workers

One `master` (plans, assigns, merges), N `worker-1`..`worker-N` (implement):

| role | can_plan | can_code | can_assign | can_merge |
|---|---|---|---|---|
| `master` | x | | x | x |
| `worker-1..N` | | x | | |

No reviewer role in this pattern — tasks move straight from implementation to merge.

## 3. Architect → Frontend → Backend → Reviewer

Fixed, no questions asked:

| role | can_plan | can_code | can_review |
|---|---|---|---|
| `architect` | x | | |
| `frontend` | | x | |
| `backend` | | x | |
| `reviewer` | | | x |

No coordinator/merge capability granted in this pattern by default — add it by hand in
`club.yaml` (`can_merge: true` on whichever role should authorize integration) if you
need `merge()` to run.

## 4. Swarm by component

One agent per component you name (e.g. `auth`, `billing`, `search`), all with
`can_code: true` and nothing else — no built-in hierarchy, matching the master design
brief's "many agents, bounded, non-overlapping territory" description. You're expected
to assign/review/merge by hand (or add those capabilities to one of the swarm agents,
or a separate coordinator role, after `init`).

## 5. Custom

Full manual control: for each role you type a name, then check off any of `plan` /
`code` / `review` / `assign` / `merge` from a checkbox picker (`patterns.CAPABILITY_FIELDS`).
Use this when none of the above fit — e.g. a 2-agent pair-review setup, or a single
do-everything agent for a solo experiment.

## Validation

`club validate` only checks that `workflow.pattern` is one of the 5 ids above and that
role names match `^[a-z][a-z0-9-]*$` — it does **not** check that a pattern's
"expected" capability shape is intact if you hand-edit `club.yaml` afterward. That's
intentional (core principle: don't over-constrain what a club can look like), but it
means a typo'd or hand-edited role can silently end up with no capabilities.
