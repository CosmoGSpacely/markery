# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.

---

## Phase 14 — Efficiency Baseline: Token and Model Benchmarking — CLOSED

**Opened:** 2026-05-24  
**Trigger:** Phase 13 complete — v0.3.0 tagged, public readiness achieved.  
**Scope:** Measure Markery's current token consumption and model sensitivity across real workflows, then reduce both enough that the gallery-exploration and card/digest historian workflows are completable end-to-end on a free cloud model. This phase closes the gap between the model-agnosticism principle documented in DESIGN.md and the reality of how sessions are run in practice.

**Goal state:** By phase close, the gallery-exploration and card/digest historian workflows complete end-to-end on a free-tier model (Claude Haiku or equivalent) without exceeding its context window or producing hallucinated structured data. Match-review-essay workflows may remain paid-model-preferred.

---

### P1 — Token instrumentation — CLOSED

Add per-command token measurement so every API call is observable without external tooling.

1. Add a `TokenRecord` datatype (model, prompt_tokens, completion_tokens, cache_read_tokens, cache_creation_tokens, wall_ms) to `common/tokens.py`
2. Add `MARKERY_TOKEN_LOG` env-var support: when set to a file path, each API call appends a JSON line to that file (timestamp, specialist, command, TokenRecord)
3. Add `--tokens` flag to the CLI dispatcher: when present, print a summary line to stderr after any command that calls the API (e.g., `[tokens] prompt=1,234 completion=456 cache_read=0 (haiku-4-5)`)
4. Verify: run `markery historian card soundex-us1261167a --tokens` and confirm token counts appear in output

---

### P2 — Baseline sweep — CLOSED

Run the standard session workflow on `information-systems` and record the token profile as the baseline.

1. Set `MARKERY_TOKEN_LOG=tests/benchmarks/baseline-2026-05-24.jsonl` and run the full session sequence:
   - `markery historian digest information-systems`
   - `markery historian card <slug>` for each unreviewed candidate
   - `markery historian scaffold <slug>` for one confirmed pair
   - `markery historian validate <slug>` against the resulting essay
2. Aggregate by command: mean prompt tokens, mean completion tokens, total tokens for the session
3. Record results in `tests/benchmarks/README.md`: baseline table, date, model, session description
4. Identify the top 3 token-cost hotspots (expected candidates: persona system prompts, full candidates.jsonl payload, goods-description fields in candidate blocks)

---

### P3 — Hotspot reductions — CLOSED

For each hotspot identified in P2, design and apply a targeted reduction. Measure the delta after each change.

**Expected hotspot candidates and candidate mitigations:**

| Hotspot | Candidate mitigation |
|---|---|
| Persona system prompt size | Audit each identity.md for redundancy; extract verbose reference sections to separate files loaded only when the relevant command runs |
| Full candidates.jsonl in context | Pass only the top-N candidates by score (configurable, default 20) to any command that enumerates candidates; `digest` already does this but `card` and `scaffold` may not |
| Goods-description verbosity | Truncate statement_text to 150 chars in card and digest output (truncation already applied in card but may not be in digest or scaffold context blocks) |

1. For each hotspot: describe the reduction, implement it, re-run the affected commands with `--tokens`, record the new count
2. Target: ≥ 20% reduction in prompt tokens for the session as a whole vs the baseline
3. No regression in output quality: run `markery historian validate` on essays produced pre- and post-reduction and confirm all-PASS

---

### P4 — Free-model run — CLOSED

Validate that the reduced workflows are completable on a free-tier model.

**Target models:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) as the primary target. Secondary: Gemini Flash or Mistral free tier if Haiku is insufficient.

1. Gallery-exploration workflow: run a full `monthly-image-review` session (select marks, run `markery enhance gallery`, draft a Wikipedia submission via `markery wikipedia from-essay`) with the model set to Haiku
2. Card/digest historian workflow: run `digest` + `card` for three candidates on `information-systems` with Haiku; verify output is structurally valid (serial numbers match DB, no invented candidates)
3. Record token counts for both runs; compare to P2 baseline
4. Define "passes" criteria explicitly:
   - No hallucinated serial numbers or patent numbers (check against DB)
   - Output passes `markery historian validate` or is parseable without human correction
   - Context window not exceeded (no truncation warnings from the model)
5. If Haiku fails on match-review-essay workflow, document the failure mode and note the minimum model tier required

---

### P5 — MVO contracts — CLOSED

Formalize the minimum viable output definition per command so free-model results are testable without human review.

1. Write `tests/benchmarks/mvo.md`: one table row per API-calling command with: command, expected output fields, validation rule (regex, schema check, or DB lookup)
2. Implement `tests/test_mvo.py`: for each command with a defined MVO contract, run the command against a known fixture and check output programmatically
3. Add MVO tests to the CI matrix (separate job so they don't run on every push — only on `workflow_dispatch` or tags)
4. Verify: all MVO tests pass with the primary paid model; note which pass with Haiku

---

### Phase Gate

P1 PASSED when: `--tokens` flag produces accurate token counts on any API-calling command; `MARKERY_TOKEN_LOG` appends valid JSON lines; confirmed against an actual API response. — PASSED

P2 PASSED when: baseline sweep is complete, `tests/benchmarks/README.md` has a populated baseline table, and the top 3 hotspots are named. — PASSED (2,122-token baseline; 3 hotspots identified in tests/benchmarks/README.md)

P3 PASSED when: session-level prompt tokens are ≥ 20% below the P2 baseline; `markery historian validate` passes on essays produced post-reduction. — PASSED (22.3% reduction, 1,648 vs 2,122 tokens; validate all-PASS)

P4 PASSED when: gallery-exploration and card/digest historian workflows complete end-to-end on Haiku without hallucinated structured data or context-window overflow; results recorded in `tests/benchmarks/README.md`. — PASSED (both workflows PASS; max 1.5% of 200K context window; hallucination check PASS on all runs)

P5 PASSED when: all MVO tests pass with the primary paid model; `tests/benchmarks/mvo.md` is complete. — PASSED (55/55 tests pass; mvo.md written; mvo CI job added to ci.yml under workflow_dispatch)

Phase PASSED when P1–P5 all pass. — PASSED 2026-05-24

---

## Phase 15 — LIBRARIAN Specialist: Cross-Project Reference Retrieval

**Trigger:** Phase 14 complete — v0.3.0 public, token benchmarks established.  
**Scope:** Build the sixth specialist. LIBRARIAN owns a shared `library/` directory at repo root, indexes secondary literature across all projects, and gives the historian a searchable reference corpus rather than isolated per-project stubs.

**Goal state:** By phase close, `markery librarian search <query>` returns annotated passages from indexed works; at least three works with real excerpts are in `library/`; the historian can load a compact context card from the library into any session; D020 is closed.

**D020 blocking condition status (at phase open):**
- Condition 1 (format proven across two projects): NOT MET — `information-systems/references/` has three files but passage sections are all stubs. `monthly-image-review` has no `references/` directory. Phase opens by meeting these conditions in P1.
- Condition 2 (concrete cross-project retrieval need): NOT MET — no second project holds references. Phase opens by establishing it in P1.

---

### P1 — Prove blocking conditions

Satisfy D020 conditions before writing a line of specialist code.

1. Populate real excerpts in `information-systems/references/` for at least two works (Yates and Cortada are the natural first choices — both have IA-borrowable copies). Each passage block must have a verbatim quotation and a context note. Stub `<!-- Add passage -->` comments do not count.
2. Create `projects/monthly-image-review/references/` with at least one work relevant to that project's scope (industrial design mark history, pneumatic tool industry, or American manufacturing branding in the 1920s–1930s). Follow the same format established in `information-systems/references/README.md`.
3. In `projects/monthly-image-review/references/README.md`, document one concrete example of a passage in `information-systems/references/` that the `monthly-image-review` historian would benefit from — establishing that cross-project access is the real need, not just copying files.
4. Verify: both directories have at least one work with real (non-stub) passage sections.

---

### P2 — Library structure

Move from per-project stubs to a shared, schema-defined corpus.

1. Create `library/` at repo root with:
   - `library/works/<author-slug>/metadata.json` (author, title, year, publisher, isbn, ia_identifier, ia_access)
   - `library/works/<author-slug>/excerpts.md` (annotated passages — same format as current `references/` files, minus per-project bias)
   - `library/works/<author-slug>/index.md` (topic index: one line per passage heading with a short description)
   - `library/README.md` (schema documentation and sourcing guidelines)
2. Migrate the three `information-systems/references/` works (Yates, Cortada, Austrian/Hollerith) into `library/works/`. Carry forward all curated excerpts; do not lose passage content.
3. Update `information-systems/references/` files to citation-only stubs — each file becomes a pointer (`see: library/works/<slug>`) rather than a content holder. Update `references/README.md` to describe the per-project citation convention.
4. Migrate `monthly-image-review/references/` work(s) into `library/works/` on the same basis.
5. Verify: `library/` contains at least three works; `projects/*/references/` contain only citation stubs; no passage content lives outside `library/`.

---

### P3 — LIBRARIAN persona and specialist scaffold

1. Create `src/markery/specialist/librarian/` with: `__init__.py`, `cli.py`, `persona/identity.md`, `persona/instructions/` (empty for now).
2. Write `identity.md`: LIBRARIAN's scope is `library/` (owns it, writes to it) and `projects/*/references/` (reads citation stubs). It does not touch DuckDB, candidates, or confirmed records. It writes `library/` and `library/index.jsonl`.
3. Register `markery librarian` in the top-level CLI dispatcher (`src/markery/cli.py` or equivalent entry point).
4. Verify: `markery librarian --help` shows registered subcommands.

---

### P4 — Index build and keyword search

1. Implement `markery librarian index`: reads all `library/works/*/excerpts.md` files; extracts passage blocks (section heading + passage text + optional context note); writes `library/index.jsonl` (one record per passage: `work_slug`, `author`, `title`, `year`, `section`, `passage`, `context`).
2. Implement `markery librarian search <query> [--top N]`: loads `library/index.jsonl`; case-insensitive substring match across `passage` + `section` + `context` text; returns top N matches (default 5) with work citation and passage context.
3. Implement `markery librarian list`: prints one line per work (slug, author short, year, excerpt count) and a total.
4. Add `--tokens` flag to `search` and `list` via existing `tokens.py` infrastructure.
5. Verify: `markery librarian search "card index"` returns at least one passage from Cortada or Yates.

---

### P5 — Historian context card

1. Implement `markery librarian card <query> [--top N]`: produces a compact context block (target ≤300 tokens) suitable for pasting into a historian session. Format: one record per match with `[Work, Year] Section heading — passage text (p. XX).`
2. Add `--out -` flag (stdout) and default file output to `library/cards/<query-slug>.md` for persistence across sessions.
3. Add `--tokens` flag.
4. MVO contract: card output must contain at least one `[` citation marker and the word count of each passage must be preserved exactly (no truncation of excerpts mid-sentence).

---

### P6 — Tests, MVO contracts, and D020 close

1. Write `tests/test_librarian.py` covering: `index` builds `library/index.jsonl` with expected record structure; `search` returns matches for a known query; `list` enumerates works; `card` produces a compact output with citation markers. Use `tmp_path` fixtures with minimal library content — do not depend on the live `library/`.
2. Add LIBRARIAN to `tests/benchmarks/mvo.md`: one table per command (`index`, `search`, `list`, `card`) with field and exit-code contracts.
3. All tests pass.
4. Mark D020 resolved in `DEFERRED.md`.

---

### Phase Gate

P1 PASSED when: two projects have `references/` with real (non-stub) excerpts; cross-project need is documented.

P2 PASSED when: `library/` exists with at least three works migrated; per-project `references/` are citation stubs only.

P3 PASSED when: `markery librarian --help` shows subcommands; `identity.md` written with correct scope.

P4 PASSED when: `markery librarian search "card index"` returns at least one real passage; `index.jsonl` exists and is valid JSON-L.

P5 PASSED when: `markery librarian card <query>` produces output ≤300 tokens with citation markers.

P6 PASSED when: all MVO tests pass; D020 closed in `DEFERRED.md`.

Phase PASSED when P1–P6 all pass.

---

## Phase 16 — PatentsView Bulk Import and Wikipedia Stage 4

**Trigger:** Phase 15 complete — LIBRARIAN operational; OR a project with 1976+ scope opens where EPO OPS quota is a genuine bottleneck (for D007 sub-track only).  
**Scope:** Three deferred items from distinct workstreams — patent data infrastructure (D007), Wikipedia inline citation (D023), and Wikipedia second article (D024) — all mature enough to close in the same phase. D007 and D023/D024 are independent and can proceed in parallel.

**Goal state:** By phase close, `markery patent bulk-import` is implemented and tested; the Chicago Pneumatic Wikipedia citation is live; a second Wikipedia article is enriched; D007, D023, and D024 are all closed.

---

### P1 — PatentsView bulk import (D007)

Full design is in `src/markery/specialist/patent/BULK_CSV.md`. Implement as specified there.

1. Implement `markery patent bulk-import download --year-start YEAR --year-end YEAR --out-dir PATH`: downloads the required PatentsView `.tsv.gz` files (`g_patent`, `g_assignee_disambiguated`, `g_cpc_current`) for the specified year range. Files are large; command must show progress and resume safely if interrupted.
2. Implement `markery patent bulk-import load --tsv-dir PATH --classes CPC [CPC ...] [--year-start YEAR] [--year-end YEAR]`: reads the `.tsv.gz` files with DuckDB `read_csv()` and predicate pushdown; constructs `patent_no` as `US{number}{kind}`; inserts into `patents` and `patent_classes` tables using insert-if-not-exists (idempotent against the existing EPO-sourced schema).
3. Verify schema compatibility: bulk-imported rows must pass the same queries that EPO-sourced rows pass. `app_dt` will be NULL for bulk-imported rows — document this in `BULK_CSV.md` and confirm no existing query hard-requires it.
4. Test against a narrow scope: one CPC class (`B42F`), year range 1976–1985. Confirm row counts match manual PatentsView query. Confirm no duplicate `patent_no` collisions with EPO-sourced rows in that range.
5. Add `markery patent bulk-import status --tsv-dir PATH`: reports row counts in the `.tsv.gz` files before load (sanity check before committing to a multi-hour import).

---

### P2 — Soundex owner attribution research (D024 prerequisite)

D024 requires resolving who filed the 1927 SOUNDEX trademark before any Wikipedia edit attributes it to a specific entity.

1. Query `trademarks.duckdb` for the SOUNDEX filing: serial number, filing date, owner on file, any assignment records. The SOUNDEX serial is in `information-systems/matches/confirmed.jsonl`.
2. Cross-reference: the Remington-Rand merger closed June 1927. The SOUNDEX filing date relative to that merger date determines whether the filer was Rand Kardex Corporation, Remington Rand Inc., or a predecessor.
3. Check `assignment` table (if populated) for any ownership transfer on the SOUNDEX serial.
4. Document the finding in `projects/information-systems/RESEARCH.md` under a new "SOUNDEX ownership timeline" section. State explicitly: (a) who the filing-date owner was, (b) whether the merger predated or postdated the filing, (c) which entity name is safe to use in a Wikipedia edit.
5. Gate: do not proceed to P4 until this question is resolved with DB evidence.

---

### P3 — Wikipedia Stage 4c: Chicago Pneumatic inline citation (D023)

D023 blocking conditions: Stage 4b (external link) live ≥48 hours unreverted; account has ≥5 confirmed non-reverted mainspace edits. Verify both before proceeding.

1. Confirm the Stage 4b external link is still live on the Chicago Pneumatic Tool Company article.
2. Confirm account edit count ≥5 non-reverted mainspace edits.
3. Identify the exact insertion point: the History section paragraph covering the 1920s–1930s branding period.
4. Draft the sentence per D023 specification: "The CP monogram design trademark (USPTO Serial No. 71299042) was filed on April 18, 1930, covering pneumatic tools, air compressors, and related apparatus." Add a `<ref>` tag citing the TSDR filing record URL.
5. Use `markery wikipedia` tooling to read-modify-write: fetch current article, insert sentence, generate diff, confirm before submitting.
6. Verify: confirm the edit is live; monitor for 48 hours; note any reviewer response.

---

### P4 — Wikipedia Stage 4d: second article (D024)

Depends on P2 (attribution resolved) and P3 (Stage 4c live ≥48 hours unreverted).

1. Based on P2 research, choose the target article: Soundex (if attribution is clean and the patent-trademark angle is clearly addable) or Remington Rand (if the product-line angle — SOUNDEX, VARIADEX, KARDEX — fits the article's existing structure).
2. Identify the specific section and sentence to add or enrich. Use `markery wikipedia from-essay` to generate a wikitext draft from the relevant confirmed-pair essay as a starting point; edit manually to meet Wikipedia's NPOV and citation standards.
3. Read-modify-write with diff review and explicit confirmation before submitting. Do not submit more than one paragraph of new content in a single edit.
4. Verify: confirm the edit is live; document the edit summary and timestamp in `projects/information-systems/STATUS.md`.

---

### P5 — Tests, cleanup, and gate

1. Add `markery patent bulk-import` to `tests/benchmarks/mvo.md`: contract for `status` command (prints row counts, exits 0) and `load` command (idempotent on re-run — no duplicate rows inserted on second load of same data).
2. Write `tests/test_bulk_import.py`: test `status` against a fixture `.tsv.gz` (synthetic, 10-row subset); test `load` inserts expected rows and is idempotent. No real PatentsView download required in tests.
3. Mark D007 resolved in `DEFERRED.md` with a note on the test scope and any `app_dt`-NULL constraint.
4. Mark D023 resolved in `DEFERRED.md` with the Wikipedia edit URL and timestamp.
5. Mark D024 resolved in `DEFERRED.md` with the Wikipedia edit URL and the attribution finding from P2.

---

### Phase Gate

P1 PASSED when: `markery patent bulk-import load` runs without error on B42F/1976–1985; row counts match PatentsView; no duplicate collisions with EPO-sourced rows.

P2 PASSED when: SOUNDEX owner attribution is documented in `RESEARCH.md` with DB evidence; a safe entity name for Wikipedia is identified.

P3 PASSED when: Chicago Pneumatic inline citation is live on Wikipedia ≥48 hours unreverted.

P4 PASSED when: second article contribution is live; edit summary recorded in `STATUS.md`.

P5 PASSED when: bulk-import MVO tests pass; D007, D023, D024 all marked resolved in `DEFERRED.md`.

Phase PASSED when P1–P5 all pass.
