# Markery — Project Contract

This file governs all Claude Code sessions in this repository. It is automatically loaded and applies to every agent working here.

---

## Work Classification

Every piece of work belongs to one of three tiers. Classify before acting; place results in the right tier.

| Tier | What it covers | Canonical paths |
|---|---|---|
| **Markery** | Shared infrastructure: CLI, databases, tests, top-level docs | `src/markery/` (excluding specialist subdirs), `tests/`, `CLAUDE.md`, `CONTEXT.md`, `DESIGN.md`, `SETUP.md`, `README.md`, `ROADMAP.md`, `DEFERRED.md`, `STATUS.md`, `archive/` |
| **Specialist** | One agent's domain: Python modules, CLI commands, persona files | `src/markery/specialist/<name>/` — each specialist owns its subtree exclusively |
| **Project** | One research project's artifacts: entities, matches, content, site | `projects/<name>/` |

A single task may touch multiple tiers. Classify each change independently.

---

## Work Routing

**When work surfaces, route it before acting.**

**ROADMAP.md** — Active phases currently in flight. Add work here when:
- It has a defined sequence of actions and a phase gate
- It is the current priority and work is imminent or in progress

**DEFERRED.md** — Known work that is not the current priority. Add an entry here when:
- Work surfaces that is out of scope for the current phase
- Work is blocked by an external condition (quota, dependency, design decision)
- Work is explicitly postponed with a named reopen trigger

Every DEFERRED entry requires: a unique ID (`Dnnn`), a one-line description, and an explicit reopen trigger. No entry without a trigger.

**ROADMAP phase completion format:**
- Append `— CLOSED` to the phase heading: `### P3 — Description — CLOSED`
- Append `— PASSED` to the phase gate line when all criteria are met
- Do not use strikethrough markup (`~~`) in ROADMAP — it obscures content for future reference
- Body text is preserved as written; only the heading status tag changes

**ROADMAP results placement:**
- Write the results paragraph immediately after the last numbered step of the phase, before the closing `---` separator
- Never write results inside the Phase Gate block — gate lines hold only the criterion and its `— PASSED` tag inline on the same line
- Format: `Results YYYY-MM-DD: <what was built, what deviated from the plan, test count, total tests passing>`

**ROADMAP archive procedure (when a phase group is complete):**
1. Create `archive/ROADMAP-<date>.md` containing only the completed phase content
2. In `ROADMAP.md`, delete the completed phase body entirely — every line from the `## Phase N` heading through the closing `---`
3. Add one line to the archive index at the top of `ROADMAP.md`: `Phase N closed YYYY-MM-DD. Archived to archive/ROADMAP-<date>.md.`
4. The archive index lines are the only trace of completed phases in the active ROADMAP — no headings, no summaries, no status notes

---

## Review File Convention

A REVIEW file is an ad-hoc cross-cutting analysis document. It is not permanent documentation.

- Create `<NAME>-REVIEW.md` at repo root when beginning a structured audit or analysis
- Work from it during the analysis; record findings and decisions in it
- When complete: copy to `archive/<NAME>-REVIEW-<date>.md`, then `git rm <NAME>-REVIEW.md`
- Never leave a REVIEW file at root after its analysis is complete

---

## Specialist Boundary Enforcement

Each specialist owns its subtree exclusively. Before writing any file, verify it falls within the active specialist's Scope (see `## Scope` in each specialist's `identity.md`). If a task requires writing outside scope, stop — create or update a DEFERRED entry and halt.

Specialist identity files:
- PATENT: `src/markery/specialist/patent/persona/identity.md`
- TRADEMARK: `src/markery/specialist/trademark/persona/identity.md`
- MATCHMAKER: `src/markery/specialist/matchmaker/persona/identity.md`
- HISTORIAN: `src/markery/specialist/historian/persona/identity.md`
- PUBLISHER: `src/markery/specialist/publisher/persona/identity.md`

---

## Use the CLI — Do Not Bypass It

Markery's CLI is the product being tested. Prefer CLI commands over direct file creation, database writes, **and database reads** at all times. This is not a convenience preference — it is how the tool validates its own correctness.

**The rule applies to inspection as much as to creation.** Before querying any DuckDB database directly or reading project CSV/JSONL files to understand current state, run `markery --help` and check whether a command surfaces that information. Raw DuckDB queries and direct file reads bypass the same validation paths as raw writes.

Before any operation — read or write — run `markery --help` and check whether a command exists for the task. If one does, use it.

| Task | Use this | Not this |
|---|---|---|
| Inspect project entity/variant/coverage state | `markery project onboard <name>` | Direct DuckDB queries, reading `entities.csv` / `variants.csv` |
| Check candidate queue | `markery match <project>` (dry-run or review output) | Reading `candidates.jsonl` by hand |
| Start a new project | `markery project init <name>` | `mkdir` + `Write` files by hand |
| Add trademark data | `markery trademark build` / `enrich` | Direct DuckDB writes |
| Add patent data | `markery patent build` | Direct DuckDB writes |
| Generate candidates | `markery matchmaker generate <project>` | Editing `candidates.jsonl` by hand |
| Build the site | `markery site build <project>` | Writing HTML directly |

**When ROADMAP steps describe file outcomes** ("create `entities.csv`", "populate `variants.csv`"), that means populate the file *after* scaffolding via the CLI — not skip the CLI entirely. Steps that describe what should exist are not permission to create it by hand if a command does the job.

**When planning work that involves a project**, run `markery project onboard <name>` first. The onboard command is the canonical source of truth for entity state, variant coverage, and patent coverage. Do not substitute raw DB queries or file inspection for it.

The only exception: research documents (`RESEARCH.md`, `RESEARCH-AGENDA.md`, `BRIEF.md`) have no CLI command and must be written by hand.

---

## Tests — hermetic vs. data-QA

Two lanes, separated by the `dataqa` pytest marker:

- **Hermetic lane (default, gating):** `pytest -m "not dataqa"`. Depends only on
  the code under test plus fixtures it builds — `tmp_path`, the synthetic repo in
  `tests/fixtures/synthetic.py` (temp corpus DBs + a synthetic project, driven
  via the `MARKERY_ROOT` / `MARKERY_DATA_DIR` env overrides), and mocked HTTP.
  **Never** reads the real `data/` or `projects/`. This is what CI gates, with a
  coverage floor (`--cov-fail-under`, currently 65). It must stay green with
  `data/` and `projects/` moved aside.
- **Data-QA lane (optional):** `pytest -m dataqa`. Real-corpus validation against
  the committed `data/` and `library/` — "is the *content* sound?", not "does the
  machinery work?". Skips when that data is absent.

When adding tests: default to hermetic. Mark a test `@pytest.mark.dataqa` only
when it genuinely validates real committed corpus/library content. Heavy optional
deps (the `enhance` extra: opencv, vtracer, realesrgan) must be `importorskip`-ed
so the hermetic lane skips them cleanly.

---

## Constraints

- **Never commit `.env`** — contains `EPO_CONSUMER_KEY`, `EPO_CONSUMER_SECRET`, `USPTO_API_KEY`; gitignored
- **No Claude attribution in commits** — do not add `Co-Authored-By` or any model credit line to commit messages
- **Classify before acting** — tier, paths, scope; then act
