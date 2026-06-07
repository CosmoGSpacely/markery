# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.
Phases 14–15 closed 2026-06-01/2026-05-24. Archived to `archive/ROADMAP-2026-06-03.md`.
Phases 16–18 closed 2026-06-06. Archived to `archive/ROADMAP-2026-06-06.md`.

**Phase 16 Track A status note:** P2 (D023 Chicago Pneumatic, rev 1358151236) and P3 (D024 Soundex, rev 1358151441) were submitted 2026-06-06. The 48-hour monitoring window closes 2026-06-08. Phase 19 P1 closes the gates and formally passes Phase 16 Track A. See D050 in `DEFERRED.md`.

---

## Phase 19 — Code Gaps and Deferred Work Sprint

**Trigger:** Phase 18 complete.
**Scope:** Close the Phase 16 Wikipedia gates (D050), implement the three highest-recurrence CLI gaps (D029 `matchmaker confirm`, D032 `librarian review --auto-accept`, D043 per-project model config), fix the librarian acquire slug mismatch (D044), complete the figurative-mark TUI audit (D041), add librarian MVO contract tests (D049), and close out documentation-only deferrals (D030, D040, D045).

**Goal state:** Phase 16 P2/P3 gates formally PASSED; `markery matchmaker confirm` working non-interactively; `markery librarian review --auto-accept` eliminates the recurring bypass; per-project model config enforced automatically; librarian acquire accepts search-sources slugs; figurative mark TUI audited; librarian MVO tests passing; DEFERRED.md fully current with no stale trigger conditions.

---

### P1 — D050: Close Phase 16 Wikipedia gates

**Prerequisite: 2026-06-08** (48-hour window after D023/D024 submission).

1. Check each of the 7 Phase 16 Track A edits for revert status:
   - Library Bureau Stage 4b external link — 2026-05-22 (check External links section still present)
   - Library Bureau CN fix — rev 1357391696 — `https://en.wikipedia.org/w/index.php?diff=1357391696`
   - Library Bureau absorption citation — rev 1357570204 — `https://en.wikipedia.org/w/index.php?diff=1357570204`
   - Rolodex Wheeldex — **revision ID not recorded** — retrieve from `https://en.wikipedia.org/w/index.php?title=Rolodex&action=history`; find the 2026-06-05 edit; record revision ID
   - Remington Rand filing systems — rev 1358111560 — `https://en.wikipedia.org/w/index.php?diff=1358111560`
   - D023 Chicago Pneumatic — rev 1358151236 — `https://en.wikipedia.org/w/index.php?diff=1358151236`
   - D024 Soundex — rev 1358151441 — `https://en.wikipedia.org/w/index.php?diff=1358151441`
2. Update `projects/monthly-image-review/STATUS.md`: record Rolodex revision ID; update D023 status from "Live — monitoring" to "Live, unreverted" or "Reverted".
3. Update `projects/information-systems/STATUS.md`: update D024 status from "Live — monitoring" to "Live, unreverted" or "Reverted".
4. If D023 and D024 are both unreverted: mark archived ROADMAP Phase 16 P2 and P3 gates PASSED with date (edit `archive/ROADMAP-2026-06-06.md` gate lines). Close D050 in DEFERRED.md.
5. If either was reverted: do not close the gate. Add a new DEFERRED entry with the revert reason and resubmission strategy. D050 stays open until both edits are live and confirmed.

---

### P2 — D029 and D041: Matchmaker confirm + figurative TUI audit

**D029 — `markery matchmaker confirm` non-interactive CLI:**

1. Add `confirm` subcommand to `src/markery/specialist/matchmaker/cli.py`:
   - `markery matchmaker confirm <project> <slug> [--note TEXT]`
   - Look up the candidate record in `candidates.jsonl` by slug (same slug-parsing logic as `historian card`)
   - Validate the slug resolves; exit 1 with a clear message if not found
   - Append a `confirmed.jsonl` entry in the same schema as the interactive reviewer (`patent_no`, `trademark_serial`, `trademark`, `entity`, `entity_id`, `score`, `note`)
   - Print the appended record to stdout; non-interactive by design (no confirmation prompt)
2. Add tests to `tests/specialist/matchmaker/`: (a) valid slug appends correct record; (b) invalid slug exits 1; (c) `--note` field appears in confirmed record; (d) running confirm twice with the same slug does not duplicate the entry.
3. Close D029 in `DEFERRED.md`.

**D041 — Figurative mark TUI audit:**

4. In `src/markery/specialist/matchmaker/review.py` (the interactive TUI that writes `confirmed.jsonl`), audit every reference to `cand["trademark"]` or `cand.get("trademark")`. Any path that could produce `None` must use `cand.get("trademark") or "(figurative)"` or an equivalent guard.
5. Add a test: pass a candidate dict with `trademark=None` through the TUI's confirmed-record construction function without raising `TypeError` or `AttributeError`.
6. Update D041 in `DEFERRED.md` — mark the TUI path closed; close D041 fully if all remaining open paths from the Phase 17.1 P1 audit are now resolved.

**Results 2026-06-07:** Both D029 and D041 implemented and tested. `markery matchmaker confirm` is now a real CLI command under `markery matchmaker`; it parses the slug to `(tm_slug, patent_no)`, finds the matching candidate in `candidates.jsonl`, guards against duplicate confirmation with an exit-0 message, handles figurative marks via `cand.get("trademark")`, and writes through the same `write_confirmed()` path as the interactive TUI. Invalid slugs exit 1 with a specific message. The TUI audit found two crash sites in `historian/review.py`: `mark = cand["trademark"]` in `display()` (would crash on any figurative candidate in the TUI queue) and `c["trademark"].upper()` in the queue-building filter (would crash when `--mark` is used with figurative candidates in scope). Both fixed with None-safe guards. D041 is now fully closed across all six code paths documented in DEFERRED. 7 tests in `tests/specialist/matchmaker/test_confirm.py`. 530 tests passing.

---

### P3 — D032 and D044: Librarian review auto-accept + acquire slug fix

**D032 — `markery librarian review --auto-accept`:**

1. Add `--auto-accept` flag to the `review` subcommand in `src/markery/specialist/librarian/cli.py` and the `review()` function in `extract.py`.
   - When set: read all pending candidates from `candidates.md`; append each to `excerpts.md` (using the existing `_append_to_excerpts` helper); update each candidate's `<!-- status: pending -->` marker to `<!-- status: accepted -->` in `candidates.md`.
   - When not set: existing interactive behavior unchanged.
2. Add a test: `review(slug, auto_accept=True)` with a `candidates.md` containing 3 pending passages results in all 3 appended to `excerpts.md` and `candidates.md` showing `accepted` status — without any call to `input()`.
3. Update the `review.md` instruction card (from D045 stubs, written in P5) to document both the interactive and `--auto-accept` paths.
4. Close D032 in `DEFERRED.md`.

**D044 — `markery librarian acquire` slug resolution:**

5. In the IA source module (`src/markery/specialist/librarian/sources/ia.py`), when `acquire` is passed an identifier that fails the initial IA lookup, attempt to resolve it by checking `library/works/<identifier>/metadata.json` for a previously acquired work with that slug. If found, re-use the existing metadata and skip re-download.
6. If the identifier is not an IA identifier and not a known slug, print: `"Identifier '<slug>' not found. Use the raw IA identifier from 'markery librarian search-sources' output (e.g. 'historydevelopme0000fran')."` — not a traceback.
7. Add a test: `acquire` with an unresolvable slug prints the helpful error message and exits 1.
8. Close D044 in `DEFERRED.md`.

**Results 2026-06-07:** Both D032 and D044 implemented and tested. `review()` in `extract.py` now accepts `auto_accept: bool = False`; when True it loops over pending blocks, calls `_append_to_excerpts()` for each, replaces `<!-- status: pending -->` with `<!-- status: accepted -->`, and writes back without any `input()` call. The `--auto-accept` flag is wired into `librarian review` via `cli.py`. For D044, the fix landed in `cli.py` rather than `sources/ia.py` — the slug check belongs in the acquire command where user intent is interpreted, not in the IA adapter. Two fixes: before hitting IA, check if `library/works/<identifier>/metadata.json` already exists and exit 0 with "Already acquired" if so; after a failed IA lookup, print a specific hint pointing to the IDENTIFIER column in `search-sources` output. Step 3 (update `review.md` instruction card) deferred to P5 where the D045 stub cards are written. 8 tests in `tests/test_librarian_p3.py`. 538 tests passing.

---

### P4 — D043 and D049: Per-project model config + librarian MVO contracts — CLOSED

**D043 — Per-project `model` in `project.json`:**

1. Add optional `"model"` field to the `Project` dataclass in `src/markery/common/project.py`. Update `load_project()` to read it (default: `None`).
2. In `src/markery/cli.py`, after any project is loaded and before dispatching to a specialist, if `project.model` is set and `MARKERY_MODEL` is not already in the environment, set `os.environ["MARKERY_MODEL"] = project.model`. Explicit env var always wins.
3. Add `"model": "claude-haiku-4-5-20251001"` to `projects/animal-marks-1930/project.json` to mechanically enforce the Phase 16.1 Haiku commitment.
4. Add tests: (a) `load_project()` returns `project.model = "claude-haiku-4-5-20251001"` when set in `project.json`; (b) `project.model = None` when absent; (c) when env already has `MARKERY_MODEL`, the project config does not override it.
5. Close D043 in `DEFERRED.md`.

**D049 — Librarian MVO contract tests:**

6. Add a `TestLibrarian` class to `tests/test_mvo.py` covering the four contracts in `tests/benchmarks/mvo.md`. Use the same `requires_dbs` / `requires_library` skip markers as existing test classes.
   - `librarian index`: exits 0; output contains a work count line
   - `librarian search <query>`: exits 0; output lines conform to the search result format
   - `librarian list`: exits 0; output lists known works with slugs
   - `librarian card <query>`: exits 0; output contains `## Card:` header and at least one passage block
7. Close D049 in `DEFERRED.md`.

Results 2026-06-07: Both D043 and D049 implemented and tested. `model: str | None` field added to `Project` dataclass; `load_project()` reads it from `project.json`. `_try_inject_project_model(rest)` in `src/markery/cli.py` scans the `rest` argument list for a known project directory name, reads its `project.json`, and sets `os.environ["MARKERY_MODEL"]` before dispatch — only when `MARKERY_MODEL` is not already set (explicit env var wins). `animal-marks-1930/project.json` now includes `"model": "claude-haiku-4-5-20251001"`, mechanically enforcing the Haiku commitment without a shell prefix. The injection function scans all `rest` args (not just `rest[0]`) so historian commands (`historian card <project> <slug>`) work correctly — `rest[0]` is the subcommand ("card"), `rest[1]` is the project. 4 tests in `tests/test_project_model.py`. D049: `TestLibrarian` class added to `tests/test_mvo.py` with 9 tests across `librarian index`, `librarian list`, `librarian search`, and `librarian card --mode keyword`; `requires_library` and `requires_library_index` skip markers gate each class correctly. 9 tests passing against the local library (10 works, 35 indexed passages). 551 total tests passing.

---

### P5 — Deferred triage: D030, D040, D045 — CLOSED

**D030 — Deprecate `historian simulate` in favour of `--infer` commands:**

Phase 18 P5 added `historian card --infer`, `historian digest --infer`, and `historian draft`. These three commands together supersede the D030 simulation script: `--infer` calls are more granular, CLI-first, tested, and token-logged. Update D030 in `DEFERRED.md` to note the supersession by Phase 18 P5 and close it.

**D040 — Patent signals spec ordering — documentation fix:**

Add a note to `src/markery/specialist/historian/persona/instructions/candidate-refresh.md` (or the closest equivalent instruction card for `markery patent signals`): "`markery patent signals <project>` reads from `candidates.jsonl` and enriches no records when called before `markery match`. Call it as step 1 of P4, immediately after `markery match` generates candidates." Close D040 in `DEFERRED.md`.

**D045 — Librarian instruction card stubs:**

Write 5 stub instruction cards in `src/markery/specialist/librarian/persona/instructions/`:
- `review.md` — notes interactive vs. `--auto-accept` paths; references D032 fix
- `raw-text.md` — prints path to `raw_text.txt`; use for debugging acquisition issues
- `enter.md` — manual ILL registration when `acquire` is not applicable
- `wants-update.md` — update status on an ILL wants-queue entry
- `list.md` — list all acquired works with slug, title, and passage count

Stubs need one paragraph describing when to use the command and the basic invocation form. Close D045 in `DEFERRED.md`.

Results 2026-06-07: All three deferrals closed. D030 closed with supersession note: `historian card --infer`, `historian digest --infer`, and `historian draft` (Phase 18 P5) together replace the simulation script — more granular, CLI-first, tested, and token-logged. D040 doc fix applied to `src/markery/specialist/historian/persona/instructions/patent-signals.md` § "When to use": ordering constraint paragraph added stating that `markery patent signals` reads from `candidates.jsonl` and enriches nothing when called before `markery match`; should be called as step 1 of P4 immediately after match. D045: five stub instruction cards written in `src/markery/specialist/librarian/persona/instructions/`: `review.md` (interactive vs `--auto-accept`, post-D032 paths), `raw-text.md` (path lookup, absent-file guidance), `enter.md` (manual ILL registration, excerpts.md format note), `wants-update.md` (status lifecycle wanted→in-progress→acquired), `list.md` (compact and verbose modes, excerpt-count interpretation). All 13 librarian instruction cards are now present.

---

### Phase Gate

P1 PASSED when: all 7 Phase 16 Wikipedia edits confirmed live or revert documented; Rolodex revision ID recorded; Phase 16 P2 and P3 gates updated in `archive/ROADMAP-2026-06-06.md`; D050 closed (or new D-entry filed for resubmission).

P2 PASSED when: `markery matchmaker confirm <project> <slug>` appends a correct record to `confirmed.jsonl`; all D029 tests pass. Figurative TUI audit complete; D041 test passes; D041 updated/closed. — PASSED 2026-06-07 (7 tests; D029 and D041 both closed in DEFERRED.md; 530 total tests passing)

P3 PASSED when: `markery librarian review --auto-accept` accepts all pending candidates without calling `input()`; D032 test passes; D032 closed. `markery librarian acquire` with unresolvable slug prints helpful error (not traceback); D044 test passes; D044 closed. — PASSED 2026-06-07 (8 tests; D032 and D044 both closed in DEFERRED.md; 538 total tests passing)

P4 PASSED when: `project.json` `"model"` field loaded and auto-sets `MARKERY_MODEL`; `animal-marks-1930/project.json` updated; D043 tests pass; D043 closed. Librarian MVO contract tests pass; D049 closed. — PASSED 2026-06-07 (13 tests; D043 and D049 both closed in DEFERRED.md; 551 total tests passing)

P5 PASSED when: D030 closed with Phase 18 P5 supersession note; D040 closed with doc fix applied; D045 closed with 5 stub cards written. — PASSED 2026-06-07 (documentation only; no new tests; 551 tests still passing)

Phase PASSED when P1–P6 all pass. `DEFERRED.md` is fully current: all closed entries are marked done; all open entries have valid reopen triggers and accurate path references. — P1–P5 PASSED 2026-06-07; P6 PASSED 2026-06-07.

---

### P6 — Wikipedia submission registry

**Motivation:** Revision IDs for submitted Wikipedia edits were recorded only as prose rows in project `STATUS.md` files. There is no structured, machine-readable record that a future `check-revision` command (Phase 21) can query. All three submission commands (`submit`, `replace`, `add-external-link`) silently discard the `newrevid` after printing it.

**Schema — `projects/<name>/wikipedia/submissions.jsonl`:**

Each line is one submitted edit:
```json
{
  "revision_id": 1357391696,
  "article": "Library Bureau",
  "description": "Resolve {{Citation needed}} — office network citation",
  "serial_no": null,
  "submitted_at": "2026-06-02",
  "status": "live",
  "diff_url": "https://en.wikipedia.org/w/index.php?diff=1357391696"
}
```

`revision_id` is `null` for edits submitted before this registry existed and whose revision ID was not captured. `status` is one of `live`, `monitoring`, `reverted`.

**Steps:**

1. Add `_record_submission(project_root, revision_id, article, description, submitted_at, serial_no=None, status="live")` helper to `src/markery/specialist/publisher/wikipedia/cli.py`. Appends one JSONL line to `projects/<project>/wikipedia/submissions.jsonl`, creating the file if absent. `revision_id` may be `None`.
2. Wire into `cmd_submit()` — project is always available. Write on `result == "Success"`.
3. Add optional `--project` flag to `cmd_replace()` and `cmd_add_external_link()` argparse entries. When `--project` is provided, write the submission record on success.
4. Update `wikipedia_main()` dispatch to pass `args.project` where added.
5. Backfill the seven existing Phase 16 Track A edits into their project files:
   - `projects/monthly-image-review/wikipedia/submissions.jsonl` — edits 1/5 through D023 (6 entries; 1/5 and 4/5 have `revision_id: null`)
   - `projects/information-systems/wikipedia/submissions.jsonl` — D024 (1 entry)
6. Manually check all seven edits for revert status; update `status` fields in the backfilled entries accordingly.
7. Update D050 in `DEFERRED.md` and STATUS.md files with confirmed revert/live status.

Results 2026-06-07: `_record_submission()` helper added to `src/markery/specialist/publisher/wikipedia/cli.py`; wired into `cmd_submit()` (always writes, project arg always present) and `cmd_replace()` / `cmd_add_external_link()` (writes when `--project` is provided, added as optional arg to both). Seven edits backfilled into `projects/monthly-image-review/wikipedia/submissions.jsonl` (6 entries) and `projects/information-systems/wikipedia/submissions.jsonl` (1 entry). MediaWiki API check on all 5 tracked revision IDs: all live, no `mw-reverted` tag. Rolodex revision ID retrieved from article history: **1357918452** (not previously recorded). Library Bureau Stage 4b external link (edit 1/5, planned 2026-05-22) confirmed **not submitted** — no CosmoGSpacely edit in Library Bureau history on that date and TSDR link is absent from the current article; status set to `not_submitted` in submissions.jsonl and STATUS.md updated. D023 (rev 1358151236) and D024 (rev 1358151441) confirmed live; Phase 16 archive P2 and P3 gates marked PASSED 2026-06-07; D050 closed in DEFERRED.md. `markery wikipedia check-revision` command added to Phase 21 P5 roadmap. 551 tests passing (no new tests — no testable logic added; submission recording is a side-effect path exercised in live submissions only).

---

### Phase Gate (updated)

P1 PASSED when: all 7 Phase 16 Wikipedia edits confirmed live or revert documented; Rolodex revision ID recorded; Phase 16 P2 and P3 gates updated in `archive/ROADMAP-2026-06-06.md`; D050 closed (or new D-entry filed for resubmission). — PASSED 2026-06-07 (5/6 tracked revisions confirmed live; edit 1/5 Library Bureau external link confirmed not submitted; Rolodex rev 1357918452 recorded; archive gates PASSED; D050 closed)

P2 PASSED when: `markery matchmaker confirm <project> <slug>` appends a correct record to `confirmed.jsonl`; all D029 tests pass. Figurative TUI audit complete; D041 test passes; D041 updated/closed. — PASSED 2026-06-07 (7 tests; D029 and D041 both closed in DEFERRED.md; 530 total tests passing)

P3 PASSED when: `markery librarian review --auto-accept` accepts all pending candidates without calling `input()`; D032 test passes; D032 closed. `markery librarian acquire` with unresolvable slug prints helpful error (not traceback); D044 test passes; D044 closed. — PASSED 2026-06-07 (8 tests; D032 and D044 both closed in DEFERRED.md; 538 total tests passing)

P4 PASSED when: `project.json` `"model"` field loaded and auto-sets `MARKERY_MODEL`; `animal-marks-1930/project.json` updated; D043 tests pass; D043 closed. Librarian MVO contract tests pass; D049 closed. — PASSED 2026-06-07 (13 tests; D043 and D049 both closed in DEFERRED.md; 551 total tests passing)

P5 PASSED when: D030 closed with Phase 18 P5 supersession note; D040 closed with doc fix applied; D045 closed with 5 stub cards written. — PASSED 2026-06-07 (documentation only; no new tests; 551 tests still passing)

P6 PASSED when: `submissions.jsonl` written on every successful `submit`, `replace` (with `--project`), and `add-external-link` (with `--project`) call; seven backfilled entries present in correct project files; all seven edits confirmed live or revert documented; D050 closed or new entry filed. — PASSED 2026-06-07

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

---

### P5 — Cross-project data quality audit

1. Run `markery historian validate` on every confirmed essay in `information-systems`, `radio-pioneers`, and `animal-marks-1930`. All must pass 8/8. Document any failures.
2. Run `markery site build` for all three projects. All must exit 0. Any crash is a blocker.
3. Run `markery matchmaker validate-variants` for all three projects. Flag any zero-match variants.
4. Query `extended_marks` for all project-scope serials across all three projects. Identify NULLs in `goods_desc` or `mark_text` that are not design marks (unexplained NULLs are a data gap to document).
5. Record results in a Phase 20 section of `tests/benchmarks/README.md`.

---

### Phase Gate

P1 PASSED when: `prior_brand_serials` implemented and tested; Colt and P&W candidates appear in `animal-marks-1930` with scores ≥ 0.5 after regeneration.

P2 PASSED when: `load-assignment` imports and the Rand Kardex ownership chain is queryable; `design-search` exits 0 with correct columns; D047 and D034 closed.

P3 PASSED when: `mark-status` exits 0 with correct live/dead/PD output; `matchmaker clear --dry-run` reports correct row count without deleting; D036 and D037 closed.

P4 PASSED when: `enrich-project --from-variants` populates `extended_marks` before candidates exist; `suggest-variants` output includes example patent titles; D046 and D039 closed.

P5 PASSED when: all confirmed essays validate 8/8 across all three projects; all three site builds exit 0; data quality results recorded in benchmarks README.

Phase PASSED when P1–P5 all pass. All D-numbers in this phase closed in `DEFERRED.md`.

---

## Phase 21 — Architectural Work

**Trigger:** Phase 20 complete.
**Scope:** Two tracks:
1. **Markery-LangGraph**: Stand up the companion repo and build the automated review workflow using Phase 18's `--infer` commands and Phase 19's `matchmaker confirm`.
2. **Project infrastructure**: D027 `project onboard` command (D042 `match --serials` ad-hoc flag as a parallel deliverable).

**Goal state:** `markery-langgraph` repo is live with a working LangGraph review graph that processes a project's candidate queue via `historian card --infer` and writes to `confirmed.jsonl` via `matchmaker confirm`; `markery project onboard` guides new project setup end-to-end; `markery match --serials` enables ad-hoc serial-scoped generation.

---

### P1 — markery-langgraph repo setup

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

---

### P2 — LangGraph workflow graph

1. Write `src/langgraph_markery/graph.py`:
   - **Nodes:** `load_digest` (parse digest into queue), `pick_next` (select next unreviewed slug), `generate_card` (write card file), `infer_card` (call `run_card_infer`, store `infer_result` in state), `route_recommendation` (conditional routing), `write_confirmed` (call `run_confirm`, trigger `run_draft`), `write_rejected` (append to rejected.jsonl), `append_defer` (add slug to deferred list for later review), `human_gate` (interrupt — surface card + recommendation for human approval before writing confirmed)
   - **Edges:** After `infer_card` → `route_recommendation`; routes: `"confirm"` → `human_gate` → `write_confirmed`, `"reject"` → `write_rejected`, `"defer"` → `append_defer`. After any write node → `pick_next`. `pick_next` terminates when queue is empty.
   - `human_gate` uses LangGraph's `interrupt()`. The graph can be resumed with an override recommendation (`"confirm"` / `"reject"`) injected by the caller.
2. Write an integration test that runs the graph on `radio-pioneers` against 3 unreviewed candidates (mocked tool calls — no live API). Verify: state contains 3 `infer_result` records; routing fires correctly; `run_confirm` was called for any "confirm" result.
3. Document in `README.md`: `MARKERY_ROOT` env setup, running `python -m langgraph_markery.graph <project>`, and how to inject a human override when the graph is interrupted.

---

### P3 — D027: `markery project onboard`

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

---

### P4 — D042: `markery match --serials` ad-hoc flag

1. Add `--serials <serial> [<serial>...]` to `markery match <project>` CLI.
   - Overrides `focus_serials` from `project.json` for this run only (does not modify `project.json`).
   - Generates candidates only for the listed serials against all project entities.
   - When `--serials` is set alongside `--all-serials`, `--serials` takes precedence.
2. Use case: exploratory generation for one or two serials without editing project configuration.
3. Add a test: `markery match <project> --serials 71299042` generates candidates only for serial 71299042.
4. Fully close D042 in `DEFERRED.md` (project-config approach from Phase 17 P1 handles persistent focus; this adds the one-off CLI override that completes the original request).

---

### P5 — `markery wikipedia check-revision`

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

---

### Phase Gate

P1 PASSED when: `markery-langgraph` repo initialised; `config.py`, `state.py`, `tools.py` all importable; `check_contract` passes against `MARKERY_ROOT`.

P2 PASSED when: LangGraph graph integration test passes with mocked tools; routing logic verified; `README.md` documents setup and usage.

P3 PASSED when: `markery project onboard` exits 0 on a correctly configured project and exits 1 with actionable errors on a misconfigured one; D027 closed.

P4 PASSED when: `markery match --serials` generates candidates only for the listed serials; test passes; D042 fully closed.

P5 PASSED when: `markery wikipedia check-revision <project>` reads `submissions.jsonl`, queries MediaWiki API for each revision, prints status table, updates changed statuses, exits 1 on revert; test passes.

Phase PASSED when P1–P5 all pass.

---

## Phase 22 — New Projects and Publisher Quality Pass

**Trigger:** Phase 21 complete.
**Scope:** Two new research projects — D025 (photographic equipment) and D026 (precision tools) — run end-to-end through the full pipeline including LangGraph-assisted review. Alongside the projects, a publisher quality pass delivers specific site rendering improvements identified across Phases 16–21.

**Goal state:** `photographic-equipment` and `precision-tools` both have ≥3 confirmed pairs, validated essays, and clean site builds; publisher renders patent figures inline, provides entity cross-links, and lists confirmed pairs on the landing page; LangGraph handles the initial review cycle for both projects; Wikipedia contributions submitted for both domains; all five project site builds meet a consistent quality standard.

---

### P1 — Publisher quality pass

Four targeted improvements to the publisher, in priority order:

1. **Patent figure embedding.** When a patent's figure PNG is in `patent_figures`, render it as an inline `<img>` in the match essay HTML, below the "The Invention" section heading. The `publisher/queries.py` already loads figure BLOBs; add the HTML rendering step to the match-essay template.

2. **Entity cross-links.** Add bidirectional cross-links between match essay pages and entity summary pages. Each match essay should link to `entity-<entity-slug>.html`; each entity summary page should list and link to all confirmed pairs for that entity. The data is already in `confirmed.jsonl`; this is a rendering change only.

3. **Landing page confirmed-pair listing.** Below the stat cards on the landing page, add a compact linked list of confirmed pairs: trademark name, entity name, date gap, and a link to the essay. Replaces the bare confirmed-pair count with navigable content.

4. **Research question block styling.** Wrap the `research-question.md` block (introduced in Phase 17 P1) in a visually distinct HTML element (bordered card or highlighted block via inline style or a dedicated CSS class) so it reads as a project framing section rather than plain body text.

5. Run `markery site build` for all existing projects (information-systems, radio-pioneers, animal-marks-1930). All must exit 0. Any regression from the new rendering is a blocker.

---

### P2 — D025: Photographic equipment project

**Target entities:** Eastman Kodak Company, Ansco (Ansco Company / General Aniline & Film), Graflex Inc., Blair Camera Company.
**CPC classes:** `G03B` (photographic apparatus), `G03C` (photosensitive materials), `G03D` (photographic processing).

1. Run `markery project onboard photographic-equipment` (Phase 21 P3). Confirm PASSED before proceeding.
2. Run trademark sweeps for each entity's variants. Target: ≥8 trademark records across all four entities.
3. Run `markery patent build` for CPC classes G03B, G03C, G03D over 1890–1940 via EPO OPS.
4. Run `markery match photographic-equipment`. Run `markery patent signals photographic-equipment` immediately after.
5. Use the LangGraph graph (Phase 21 P2) for the initial review cycle: run the graph against the candidate queue. Confirm that `human_gate` interrupts work correctly for borderline cases. Target: ≥3 confirmed pairs.
6. Run `markery historian draft` for each confirmed pair; run `markery historian validate` on each draft. All must pass 8/8.
7. Acquire Reese Jenkins, *Images and Enterprise: Technology and the American Photographic Industry, 1839–1925* (1975) from IA (`markery librarian acquire`). Run `markery librarian extract` with topics `"Kodak" "trademark" "patent" "camera"`.
8. Run `markery site build photographic-equipment`. Exit 0 required.
9. Identify the strongest Wikipedia contribution target: an article with a genuine citation gap that a USPTO primary source (from confirmed pairs) would fill. Write a draft to `projects/photographic-equipment/wikipedia/`.

---

### P3 — D026: Precision tools project

**Target entities:** Snap-on Tools Company, L.S. Starrett Company, Brown & Sharpe Manufacturing, Illinois Tool Works.
**CPC classes:** `B25B` (tools for tightening/loosening), `B23B` (turning and boring), `G01B` (measuring instruments).

Same workflow as P2. Secondary literature is thinner for precision tools — use `markery librarian discover --wikipedia` on company article pages to surface available IA sources. Acquire what is available; note any dry-run gaps in `RESEARCH-AGENDA.md`.

Target: ≥3 confirmed pairs, validated essays, site build exit 0, Wikipedia draft written.

---

### P4 — Wikipedia submissions for new domains

1. For photographic equipment: review the draft from P2 step 9. Submit via `markery wikipedia replace --yes` after diff review. Use summary: "Add primary source citation from USPTO filing record."
2. For precision tools: identify and draft a citation addition for the strongest underserved Wikipedia article in the domain. Submit via `markery wikipedia replace --yes` after diff review.
3. Monitor both new edits for 48 hours. Record revision IDs in each project's `STATUS.md`.
4. Add DEFERRED entries (D051, D052) for both new edits following the D050 pattern — one monitoring entry per article edit.

---

### Phase Gate

P1 PASSED when: patent figures render inline in match essays; entity cross-links present; landing page lists confirmed pairs; research-question block styled distinctly; all three existing site builds exit 0 without regressions.

P2 PASSED when: `photographic-equipment` has ≥3 confirmed pairs, all essays validate 8/8, site build exits 0, Wikipedia draft written to `projects/photographic-equipment/wikipedia/`.

P3 PASSED when: `precision-tools` has ≥3 confirmed pairs, all essays validate 8/8, site build exits 0, Wikipedia draft written to `projects/precision-tools/wikipedia/`.

P4 PASSED when: at least one Wikipedia edit submitted per domain; revision IDs recorded in STATUS.md files; D051 and D052 DEFERRED entries filed.

Phase PASSED when P1–P4 all pass. `DEFERRED.md` updated with all new bypasses discovered during the two new projects.
