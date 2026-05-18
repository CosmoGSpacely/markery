# Markery — Project Constitution

This document defines the structure of the Markery repository and the lifecycle of work within it. It contains no current state — for that, see `STATUS.md` and `ROADMAP.md`.

---

## Two-Track Model

All work in this repository is either **tool work** (building and improving Markery) or **project work** (conducting research using Markery). Root documents describe the tool only. Each research project is self-contained in its own folder under `projects/`.

---

## Tool Work Lifecycle

```
DEFERRED.md  →  ROADMAP.md  →  STATUS.md  →  archive/
```

- **`DEFERRED.md`** — items that are known, intentional, and not currently active. Each has a reopen trigger. When a trigger fires, promote the item to `ROADMAP.md`.
- **`ROADMAP.md`** — active and upcoming tool development, organized into phases with explicit gates.
- **`STATUS.md`** — current state: infrastructure ledger and one-line status per active project. Updated at the end of each session.
- **`archive/`** — completed roadmaps and design records, datestamped. Never edited after archiving.

---

## Project Work Lifecycle

```
project/RESEARCH-AGENDA.md  →  review  →  content/  →  site/
```

Each project under `projects/<name>/` is independent. A project contains:

| Path | Purpose |
|---|---|
| `RESEARCH-AGENDA.md` | Candidate subjects, methodology, key references |
| `RESEARCH.md` | Scholarly framework for this project |
| `STATUS.md` | Project-local metrics and next action |
| `README.md` | Project overview and entity list |
| `entities.txt` | Entity IDs scoped to this project |
| `matches/candidates.jsonl` | Generated — never edited |
| `matches/confirmed.jsonl` | Hand-curated confirmed pairs |
| `content/` | Research essays and narrative pages |
| `site/` | Built static site — gitignored, regenerable |
| `output/` | Enhanced images, PDFs — gitignored, regenerable |

Project-local `STATUS.md` carries the metrics and next action for that project. The root `STATUS.md` carries only a one-line summary per project.

---

## Root File Responsibilities

| File | What it contains |
|---|---|
| `CONTEXT.md` | This document — structural rules, no current state |
| `ROADMAP.md` | Active and upcoming tool development phases |
| `STATUS.md` | Tool infrastructure ledger + project summary table |
| `DEFERRED.md` | Deferred tool work with reopen triggers |
| `DESIGN.md` | Engineering rationale and architecture decisions |
| `SETUP.md` | New-machine setup instructions |
| `research-session.md` | Runnable operations checklist (project-agnostic) |
| `README.md` | Repository overview for new contributors |

---

## Specialist Reference Docs

Each specialist owns its API reference alongside its code:

| Doc | Owned by |
|---|---|
| `src/markery/specialist/patent/EPO.md` | Patent specialist — EPO OPS API reference |
| `src/markery/specialist/trademark/TSDR.md` | Trademark specialist — USPTO TSDR API reference |
| `src/markery/specialist/historian/persona/` | Historian specialist — Claude persona and content schemas |
