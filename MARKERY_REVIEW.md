# Markery Root File Gap Analysis

**Date:** 2026-05-20
**Scope:** All root-level `.md` files — `CLAUDE.md`, `CONTEXT.md`, `DESIGN.md`, `DEFERRED.md`, `README.md`, `ROADMAP.md`, `SETUP.md`, `STATUS.md`

---

## Gaps by Severity

### Critical — wrong or missing

**G01 · SETUP.md: `markery trademark verify-credentials` does not exist**
`SETUP.md §2` instructs the user to verify USPTO credentials with `markery trademark verify-credentials`. This command is not implemented. Only `markery patent verify-credentials` exists in `cli.py`. Either the command needs to be added to the trademark specialist CLI, or the SETUP.md instruction needs to be replaced with an alternative verification step (e.g., `markery trademark fetch <known_serial_no>` as a smoke test).

**G02 · DESIGN.md: stale reference to a root-level `RESEARCH.md`**
`DESIGN.md` opens with: *"The research rationale is in `RESEARCH.md`."* There is no `RESEARCH.md` at the repo root. The file exists at `projects/information-systems/RESEARCH.md` — a project artifact, not a tool document. The sentence implies a root-level counterpart to `DESIGN.md` that does not exist. Either drop the sentence or rewrite it to clarify that research rationale lives in each project's `RESEARCH.md`.

---

### Incomplete — accurate but missing content

**G03 · CONTEXT.md: Root File Responsibilities table missing `CLAUDE.md`**
`CLAUDE.md` was added today (Phase 8 P0) and is not listed in the Root File Responsibilities table in `CONTEXT.md`. It should appear as: `CLAUDE.md | Working contract for Claude Code sessions — work classification, routing, review lifecycle, specialist boundary enforcement`.

**G04 · CONTEXT.md: match-review-essay project structure incomplete**
The file structure table for match-review-essay projects (`CONTEXT.md §Project Work Lifecycle`) is missing three files that are required for the project to function:
- `entities.csv` — entity definitions (required by `markery matchmaker build`)
- `variants.csv` — name variant definitions (required by `markery matchmaker build`)
- `seed_patents.json` — manually-identified seed records
- `matches/rejected.jsonl` — explicitly rejected pairs (written by `markery review`)

All four appear correctly in `SETUP.md §Project layout` but are absent from `CONTEXT.md`.

**G05 · DESIGN.md: Historian ownership table missing `rejected.jsonl`**
The Specialist Ownership Pattern table in `DESIGN.md` lists the Historian as owning `confirmed.jsonl, interactive review`. It omits `rejected.jsonl`. Both files are written by `markery review`; both are hand-curated and are not generated. The table entry should read: `confirmed.jsonl, rejected.jsonl, interactive review`.

**G06 · DESIGN.md: Agentic Architecture section predates CLAUDE.md/Scope contracts**
`DESIGN.md §Agentic Architecture` describes the three-surface model (CLI, queries module, persona/) and notes that `identity.md` states what each agent does not do. It does not mention the `## Scope` section added to each `identity.md` in Phase 8 P0, or `CLAUDE.md` as the session-level contract. These additions are the enforcement mechanism that makes the identity limits actionable; `DESIGN.md` should note them.

---

### Wrong value

**G07 · SETUP.md: disk space estimate overstated**
`SETUP.md §Prerequisites` states "~100 MB disk space for the committed databases." Actual sizes as of 2026-05-20:
- `trademarks.duckdb` — 23 MB
- `patents.duckdb` — 9.8 MB (will grow as G09F 1910–1939 is fetched; D001)
- `entities.duckdb` — 2.6 MB

Current total: ~36 MB. Even at full G09F completion, ~40–50 MB is a more accurate estimate. Correct to "~50 MB" to leave headroom for continued fetching without overstating.

---

### Intentional — documented for awareness

**G08 · Deliberate redundancy between CONTEXT.md and DESIGN.md**
Both files describe the specialist ownership pattern and the three-database architecture. `CONTEXT.md` states the structure; `DESIGN.md` explains the rationale. This split is intentional (`CONTEXT.md §Root File Responsibilities` documents both files' distinct purposes). No change needed, but reviewers should be aware the overlap is by design.

**G09 · DESIGN.md internal jargon: "Phase 7 (database review, 2026-05-20)"**
`DESIGN.md §Scope-Neutral Databases` references an internal session label ("Phase 7") that has no definition in `DESIGN.md` or any root file. Acceptable as development history but opaque to a new reader. Low priority — consider replacing with a neutral description on next edit of that section.

---

## Summary

| ID | File | Severity | Action |
|---|---|---|---|
| G01 | SETUP.md | Critical | Add `markery trademark verify-credentials` to CLI, or replace with an alternative verification step |
| G02 | DESIGN.md | Critical | Remove or rewrite opening sentence referencing a root-level `RESEARCH.md` |
| G03 | CONTEXT.md | Incomplete | Add `CLAUDE.md` row to Root File Responsibilities table |
| G04 | CONTEXT.md | Incomplete | Add `entities.csv`, `variants.csv`, `seed_patents.json`, `matches/rejected.jsonl` to match-review-essay project structure |
| G05 | DESIGN.md | Incomplete | Add `rejected.jsonl` to Historian ownership table entry |
| G06 | DESIGN.md | Incomplete | Note CLAUDE.md and Scope sections in Agentic Architecture section |
| G07 | SETUP.md | Wrong value | Correct disk space estimate from ~100 MB to ~50 MB |
| G08 | CONTEXT.md + DESIGN.md | Intentional | No action — overlap by design |
| G09 | DESIGN.md | Low | Replace "Phase 7" jargon with a neutral description on next edit |

---

## Codebase Gap Analysis — `src/markery/` (excluding specialist/)

**Scope:** `src/markery/cli.py`, `src/markery/common/`, `pyproject.toml`, `tests/` structure

---

### Critical — wrong or missing

**G10 · `pyproject.toml`: no `anthropic` SDK dependency**
`CONTEXT.md §Specialist Agents` lists "Anthropic API (for essay drafting)" as a Historian credential, implying Python SDK usage. The `anthropic` package does not appear in `pyproject.toml` dependencies or optional-dependencies. Clarify: if essay drafting is done through a Claude project (not Python API calls), remove the credential reference from `CONTEXT.md`. If Python SDK calls are planned, add `anthropic` to the appropriate dependency group.

**G11 · `cli.py`: `markery historian`, `markery publisher`, `markery wikipedia` undocumented in README**
All three subcommands exist in `cli.py` and are registered in `_SUBCOMMANDS`. None appear in `README.md §CLI`. The `markery patent signals` and `markery patent fetch <project> --confirmed` subforms also exist in the cli.py docstring but are absent from README. The README CLI section is materially incomplete as a reference.

---

### Incomplete — accurate but missing content

**G12 · `common/config.py`: `Project` class has undocumented properties**
The `Project` dataclass in `config.py` defines five properties that reference real project files not mentioned in any root documentation:
- `.brief` → `matches/BRIEF.md` — machine-generated project brief, populated by `markery historian prepare`
- `.objectives` → `OBJECTIVES.md` — purpose and scope unknown from docs alone
- `.references` → `references/` — a committed directory in `information-systems/` with no documented format
- `.pipeline_state` → `matches/pipeline_state.json` — pipeline state tracking file

All four are present in `projects/information-systems/` as committed files. `CONTEXT.md` and `SETUP.md` project layout tables do not list them. Either they are project-specific artifacts that belong only in `projects/information-systems/README.md`, or they are part of the match-review-essay structure and should be added to `CONTEXT.md §Project Work Lifecycle`.

**G13 · Test suite: `common/auth.py`, `common/config.py`, and `cli.py` have zero test coverage**
These three modules are shared infrastructure used by every specialist:
- `common/auth.py` — credential loading with `.strip()` on secrets; the leading-space handling is a known correctness constraint with no test
- `common/config.py` — project path contracts; `Project` dataclass properties are the canonical path definitions used everywhere
- `cli.py` — subcommand routing; unknown command handling, help output, and dispatch table are untested

Tests exist for all five specialist areas (307 collected). The common layer and CLI router have none.

---

### Wrong value

**G14 · `pyproject.toml`: `duckdb>=0.9.0` lower bound too permissive**
DuckDB changed its Python connection API between 0.9.x and 1.0.x. The current codebase targets 1.x behavior. The lower bound `>=0.9.0` would permit installation of a version that would break at runtime. Tighten to `>=1.0.0` or pin to the tested minor version.

---

### Minor

**G15 · `tests/__pycache__/test_score.cpython-312-pytest-9.0.3.pyc` is a ghost**
`tests/test_score.py` no longer exists, but its compiled bytecode remains in `tests/__pycache__/`. The source was likely moved to `tests/specialist/matchmaker/test_score.py` and the cache not cleaned. Not harmful but adds noise. Remove with `find tests/__pycache__ -name 'test_score*.pyc' -delete`.

**G16 · `pyproject.toml`: version `0.2.0a0` not surfaced anywhere**
`__init__.py` exports `__version__ = "0.2.0a0"` from `pyproject.toml`. No root document references the version. Not a gap in documentation so much as an unused artifact — if version is tracked, it should appear somewhere (README header, `markery --version` flag, STATUS.md). If it is not actively maintained, it is noise.

---

### Summary addendum

| ID | File/Module | Severity | Action |
|---|---|---|---|
| G10 | `pyproject.toml` + `CONTEXT.md` | Critical | Resolve Anthropic SDK: add dependency or remove credential reference |
| G11 | `cli.py` + `README.md` | Critical | Add missing subcommands to README CLI section |
| G12 | `common/config.py` + `CONTEXT.md` | Incomplete | Document or scope undocumented Project properties |
| G13 | `tests/` | Incomplete | Add tests for `common/auth.py`, `common/config.py`, `cli.py` |
| G14 | `pyproject.toml` | Wrong value | Tighten `duckdb` lower bound to `>=1.0.0` |
| G15 | `tests/__pycache__/` | Minor | Delete ghost `test_score.pyc` |
| G16 | `pyproject.toml` | Minor | Surface version or stop tracking it |
