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
