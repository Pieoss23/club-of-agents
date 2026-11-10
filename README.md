# Clubs of Agents (`club`)

Trasforma un normale repository Git in un ambiente di sviluppo multi-agente:
più agenti lavorano sullo stesso progetto, ciascuno isolato in un worktree,
coordinandosi attraverso file versionati invece che attraverso un database o
un servizio esterno.

**Il repository è la memoria condivisa.** Niente database, niente dashboard,
nessun vincolo a un fornitore di modelli: gli agenti possono essere Claude
Code, Codex, un modello locale via Ollama, uno script shell o un adattatore
fittizio per i test.

## Cosa dimostra questo progetto

- **169 test automatici**, eseguibili con `python -m pytest -q`.
- **Architettura a provider intercambiabili.** Nove adattatori — Claude,
  Codex, Gemini, OpenAI, OpenRouter, Ollama, shell, più due fittizi — dietro
  un'unica interfaccia. Il motore di workflow non sa quale modello sta
  usando.
- **Isolamento per task tramite worktree Git.** Ogni task lavora su un albero
  separato: due agenti non si pestano i piedi sullo stesso file.
- **Bus di messaggi su filesystem.** La comunicazione fra agenti passa da file
  versionati, quindi è ispezionabile, diffabile e sopravvive a un riavvio.
- **Motore di transizioni di stato** per il ciclo di vita dei task, con log di
  audit di ogni passaggio.
- **CLI completa** costruita con Typer e Rich, installabile come pacchetto.

## Perché

Far collaborare più agenti su una base di codice è facile da dimostrare e
difficile da rendere affidabile: gli agenti si sovrascrivono, perdono il
contesto, e il coordinamento finisce in un servizio che diventa un punto
unico di rottura. Qui il coordinamento sta nel repository stesso — la stessa
cosa che gli agenti stanno già modificando, e che un essere umano può leggere
con `git log`.

## Quickstart

```bash
pip install -e .
club init          # interactive wizard: name, collaboration pattern, roles, Master Contract location
club validate       # check the generated config/docs/folders
club mission create # describe a goal in one sentence
club task create    # decompose it into a task under that mission
club agent start developer   # run one agent's poll loop (dummy provider by default)
club status         # see agents, task counts, missions at a glance
```

Full walkthrough: [docs/cli/quickstart.md](docs/cli/quickstart.md).

## Documentation

- [docs/cli/installation.md](docs/cli/installation.md) — requirements, editable install, verifying the `club` command.
- [docs/cli/quickstart.md](docs/cli/quickstart.md) — a full lifecycle, start to finish.
- [docs/cli/commands.md](docs/cli/commands.md) — every command and flag.
- [docs/cli/configuration.md](docs/cli/configuration.md) — `club.yaml` reference.
- [docs/cli/patterns.md](docs/cli/patterns.md) — the 5 collaboration patterns and the roles/capabilities each one generates.
- [docs/cli/workflow.md](docs/cli/workflow.md) — the task lifecycle, Git isolation, path policy, PR drafts.
- [docs/cli/providers.md](docs/cli/providers.md) — dummy/shell/Claude/Codex adapters, including the real, unattended-execution safety notes.
- [docs/cli/architecture.md](docs/cli/architecture.md) — module map and contributor guide.

## Project status

All 10 milestones from the original design brief are implemented: CLI skeleton, init
wizard, validation, status, missions/tasks, the filesystem message bus, the agent
runner, the stage-transition workflow engine, Git worktree isolation, and provider
adapters (shell/Claude/Codex). See `python -m pytest -q` (169 test) for the current
regression suite.

## The dogfooded example project

Before this CLI existed, this same repository was used to prove out its document/task
conventions by hand — a small Node.js health-check HTTP service built via simulated
planner/developer/reviewer agents. That history (and how to run it) is preserved in
[docs/dogfood-example.md](docs/dogfood-example.md); it's a real example of the workflow
`club` now automates, not part of the CLI itself.

## License

MIT — see [LICENSE](LICENSE).
