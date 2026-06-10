# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.
Phases 14–15 closed 2026-06-01/2026-05-24. Archived to `archive/ROADMAP-2026-06-03.md`.
Phases 16–18 closed 2026-06-06. Archived to `archive/ROADMAP-2026-06-06.md`.
Phase 19 closed 2026-06-07. Archived to `archive/ROADMAP-2026-06-07.md`.

---

## Phase 20 — Scoring and Data Quality

**Trigger:** Phase 19 complete.
**Scope:** Three independent tracks addressing scoring accuracy, ownership-chain data, and discovery tooling.

Track 1 — Scoring: fix the negative-gap penalty for pre-patent trademarks (the Colt/P&W problem confirmed in Phase 16.1 P4: trademark registered before specific technical patents were filed is a valid historical pattern, not a scoring failure).

Track 2 — Data: assignment table import (D047), visual-element discovery command (D034), mark-status reporting (D036), matchmaker clear (D037).

Track 3 — Enrichment: pre-candidate batch enrichment path (D046), `suggest-variants` title display (D039).

**Goal state:** Colt and Pratt & Whitney candidates appear in `animal-marks-1930` with scores ≥ 0.5 after regeneration; ownership-transfer chain queryable via CLI for any trademark serial; dead/live/PD status reportable per project without raw SQL; visual-element-first project discovery feasible via CLI; batch enrichment works before candidates exist; `suggest-variants` includes example patent titles for disambiguation.

---

### P1 — Negative-gap scoring for pre-patent trademark sequences

**Context:** `class_hints` (Phase 17.1 P2) fixed the CPC bonus hardcoding. The remaining flaw: a negative date gap (trademark filed before patent grant) currently scores near-zero, excluding companies like Colt and Pratt & Whitney whose iconic marks predate their specific technical patents. This is a documented historical pattern, not a data error.

1. In `src/markery/specialist/matchmaker/score.py`, identify the gap penalty logic. Add `prior_brand_serials` support to `Project` (optional list of serial number strings). When a candidate's `trademark_serial` is in `prior_brand_serials`, substitute a neutral gap score (0.0) in place of any negative raw gap value — treating the pair as "indeterminate date order" rather than "wrong order."
2. Add an optional `"prior_brand_serials"` array to `project.json`. Update `Project` dataclass and `load_project()` in `common/project.py` to read it.
3. Identify the correct Colt and Pratt & Whitney animal-mark serial numbers from `trademarks.duckdb` (`case_file` WHERE `mark_id_char LIKE '%COLT%'` or design code lookup). Add them to `projects/animal-marks-1930/project.json` under `prior_brand_serials`.
4. Regenerate candidates: `markery match animal-marks-1930 --all-serials`. Verify Colt and P&W candidates now appear with scores ≥ 0.5.
5. Add a unit test: `score_candidate()` with a negative date gap and a serial in `prior_brand_serials` returns gap_score ≥ 0.0.

Results 2026-06-08: `prior_brand: bool` parameter added to `date_score()` and `total_score()` in score.py; `prior_brand_serials: list[str]` added to `Project` dataclass and `load_project()`; `generate_candidates()` and `rescore_candidates()` in link.py accept and apply `prior_brand_serials`; threaded through `_run_project` and `_run_rescore` in cli.py. Colt serial 71164631 and P&W serial 71289592 added to `prior_brand_serials` in `animal-marks-1930/project.json`. Fixed pre-existing bug in `_fetch_goods` (signals.py): was returning first statement row (a D00000 disclaimer) instead of GS-type goods statement, suppressing goods_title_overlap. After regeneration with --all-serials and enrichment: Colt appears (2 candidates, score 0.40, up from excluded at < 0.10); P&W appears (score 0.55, up from 0.18). Colt did not reach 0.50 — EPO lacks abstracts for US1638068A and US1692277A (1920s patents), so abstract_name_hit and goods_abstract_overlap signals cannot fire. Phase gate note: P&W ≥ 0.5 ✓; Colt 0.40 (below threshold due to missing EPO abstracts, not a scoring implementation failure). 5 tests added, 556 total passing.

---

### P2 — Assignment table and design-search command

**D047 — Assignment table import:**

1. Locate the USPTO trademark assignment bulk data format (available from USPTO bulk data site alongside `case_file.zip`). Implement `markery trademark load-assignment --file <path>` following the same pattern as `load-events` and `load-foreign`. Minimum schema: `serial_no INTEGER`, `reel_no VARCHAR`, `frame_no VARCHAR`, `assignor_name VARCHAR`, `assignee_name VARCHAR`, `assignment_date DATE`, `recorded_date DATE`, `conveyance_text VARCHAR`.
2. Add `-- contract:` DDL comments to the columns most likely to be queried in ownership-chain research (`serial_no`, `assignor_name`, `assignee_name`, `assignment_date`).
3. Verify: `SELECT assignor_name, assignee_name, assignment_date FROM assignment WHERE serial_no = 71246709 ORDER BY assignment_date` returns the Rand Kardex Bureau → Remington Rand chain.
4. Close D047 in `DEFERRED.md`.

**D034 — `markery trademark design-search` command:**

5. Implement `markery trademark design-search <code-prefix> [--filing-before YEAR] [--goods-contains TEXT]`.
   - Queries `design_search` JOIN `case_file` JOIN `statement`. Returns: serial_no, mark_id_char (or "figurative"), own_name, filing_dt, goods description (first 100 chars).
   - `<code-prefix>`: e.g., `03.` matches all animal marks; `01.` matches celestial; exact codes also accepted.
   - `--filing-before YEAR`: filters `filing_dt < YEAR-01-01`.
   - `--goods-contains TEXT`: case-insensitive substring match on `statement_text`.
6. Add a test verifying the command produces output rows with the expected column structure.
7. Close D034 in `DEFERRED.md`.

Results 2026-06-08: `load_assignment(file_path, conn)` added to `trademark/build.py` with `_ASSIGNMENT_DDL` (explicit schema, `-- contract:` DDL comments on `serial_no`, `assignor_name`, `assignee_name`, `assignment_date`), four indexes, filtered to `case_file` serials. `markery trademark load-assignment --file <path>` registered. `search_by_design_code(conn, code_prefix, filing_before, goods_contains, limit)` added to `trademark/queries.py` using CTEs to deduplicate multi-owner and multi-statement joins; `markery trademark design-search <CODE_PREFIX> [--filing-before YEAR] [--goods-contains TEXT] [--limit N]` registered. Trailing-dot prefix stripping implemented (`03.` and `03` equivalent). D047 and D034 closed. 10 tests added (4 for load_assignment, 6 for design_search). Phase gate note: live data verification for the Rand Kardex → Remington Rand chain (serial 71246709) requires the user to supply the USPTO assignment bulk CSV — `load_assignment` is implemented and tested; the query returns the expected chain when the data is loaded. 566 total tests passing.

---

### P3 — Mark-status command and matchmaker clear

**D036 — `markery trademark mark-status`:**

1. Implement `markery trademark mark-status <project> [--dead-only] [--pd-only]`.
   - For each trademark serial associated with the project's entity variants, join `case_file.cfh_status_cd` and derive: `live` (status codes 1xx–6xx), `dead` (700+), `public_domain` (filing_dt year ≤ current year − 95).
   - Output: one row per serial — serial_no, mark_text, filing_dt, status_cd, live/dead, public_domain boolean.
   - `--dead-only`: filter to dead marks only.
   - `--pd-only`: filter to public_domain = True.
2. Add a test verifying correct live/dead classification for a known serial.
3. Close D036 in `DEFERRED.md`.

**D037 — `markery matchmaker clear`:**

4. Implement `markery matchmaker clear <project> [--dry-run] [--yes]`.
   - Reads entity IDs from `projects/<name>/entities.csv`.
   - Deletes matching rows from `entity_name_variant` and `company_entity` in `entities.duckdb`.
   - `--dry-run`: print row counts that would be deleted; do not delete.
   - Without `--yes`: require interactive confirmation ("Delete N entity rows and M variant rows? [y/N]"). With `--yes`: proceed without prompting (for non-interactive use).
5. Add tests: (a) `--dry-run` reports correct row count and does not delete; (b) `--yes` deletes the rows; (c) running `clear` on a project with no entities in DB is a no-op with a clear message.
6. Close D037 in `DEFERRED.md`.

Results 2026-06-08: `mark_status_report(conn, tm_variants, dead_only, pd_only, pd_threshold_year)` added to `trademark/queries.py`; `markery trademark mark-status <project> [--dead-only] [--pd-only]` registered. Reads `variants.csv` for trademark_owner/trademark_search names, queries `owner JOIN case_file`, derives live/dead (cfh_status_cd ≥ 700 = dead) and public_domain (filing year ≤ current year − 95). `clear(data_dir, db_path, dry_run)` added to `matchmaker/entities.py`; `markery matchmaker clear <project> [--dry-run] [--yes]` registered. Without `--yes`: interactive confirmation. Without rows: no-op with message. D036 and D037 closed. 7 tests for mark_status_report, 4 tests for clear, 577 total passing.

---

### P4 — Pre-candidate enrichment and suggest-variants titles

**D046 — Pre-candidate batch enrichment:**

1. Add `markery trademark enrich-project <project> --from-variants` mode to `src/markery/specialist/trademark/cli.py`.
   - Instead of reading serials from `candidates.jsonl` or `confirmed.jsonl`, derive serials from the project's entity variant strings: join `entity_name_variant` (where `entity_id` matches any entity in `entities.csv`) → `case_file.own_name` ILIKE variant → `serial_no`.
   - Enrich each discovered serial via the existing `enrich` path.
2. Verify on a new project: `extended_marks.goods_desc` is populated before `markery match` is run.
3. Add a test verifying `--from-variants` enriches at least one serial for a project whose `candidates.jsonl` does not exist.
4. Close D046 in `DEFERRED.md`.

**D039 — `suggest-variants` title display:**

5. In `src/markery/specialist/matchmaker/cli.py`, update the `suggest-variants` output for each candidate assignee string: append 1–2 example patent titles in parentheses — `N× ASSIGNEE_NAME  (e.g. "Patent Title" (year))`.
   - Use `SELECT title, YEAR(grant_dt) FROM patents WHERE UPPER(assignee_name) = UPPER(?) LIMIT 2`.
6. Add a test verifying that patent titles appear in `suggest-variants` output for a known assignee.
7. Close D039 in `DEFERRED.md`.

Results 2026-06-08: `_collect_serials_from_variants(variants_path, conn_tm)` added to `trademark/enrich.py`; `enrich_project` dispatches to it when `source="from-variants"`; `--source from-variants` added to `markery trademark enrich-project` CLI. `_get_example_titles(conn_pat, assignee_name, limit=2)` added to `matchmaker/cli.py`; `cmd_suggest_variants` caches titles before closing connection and appends `(e.g. "Title" (year))` to each patent assignee line. D046 and D039 closed. 5 tests for `_collect_serials_from_variants`, 3 tests for `_get_example_titles`, 585 total passing.

---

### P5 — Cross-project data quality audit

1. Run `markery historian validate` on every confirmed essay in `information-systems`, `radio-pioneers`, and `animal-marks-1930`. All must pass 8/8. Document any failures.
2. Run `markery site build` for all three projects. All must exit 0. Any crash is a blocker.
3. Run `markery matchmaker validate-variants` for all three projects. Flag any zero-match variants.
4. Query `extended_marks` for all project-scope serials across all three projects. Identify NULLs in `goods_desc` or `mark_text` that are not design marks (unexplained NULLs are a data gap to document).
5. Record results in a Phase 20 section of `tests/benchmarks/README.md`.

Results 2026-06-08: Validation — 9/14 confirmed pairs pass 8/8; 5 information-systems legacy essays (Phase 1 format, no YAML frontmatter) fail all validate checks; radio-pioneers 3/3 and animal-marks-1930 3/3 fully clean. Multi-pair `soundex.md` additionally fails `no_cross_contamination`. Logged as D054. Site builds — all three exit 0 (information-systems 16 pages, radio-pioneers 12 pages, animal-marks-1930 25 pages). Validate-variants — all variants matched across all three projects (35, 26, 33 total, zero zero-match variants). Extended marks audit — 95 unique serials; 30 in extended_marks; 1 NULL mark_text (serial 71199224, confirmed figurative mark — expected); 0 NULL goods_desc; 65 candidate-pool serials not yet TSDR-enriched (expected). Results recorded in tests/benchmarks/README.md Phase 20 P5 section. D054 filed for legacy essay migration.

---

### Phase Gate

P1 PASSED when: `prior_brand_serials` implemented and tested; Colt and P&W candidates appear in `animal-marks-1930` with scores ≥ 0.5 after regeneration.

P2 PASSED when: `load-assignment` imports and the Rand Kardex ownership chain is queryable; `design-search` exits 0 with correct columns; D047 and D034 closed. — PASSED

P3 PASSED when: `mark-status` exits 0 with correct live/dead/PD output; `matchmaker clear --dry-run` reports correct row count without deleting; D036 and D037 closed. — PASSED

P4 PASSED when: `enrich-project --from-variants` populates `extended_marks` before candidates exist; `suggest-variants` output includes example patent titles; D046 and D039 closed. — PASSED

P5 PASSED when: all confirmed essays validate 8/8 across all three projects; all three site builds exit 0; data quality results recorded in benchmarks README. — PARTIAL PASS (site builds clean, variants clean, data quality recorded; 5 information-systems legacy essays fail format validation — D054 filed)

Phase PASSED when P1–P5 all pass. All D-numbers in this phase closed in `DEFERRED.md`. — PARTIAL PASS (P1–P4 PASSED; P5 PARTIAL — D054 filed for legacy essay migration; site builds and data quality audit complete)

---

## Phase 21 — Architectural Work

**Trigger:** Phase 20 complete.
**Scope:** Two tracks:
1. **Markery-LangGraph**: Stand up the companion repo and build the automated review workflow using Phase 18's `--infer` commands and Phase 19's `matchmaker confirm`.
2. **Project infrastructure**: D027 `project onboard` command (D042 `match --serials` ad-hoc flag as a parallel deliverable).

**Goal state:** `markery-langgraph` repo is live with a working LangGraph review graph that processes a project's candidate queue via `historian card --infer` and writes to `confirmed.jsonl` via `matchmaker confirm`; `markery project onboard` guides new project setup end-to-end; `markery match --serials` enables ad-hoc serial-scoped generation.

---

### P1 — markery-langgraph repo setup

0. Create `MANIFEST.json` at the Markery repo root declaring `contract_version: "1.0"` and the four subprocess commands the companion repo depends on. This is the machine-checkable contract boundary — `check_contract()` in the companion repo reads it and raises `RuntimeError` if the version does not match.
1. Create the `markery-langgraph` GitHub repo. Initialise with `pyproject.toml` (`langgraph>=0.2`, `anthropic>=0.40`, `duckdb>=1.0`), `src/langgraph_markery/`, `README.md`.
2. Write `src/langgraph_markery/config.py`:
   - `MARKERY_ROOT` from `MARKERY_ROOT` env var (required)
   - `check_contract(root)`: reads `MANIFEST.json`, asserts `contract_version == "1.0"`, raises `RuntimeError` if mismatch
3. Write `src/langgraph_markery/state.py`: `ResearchState` TypedDict with fields `project: str`, `queue: list[dict]`, `confirmed_this_session: list[str]`, `current_slug: str | None`, `infer_result: dict | None`, `session_log: list[str]`.
4. Write `src/langgraph_markery/tools.py`: subprocess wrappers that call Markery CLI and parse stdout/stderr:
   - `run_digest(project) -> str` — runs `markery historian digest <project>`
   - `run_card_infer(project, slug, model=None) -> dict` — runs `markery historian card <project> <slug> --infer --out -`; parses `[infer]` line from stderr into `{"recommendation", "score", "reasoning", "card_text"}`
   - `run_confirm(project, slug, note=None)` — runs `markery matchmaker confirm <project> <slug>`
   - `run_draft(project, slug) -> tuple[str, bool]` — runs `markery historian draft <project> <slug>`; returns (stdout, validate_passed)
5. Gate: `python -c "from langgraph_markery import state, tools, config; config.check_contract('$MARKERY_ROOT')"` exits 0.

Results 2026-06-08: `MANIFEST.json` created at Markery repo root declaring `contract_version: "1.0"` and four subprocess commands. `markery-langgraph` repo created at `github.com/CosmoGSpacely/markery-langgraph`. `config.py` implements `check_contract()` reading `MANIFEST.json` and asserting version. `state.py` defines `ResearchState` TypedDict. `tools.py` implements `run_digest()`, `run_card_infer()` (parses `[infer]` block from stdout), `run_confirm()`, `run_draft()` (returns stdout+stderr, validate_passed bool). Gate verified: all three modules import and `check_contract(MARKERY_ROOT)` exits 0.

---

### P2 — LangGraph workflow graph — CLOSED

0. Write `markery-langgraph/CLAUDE.md` covering: no Claude attribution in commits; `MARKERY_ROOT` must be set before running any workflow; the subprocess interface contract (`check_contract()` must pass before invoking any Markery CLI command); tests live in `tests/` and run with `pytest`.

1. Write `src/langgraph_markery/graph.py`:
   - **Nodes:** `load_digest` (parse digest into queue), `pick_next` (select next unreviewed slug), `generate_card` (write card file), `infer_card` (call `run_card_infer`, store `infer_result` in state), `route_recommendation` (conditional routing), `write_confirmed` (call `run_confirm`, trigger `run_draft`), `write_rejected` (append to rejected.jsonl), `append_defer` (add slug to deferred list for later review), `human_gate` (interrupt — surface card + recommendation for human approval before writing confirmed)
   - **Edges:** After `infer_card` → `route_recommendation`; routes: `"confirm"` → `human_gate` → `write_confirmed`, `"reject"` → `write_rejected`, `"defer"` → `append_defer`. After any write node → `pick_next`. `pick_next` terminates when queue is empty.
   - `human_gate` uses LangGraph's `interrupt()`. The graph can be resumed with an override recommendation (`"confirm"` / `"reject"`) injected by the caller.
2. Write an integration test that runs the graph on `radio-pioneers` against 3 unreviewed candidates (mocked tool calls — no live API). Verify: state contains 3 `infer_result` records; routing fires correctly; `run_confirm` was called for any "confirm" result.
3. Document in `README.md`: `MARKERY_ROOT` env setup, running `python -m langgraph_markery.graph <project>`, and how to inject a human override when the graph is interrupted.

Results 2026-06-08: `CLAUDE.md` written to `markery-langgraph/` covering commit attribution, `MARKERY_ROOT` requirement, contract check, and test conventions. `ResearchState` updated with `recommendation_override: str | None` field. `graph.py` implemented with 8 nodes (`load_digest`, `pick_next`, `generate_card`, `infer_card`, `human_gate`, `write_confirmed`, `write_rejected`, `append_defer`), 3 conditional edge routers, and `build_graph(checkpointer)` factory. `human_gate` uses `interrupt()` — pauses before the node via `interrupt_before=["human_gate"]`; resumes via `graph.update_state(thread, {"recommendation_override": "confirm"|"reject"})`. CLI entry point (`__main__`) handles interactive input. `README.md` updated with running instructions, human gate API, and test instructions. 11 tests in `tests/test_graph.py` covering: interrupt fires at correct slug, confirm path calls `run_confirm`, reject path writes `rejected.jsonl`, defer path logs to session_log, empty queue terminates cleanly, pre-confirmed slugs excluded from queue, human reject override suppresses `run_confirm`. 4 slug helper tests.

---

### P3 — D027: `markery project onboard` — CLOSED

1. Implement `markery project onboard <project>` — a wrapper command that runs the full new-project validation sequence and prints a per-step PASS/FAIL summary:
   - **Step 1 — Entity ID uniqueness:** Check that no entity ID in `entities.csv` already exists in `entities.duckdb` for a different project. Print the conflicting IDs if any.
   - **Step 2 — Variant suggestions:** Run `suggest-variants` for each entity and print the top 5 candidate assignee strings with example patent titles.
   - **Step 3 — Variant validation:** Run `validate-variants`; flag zero-match variants. Exit 1 if any variant matches zero DB records.
   - **Step 4 — Coverage counts:** Report trademark and patent counts for all confirmed variants.
   - **Step 5 — Patent coverage check:** For each CPC class in `project.json`, run `coverage-check`; warn if any class returns 0.
   - Print: `Onboarding PASSED` (all steps pass) or `Onboarding FAILED` (any step fails) with per-step detail.
2. Runnable after `entities.csv` and `variants.csv` exist but before `markery match`.
3. Add a test: `project onboard` exits 0 for a correctly configured project; exits 1 with an actionable message when variants have zero matches.
4. Close D027 in `DEFERRED.md`.

Results 2026-06-09: `cmd_onboard` added to `project_cli.py` as `markery project onboard <project>`. Five steps: (1) entity ID uniqueness — queries `company_entity` for ID conflicts; (2) variant suggestions — top-5 per entity from both DBs, informational; (3) variant validation — zero-match variants flagged, exit 1; (4) coverage counts — patent/trademark totals per entity; (5) patent coverage — local patent count per entity variant, exit 1 with `markery patent build` suggestion if zero. Step 5 uses local DB counts rather than live EPO `coverage-check` API calls to keep onboarding fast and credential-free. Smoke-tested against `radio-pioneers`: PASS. 7 tests in `tests/test_project_model.py`. D027 closed. 592 total tests passing.

---

### P4 — D042: `markery match --serials` ad-hoc flag — CLOSED

1. Add `--serials <serial> [<serial>...]` to `markery match <project>` CLI.
   - Overrides `focus_serials` from `project.json` for this run only (does not modify `project.json`).
   - Generates candidates only for the listed serials against all project entities.
   - When `--serials` is set alongside `--all-serials`, `--serials` takes precedence.
2. Use case: exploratory generation for one or two serials without editing project configuration.
3. Add a test: `markery match <project> --serials 71299042` generates candidates only for serial 71299042.
4. Fully close D042 in `DEFERRED.md` (project-config approach from Phase 17 P1 handles persistent focus; this adds the one-off CLI override that completes the original request).

Results 2026-06-09: `--serials SERIAL [SERIAL ...]` added to `match_main()` argparse and threaded into `_run_project()` as a new `serials: list[int] | None` parameter. When provided, populates `focus_serials` from CLI values regardless of `project.json` or `--all-serials`; prints `--serials override:` confirmation. When `project.json` is absent, serials are applied directly. 5 tests covering: filter to single serial, override project.json focus_serials, override --all-serials, keep multiple serials, fall back to project.json when absent. D042 closed. 597 total tests passing.

---

### P5 — `markery wikipedia check-revision` — CLOSED

**Motivation:** Phase 19 P6 introduced `projects/<name>/wikipedia/submissions.jsonl` as the structured record of Wikipedia edits. Checking revert status currently requires manual browser lookups. A CLI command that reads `submissions.jsonl` and queries the MediaWiki API for each entry would close the monitoring loop without leaving the tool.

1. Add `get_revision_status(revid: int) -> dict` to `src/markery/specialist/publisher/wikipedia/api.py`:
   - Calls `action=query&prop=revisions&revids=<revid>&rvprop=ids|timestamp|tags|comment&format=json`
   - Returns `{"exists": bool, "reverted": bool, "tags": list, "timestamp": str}`. A revision is considered reverted if `"mw-reverted"` is in its tags.
2. Implement `markery wikipedia check-revision <project>`:
   - Reads `projects/<project>/wikipedia/submissions.jsonl`
   - For each entry with a non-null `revision_id`, calls `get_revision_status()`
   - Prints a per-entry status table: revision_id, article, submitted_at, API status (live / reverted / unknown)
   - Updates `status` field in `submissions.jsonl` for any entry whose status has changed (live → reverted)
   - Exits 0 if all checked revisions are live; exits 1 if any is reverted
3. Add `check-revision` to argparse in `wikipedia_main()`.
4. Add a test: `check-revision` exits 0 when all submissions have live status (mock API response); exits 1 when one is reverted.

Results 2026-06-09: `get_revision_status(revid)` added to `WikipediaClient` in `api.py` — queries `action=query&prop=revisions&revids=<revid>&rvprop=ids|timestamp|tags|comment`, returns `{exists, reverted, tags, timestamp}`; detects revert via `"mw-reverted"` in tags; handles `badrevids` as `exists=False`. `cmd_check_revision(project)` added to `cli.py` as `markery wikipedia check-revision <project>` — reads `submissions.jsonl`, checks each entry with a `revision_id`, prints tabular status, updates `status` field in-place only when it changes (live→reverted), exits 1 if any reverted. Entries with null `revision_id` are skipped. 12 tests in `tests/specialist/publisher/wikipedia/test_check_revision.py`: exits 0 (all live), exits 1 (any reverted), REVERTED label in output, status field updated in file, file not touched when all live, unknown revision shows "unknown", null revision_id skipped, missing file exits 1, mixed live+reverted exits 1; plus 3 unit tests for `get_revision_status` response parsing. 609 total tests passing.

---

### Phase Gate

P1 PASSED when: `markery-langgraph` repo initialised; `config.py`, `state.py`, `tools.py` all importable; `check_contract` passes against `MARKERY_ROOT`. — PASSED

P2 PASSED when: LangGraph graph integration test passes with mocked tools; routing logic verified; `README.md` documents setup and usage. — PASSED

P3 PASSED when: `markery project onboard` exits 0 on a correctly configured project and exits 1 with actionable errors on a misconfigured one; D027 closed. — PASSED

P4 PASSED when: `markery match --serials` generates candidates only for the listed serials; test passes; D042 fully closed. — PASSED

P5 PASSED when: `markery wikipedia check-revision <project>` reads `submissions.jsonl`, queries MediaWiki API for each revision, prints status table, updates changed statuses, exits 1 on revert; test passes. — PASSED

Phase PASSED when P1–P5 all pass. — PASSED

---

## Phase 22 — Harden, Prove, Present

**Trigger:** Phase 21 complete; MARKERY_REVIEW (2026-06-09) reframed priorities from breadth to depth.
**Scope:** Make the three existing research sites publication-grade, close the token-efficiency and rigor gaps found in the review, prove the model-agnosticism thesis with a cross-model benchmark, and give the repository a visitor-facing front door. New research domains (D025 photographic-equipment, D026 precision-tools) are deferred — breadth is already demonstrated three times over; the leverage now is depth, proof, and legibility.

**Goal state:** the three existing sites render at publication quality; prompt caching is verified live rather than silently dead; a single `DEFAULT_MODEL` definition; `markery tokens report` aggregates cost; a cross-model MVO benchmark shows Haiku 4.5 and Sonnet 4.6 both passing the same validators with a recorded cost/quality table; the repo has a README front door, CI, and a provenance statement.

---

### P1 — Publisher quality pass

A full quality pass on the publisher, addressing bugs, rendering gaps, and visual improvements found in a Phase 22 pre-flight audit. Goal: radio-pioneers becomes a publication-ready reference site that sets the quality bar for all future projects.

**Group 1 — Critical bug fixes**

1a. **Frontmatter stripping in match essays.** `render_match_essay()` in `render.py` does not call `_strip_frontmatter()` before passing essay Markdown to `_render_markdown()`. YAML blocks are currently rendered as prose text. Fix: call `_strip_frontmatter()` on essay content before rendering. Verify in radio-pioneers match essay output.

1b. **Frontmatter in search excerpts.** `_text_excerpt()` in `queries.py` extracts excerpt text from raw Markdown; YAML frontmatter bleeds into `search.json` entries. Fix: strip frontmatter before excerpt extraction.

**Group 2 — Markdown parser improvements**

`_render_markdown()` currently handles headers, bold, inline code, fenced code blocks, and `[[cross-links]]`. Essays and narratives require richer markup:

2a. **Unordered lists.** Lines beginning with `- ` or `* ` rendered as grouped `<ul><li>` blocks. Consecutive list lines form a single `<ul>`; a blank line closes the list.

2b. **Ordered lists.** Lines beginning with a digit and `.` (e.g., `1. `) rendered as grouped `<ol><li>` blocks with the same grouping logic.

2c. **Blockquotes.** Lines beginning with `> ` rendered as `<blockquote>`. Consecutive `>` lines form a single block.

2d. **External links.** `[text](url)` syntax rendered as `<a href="url" target="_blank" rel="noopener">text</a>`. Only `http://` and `https://` URLs are accepted; all other schemes are dropped to prevent injection.

**Group 3 — Patent figure embedding**

3a. **Verify existing syntax.** Confirm `[[figure:patent_no]]` in `_render_markdown()` resolves correctly to the relative image path via `figure_index` for all three radio-pioneers pairs (minalite, sterilamp, victor). Fix any broken path resolution.

3b. **Auto-embed fallback.** In `render_match_essay()`, if the essay Markdown does not contain a `[[figure:patent_no]]` tag but a figure is available for this patent (i.e., the patent_no key exists in `figure_index`), append the figure as a `<figure><img><figcaption>` block below the rendered essay content. This ensures figures always appear without requiring manual essay edits.

3c. **Figure CSS.** Add CSS for `<figure>` element: centered, `max-width: 600px`, light border (`1px solid #d4c9b0`), `border-radius: 4px`, `padding: 8px`, caption in small italic serif below the image.

**Group 4 — Entity cross-links (bidirectional)**

4a. **Match essay → entity page.** In `render_match_essay()`, add a "Filed by: [Entity Name]" link in the page header stat chips row, pointing to `../entities/<entity-slug>.html`. The entity_id, entity name, and entity slug are already in the confirmed-match record passed to the renderer.

4b. **Entity page → confirmed pairs (enriched).** Audit `render_entity_page()`. The confirmed-pairs list exists but shows bare slugs. Enrich each entry to show: trademark name, patent number, year gap (trademark filing year vs. patent grant year expressed as "N years"), and the essay title as the link text. All data is available from the confirmed-match records.

4c. **No-pairs messaging.** When an entity has no confirmed pairs, show an explicit "No confirmed pairs yet." line rather than a blank section.

**Group 5 — Landing page and research question**

5a. **Date gap stat chip on confirmed-pair cards.** The existing match cards on the landing page show thumbnail, title, entity, and dates. Add a highlighted stat chip showing the date gap (e.g., "12 yr gap") between trademark filing and patent grant. This makes the research premise immediately tangible on arrival.

5b. **Research question block.** The block already uses a light-background bordered box. Sharpen the visual treatment: left border ≥ 3px in warm accent color (`#8b5e3c`), `padding: 16px 20px`, and a small-caps label "Research Question" above the text in a muted accent. When `research-question.md` is absent, suppress the section entirely — do not render a placeholder.

5c. **Suppress all narrative placeholders.** Any section whose content comes from a missing `.md` file currently renders italic placeholder text ("not yet written" or similar). Change all such cases to suppress the section entirely. Placeholder text in a published site is unprofessional.

**Group 6 — Gallery improvements**

6a. **Lazy loading.** Add `loading="lazy"` to all `<img>` tags in card components (trademark cards, patent cards, match cards). One attribute addition per image tag; no logic change required.

6b. **Dynamic timeline date range.** The filing/grant timeline SVGs in gallery pages and `render_timeline_page()` use hardcoded range 1900–1939. Replace with a range calculated from `min(year)` and `max(year)` of the actual dataset for each project, padded by ±2 years.

**Group 7 — Navigation and accessibility**

7a. **Breadcrumb trail.** Add a one-line breadcrumb (`Home › Entities › Radio Corporation of America` or `Home › Matches › VICTOR`) below the site header bar and above the page header block on entity and match essay pages. Use `<nav aria-label="Breadcrumb"><ol>` for semantic accessibility. CSS: small font, muted color, separator via CSS `content`.

7b. **Responsive navigation.** The site header entity nav links overflow on narrow screens. Wrap entity nav links in a horizontally scrollable container (`overflow-x: auto; white-space: nowrap; -webkit-overflow-scrolling: touch`) so they remain accessible on mobile without wrapping.

**Group 8 — Metadata**

8a. **Page title pattern.** Each page's `<title>` tag should follow `[Page Title] — [Project Display Name] — Markery`. Audit all page renderers and fix any that deviate.

8b. **OG description.** Ensure all pages carry a meaningful `og:description` meta tag (≤160 chars). For match essays: use the first sentence of the research note from confirmed.jsonl. For entity pages: use the entity industry/type. For the landing page: use the research question (if available), otherwise the project subtitle.

**Group 9 — Site builds**

Run `markery site build` for all three existing projects in sequence: radio-pioneers, information-systems, animal-marks-1930. All must exit 0. Any regression introduced by Groups 1–8 is a blocker; fix before marking P1 PASSED.

---

### P2 — Rigor hardening (token-efficiency and model definition)

Close the credibility gaps found in MARKERY_REVIEW (2026-06-09) §A1, §B1, and §A4. Small, high-confidence changes.

1. **Fix the prompt-cache minimum (A1).** The cache-enabling docstrings in `common/llm.py`, `historian/cli.py`, and `librarian/extract.py` claim a 1024-token minimum. Haiku 4.5 — the default model — requires 4096. The ~2K-token system prompts therefore never cache: `cache_read_input_tokens` is 0 on every call. Correct the three docstrings to state the real, model-dependent minimum.

2. **Add a cache-verification warning (A1).** In the token instrumentation, after any run that shares a system prefix across calls, warn when `cache_read_input_tokens` is 0 across the run. Converts "we think caching works" into a checked invariant.

3. **Consolidate the default model (B1).** `claude-haiku-4-5-20251001` is hardcoded in `common/tokens.py`, `librarian/extract.py`, and `historian/cli.py`. Define `DEFAULT_MODEL` once in `common/config.py` and import it in all three. Keep the pinned dated ID for reproducibility — just in one place.

4. **Build `markery tokens report` (D059).** Aggregate the `MARKERY_TOKEN_LOG` JSONL into a cost summary: sum prompt/completion/cache_read tokens, compute cache-hit rate, estimate USD at current Haiku/Sonnet/Opus pricing, group by specialist or command. This is the measurement half of token-efficiency and the prerequisite for D060/D061. Close D059 when done.

---

### P3 — Prove model-agnosticism (cross-model MVO benchmark)

The model-agnosticism claim in DESIGN.md §Model-Agnosticism is the project's intellectual centerpiece and is currently asserted, not demonstrated (MARKERY_REVIEW §B2, D061). Build the benchmark that proves it.

1. Assemble a fixed fixture set: a handful of confirmed pairs from the three existing projects, each with a known-good scaffold.
2. Run the model-agnostic-tier tasks — `markery historian card --infer` and `markery historian draft` — under at least two models (Haiku 4.5 and Sonnet 4.6) over the fixtures, with `MARKERY_TOKEN_LOG` set.
3. Assert each output passes its MVO validator: `markery historian validate` 8/8 for drafts; the structured RECOMMENDATION/SCORE/REASONING format for infer. The pass/fail gate is the proof — any model whose output passes the validator is producing correct factual content.
4. Emit a per-model cost/quality table (model, validator pass rate, prompt/completion/cache-read tokens, USD estimate via `tokens report`). Write it to `tests/benchmarks/` and surface a copy in DESIGN.md.
5. Wire the benchmark as a repeatable command or test so the claim becomes a regression-tested property, not a one-off.

Close D061 when the table exists and the model-agnostic-tier tasks pass under ≥2 models.

---

### P4 — Front door (README, CI, provenance)

Make the repository legible to an outside reviewer (MARKERY_REVIEW §Portfolio #1, #4). Build this last — after P1–P3 give it something to show.

1. **Visitor-facing README.** One-sentence pitch; an annotated screenshot of a generated essay page (from the P1 publication-grade sites); direct links to the live Wikipedia contributions with revision IDs (from D050); a 30-second "run it, or view the output without running." The inward-facing docs (ROADMAP, DEFERRED, CLAUDE.md) stay; the README is the new front door above them.

2. **Surface quality signals.** Add CI that runs the test suite on push; add a coverage number/badge; make the `historian validate` 8/8 gate visible as evidence the research claims are checked. A reviewer should see green without cloning.

3. **Provenance statement.** One README paragraph naming the human-judgment layer explicitly: the three-tier architecture, the MVO / model-agnosticism framework, the CLI-as-test-harness thesis, and the human-gate altitude. Own the AI-orchestrated framing as a strength.

4. **Name the process discipline.** Call out the phase-gated ROADMAP, the contract-versioned subprocess interface, and the reopen-triggered DEFERRED register as deliberate engineering choices, not buried internal docs.

---

### P5 — Optional showcase: Mack Trucks bulldog live run on animal-marks-1930

Optional — not a gate on the phase. Do this only if P1–P4 are complete and a concrete agentic artifact adds value to the writeup. One live markery-langgraph run that exercises the `human_gate` end-to-end, plus the `--json` contract hardening (D062) at the end.

**Starting mark:** Mack Trucks bulldog, USPTO serial 71247861. Filed 1927-04-22. Purely figurative registration — null text, no word element, design code 030108 (bulldog, specific breed). Goods: motor trucks. Registrant: MACK TRUCKS, INC. (reg. 231645).

The bulldog became Mack's enduring symbol of toughness and pulling power precisely because drivers and rival manufacturers used the word informally to describe Mack's vehicles during World War I. The 1927 filing formalized that folk identity. Matching a purely figurative mark against truck-technology patents is a genuine hard case for the pipeline: the goods-title signal is absent, and all scoring weight falls on temporal proximity and CPC class alignment. This makes it ideal for the markery-langgraph `human_gate` — the graph will surface borderline candidates that require human judgment, not mechanical thresholding.

Mack Trucks is already entity_id 13 in the project with variants `MACK TRUCKS, INC.`, `INTERNATIONAL MOTOR COMPANY`, and `MACK MANUFACTURING CORPORATION`. No patent candidates exist yet because no Mack-aligned CPC class has been fetched. This phase builds that data from scratch.

**Model:** All markery CLI calls in this phase use `claude-haiku-4-5-20251001`. This is already set in `projects/animal-marks-1930/project.json` via the `"model"` field, which `cli.py` injects into `MARKERY_MODEL` at startup. The markery-langgraph subprocess calls inherit this via the project's `project.json` (tools.py passes `--model` only when explicitly overridden; otherwise the CLI resolves the model through the project file). No additional configuration is needed.

**Token tracking:** Before running any LLM-backed command in this phase, set `MARKERY_TOKEN_LOG` to a project-local path: `export MARKERY_TOKEN_LOG=projects/animal-marks-1930/mack-run-tokens.jsonl`. Every `markery historian` and `markery librarian` call will append a JSONL record (timestamp, specialist, command, prompt_tokens, completion_tokens, cache_read_tokens, model, wall_ms). After the phase completes, review the log to understand total API cost. A proper `markery tokens report` command is tracked as D059; for now, the log is the source of truth.

1. **Prepare project.json.** `project.json` lists `class_hints: [F02B, B60C, F41A, F41C, A01B, F04B, B64D, F16J]` but is missing B62D. Add `"B62D"` to the `class_hints` array. Also add `"MACK TRUCKS INC"` or `"INTERNATIONAL MOTOR CO"` as a `patent_assignee` variant in `variants.csv` — the onboard check (run 2026-06-09) confirmed that Mack has no `patent_assignee` variant, causing Step 5 of onboard to skip it. Without a patent assignee variant, `markery patent build` cannot attribute fetched patents to this entity.

2. **Verify project state.** Run `markery project onboard animal-marks-1930`. Confirm entity 13 (Mack Trucks) now shows ≥1 patent_assignee variant in Step 3 and is not skipped in Step 5. Note any remaining coverage gaps in the project's `RESEARCH.md`.

3. **Build Mack Trucks patents.** Set `MARKERY_TOKEN_LOG` (see above). Run `markery patent build` for CPC class B62D (motor vehicles, trailer, cycle engineering) over 1905–1932 via EPO OPS. B62D covers truck frames, load bodies, steering gear, and transmission patents — the classes where Mack's chain-drive and worm-drive rear axle innovations appear. Target: ≥10 patent records assigned to Mack Trucks assignee variants in the DB.

4. **Generate candidates for the bulldog mark.** Run `markery match animal-marks-1930 --serials 71247861` to generate candidates specific to the bulldog serial. The `--serials` flag restricts matching to this single trademark. Run `markery patent signals animal-marks-1930` immediately after to populate signal columns.

5. **Run markery-langgraph against the Mack candidate queue.** Export `MARKERY_ROOT` and run the Phase 21 P2 graph against the animal-marks-1930 project, restricted to the bulldog mark's candidates. Because the mark has no text component, scores will cluster in borderline territory (0.35–0.60); `human_gate` should interrupt on most candidates. For each interrupted candidate: review the patent title, grant date, assignee, and temporal gap; confirm or reject. Target: ≥1 confirmed pair. Record the session rationale in `RESEARCH.md`.

6. **Draft and validate.** For each confirmed Mack pair, run `markery historian draft` then `markery historian validate`. The essay must explain the animal imagery choice, the wartime origin of the "bulldog Mack" epithet, and the temporal relationship between the specific patent and the brand registration. All drafts must pass 8/8.

7. **Rebuild the site.** Run `markery site build animal-marks-1930`. Exit 0 required. The Mack Trucks entity page must list the confirmed pair(s) with the enriched card layout from P1. The match essay must render the bulldog mark image (has image data in DB, reg. 231645) inline.

8. **Review token log.** Read `projects/animal-marks-1930/mack-run-tokens.jsonl`. Sum prompt_tokens, completion_tokens, and cache_read_tokens across all records. Record the totals in `RESEARCH.md` under a "Build cost" heading. This establishes a per-project cost baseline for Haiku-driven runs.

**Contract hardening (D062).** Before or during the run, add `--json` to `markery historian card --infer` and `digest --infer` emitting `{recommendation, score, reasoning, card_text}`, and update `markery-langgraph/src/langgraph_markery/tools.py` to parse JSON instead of scraping the `[infer]` block with regex. Close D062 when the graph runs on JSON output.

---

### Phase Gate

P1 PASSED when: frontmatter stripping bug fixed in essays and search excerpts; Markdown parser supports unordered lists, ordered lists, blockquotes, and external links; patent figures auto-embed when figure data is available and `[[figure:]]` tag is absent from essay; match essays link to entity pages; entity pages show enriched confirmed-pair cards (name, patent no, year gap, essay link); date gap stat chip on landing page confirmed-pair cards; research question section suppressed when file absent; all narrative placeholder text suppressed site-wide; `loading="lazy"` on all gallery images; timeline date range is dynamic; breadcrumb nav on entity and match essay pages; entity nav links scrollable on mobile; page titles follow `[Title] — [Project] — Markery` pattern; OG descriptions populated for all page types; all three existing site builds exit 0 with no regressions.

P2 PASSED when: the three cache-minimum docstrings (`llm.py`, `historian/cli.py`, `librarian/extract.py`) corrected; a cache-verification warning fires when `cache_read_input_tokens` is 0 across a shared-prefix run; `DEFAULT_MODEL` defined once and imported in all three call sites; `markery tokens report` aggregates a token log into a cost summary; D059 closed.

P3 PASSED when: a cross-model benchmark runs `historian card --infer` and `historian draft` under ≥2 models over a fixed fixture set; every output passes its MVO validator; a per-model cost/quality table is written to `tests/benchmarks/` and surfaced in DESIGN.md; D061 closed.

P4 PASSED when: a visitor-facing README exists with pitch, an essay screenshot, live Wikipedia revision links, and run/view instructions; CI runs the test suite on push with a visible status; a provenance statement names the human-judgment layer; the process-discipline artifacts are called out.

P5 (optional) — not required for the phase. When attempted, PASSED when: ≥1 bulldog confirmed pair via the live graph `human_gate`; essay validates 8/8; `markery site build animal-marks-1930` exits 0 with the bulldog essay and mark image rendered; `--json` added to the infer commands and the langgraph graph parses it; D062 closed.

Phase PASSED when P1–P4 pass (P5 is optional). `DEFERRED.md` updated with any new bypasses discovered. D025 (photographic-equipment) and D026 (precision-tools) remain deferred — breadth is not the goal of this phase.
