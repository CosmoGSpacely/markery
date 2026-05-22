# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phase 8 — Specialist Completeness — CLOSED 2026-05-20. Archived to `archive/SPECIALIST-REVIEW-2026-05-20.md`.

---

## Phase 9 — Tool Generalization: Image Enhancement & Wikipedia

**Opened:** 2026-05-20  
**Scope:** Two publisher-owned tools currently constrained to specific workflows. Goal: both usable from any project without restriction.

---

### Current State — Image Enhancement

The image enhancement pipeline lives in `src/markery/specialist/publisher/image_enhancement/` and exposes three CLI subcommands under `markery enhance`:

| Subcommand | Function | Status |
|---|---|---|
| `gallery` | Build self-contained HTML gallery from DB images or enhanced PNGs | **Working** — no optional deps required |
| `enhance` | Upscale one mark 4× with Real-ESRGAN, optionally vectorize to SVG | **Broken** — pipeline import fails; see below |
| `batch` | Enhance all marks matching a SQL WHERE clause | **Broken** — same root cause |

**Module dependency map:**

```
markery enhance enhance / batch
  → image_enhancement/cli.py  (fixed: lazy-imports pipeline)
    → image_enhancement/pipeline.py
        → binarize.py   imports cv2 (✅ installed), vtracer (❌ not installed)
        → upscale.py    imports cv2 (✅), numpy (✅); realesrgan inside fn body (❌ not installed)
```

`gallery` does not touch pipeline.py. The lazy-import fix in cli.py and `__init__.py` (2026-05-20) means `gallery` is completely isolated from optional deps.

**Blocking layers:**

1. **vtracer** — not installed. Single package, no transitive deps (`pip install vtracer`). Blocks `binarize.py` import, which blocks `pipeline.py`, which blocks both `enhance` and `batch`. Fix is trivial.

2. **realesrgan** — not installed. Heavy ML chain: pulls in PyTorch, torchvision, basicsr, facexlib, gfpgan, scipy, scikit-image (~1–2 GB installed). realesrgan's own imports are deferred to the `upscale()` function body, so once vtracer is installed the pipeline *imports* cleanly — but calling `upscale()` fails at runtime.

**What happens after installing only vtracer:**
- `pipeline.py` imports successfully
- `binarize.threshold()` and `binarize.vectorize()` work (cv2 + vtracer path)
- `upscale.upscale()` raises ImportError on first call (realesrgan/basicsr absent)
- Result: `enhance` and `batch` fail with a runtime error rather than an import error — better, but still broken

**Current workaround:** manual Pillow LANCZOS 4× upscale (used for the Chicago Pneumatic test, 2026-05-20). Produces acceptable output for historical scans; no SVG vectorization.

---

### Options — Image Enhancement

**Option A — Graceful Pillow fallback (recommended)**  
In `upscale.py`, wrap the realesrgan import in a try/except. If realesrgan is absent, fall back to Pillow LANCZOS 4×. Log or print a one-line notice. The pipeline then runs end-to-end with no ML stack required. SVG vectorization still works (binarize path is independent of upscaling). The `model_used` field in MarkResult reports `"lanczos-fallback"` instead of `"x4plus-anime"`. The full Real-ESRGAN path is activated automatically whenever realesrgan is installed.

Trade-off: Lanczos output is visibly softer than Real-ESRGAN on historical scans, but fully usable for gallery, essay illustration, and Wikipedia upload. Any project can run `enhance` without the ML stack.

**Option B — Separate lightweight optional group**  
Split pyproject.toml `[enhance]` into `[enhance-light]` (opencv + vtracer) and `[enhance-full]` (adds realesrgan). Document the tiers. No code change to the pipeline — `enhance` still fails without the full stack.

Trade-off: cleaner dependency communication but does not solve the usability problem. Projects still cannot run `enhance` without committing to the ML install.

**Option C — Full ML stack install**  
`pip install -e ".[enhance]"` installs realesrgan, which pulls in PyTorch. On a GPU machine this is the highest-quality path. On CPU it runs but is slow (~30–120s per image depending on size). Model weights are downloaded on first use (~64 MB for x4plus-anime).

Trade-off: only viable on machines where ~2 GB of ML deps and weight downloads are acceptable. Not appropriate as the default for a research CLI.

---

### Options — Wikipedia

The Wikipedia tooling lives in `src/markery/specialist/publisher/wikipedia/` and exposes two CLI subcommands:

| Subcommand | Function | Status |
|---|---|---|
| `draft` | Generate wikitext from a confirmed match record and its essay | **Working but restricted** — requires confirmed.jsonl entry with `patent_no`, `grant_dt`, `entity`, `essay_path` |
| `submit` | Show diff and POST to Wikipedia API | Working but restricted by same requirement |

**Current `draft` command contract:**

```
markery wikipedia draft <project> <slug>
```

Reads `projects/<project>/matches/confirmed.jsonl`, finds the entry whose `slug` matches, then calls `build_draft_wikitext()` which requires:

- `trademark` — mark name
- `patent_no` — US patent number (patent-trademark pair specific)
- `trademark_serial` — USPTO serial number
- `entity` — canonical entity name
- `filing_dt` / `grant_dt` — dates
- `essay_path` — path to historian's markdown essay

**What this excludes:**

- Standalone trademark research (no patent pair): e.g., the Chicago Pneumatic CP mark (serial 71299042) — has an essay and a serial but no patent match
- Gallery-driven research: marks surfaced through `monthly-image-review` that warrant Wikipedia coverage but are not in any project's `confirmed.jsonl`
- Any future project type that does not use the patent-trademark confirmation pipeline
- `markdown_to_wikitext()` is standalone and project-neutral, but there is no CLI path to reach it without a confirmed pair

**What `build_draft_wikitext()` produces that is pair-specific:**
The patent citation ref (`{{US patent|<no>}}`), the `[[Category:United States patents]]` tag, and the `assignee: <entity>` attribution in the sources section. Everything else (body conversion, trademark ref, sources section) is generalizable.

---

### Options — Wikipedia

**Option A — Add `from-essay` subcommand (recommended)**  
New command: `markery wikipedia from-essay <essay_path> --out <path> [--title <title>] [--serial <serial>] [--categories <cat>...]`  
Calls `markdown_to_wikitext()` directly, appends a minimal sources section (TSDR ref if serial is provided, no patent ref), writes wikitext to the specified output path. Does not require `confirmed.jsonl` or a project directory. Works for any research context.

Trade-off: adds a second entry point for Wikipedia drafting. The `draft` command (patent-trademark pair path) stays unchanged; `from-essay` is additive.

**Option B — Optional fields in `draft`**  
Make `patent_no` and `grant_dt` optional in `build_draft_wikitext()`. When absent, omit the patent citation ref and patent category. The `draft` command already reads from confirmed.jsonl; extend it to also accept `--essay <path>` to bypass the confirmed.jsonl lookup entirely.

Trade-off: less clean interface (one command doing two jobs), but fewer commands for users to learn. The confirmed.jsonl lookup path and the essay-path path share the same subcommand.

**Option C — Project-level wikipedia directory convention**  
Add a `wikipedia` property to the `Project` class. Extend `markery wikipedia draft` to accept a project name and any essay slug present in `projects/<project>/essays/` rather than only slugs in `confirmed.jsonl`. This keeps the project-centric model but removes the patent-pair requirement.

Trade-off: still requires the essay to live inside a known project directory. Does not help for ad-hoc use outside a project.

---

### Work Plan

**P1 — Image enhancement: install vtracer, add Lanczos fallback — CLOSED**

1. Install vtracer into the project venv: `pip install vtracer`
2. In `upscale.py`, wrap the realesrgan/basicsr imports in a try/except inside `upscale()`. On ImportError, log a notice and return `img.resize((w*4, h*4), Image.LANCZOS)`.
3. Update `MarkResult.model_used` convention: `"x4plus-anime"` when Real-ESRGAN ran, `"lanczos-fallback"` otherwise.
4. Update `pyproject.toml`: add `vtracer` to `[enhance]` optional group (it is a required dep for the pipeline to import, not optional).
5. Verify `markery enhance enhance 71299042 --out-dir /tmp/test` runs end-to-end.
6. Verify `markery enhance batch "..."` runs end-to-end.
7. Verify `markery enhance gallery` still works (no regression).

**P2 — Wikipedia: add `from-essay` subcommand — CLOSED**

1. Add `cmd_from_essay()` to `wikipedia/cli.py`. Signature: `markery wikipedia from-essay <essay_path> --out <out_path> [--title <title>] [--serial <serial>] [--category <cat>]...`
2. Build a `build_standalone_wikitext()` function in `wikitext.py`. Calls `markdown_to_wikitext()` on the essay body, then appends:
   - A sources section with a TSDR ref if `--serial` is provided
   - Category tags from `--category` args (plus `[[Category:Trademarks of the United States]]` by default if serial is present)
3. Register the subcommand in the argparse block.
4. Test: `markery wikipedia from-essay projects/monthly-image-review/essays/chicago-pneumatic-cp.md --out projects/monthly-image-review/wikipedia/chicago-pneumatic-cp.wiki --serial 71299042 --title "Chicago Pneumatic Tool Company" --category "Pneumatic tools" --category "Manufacturing companies based in New York City"`
5. Verify output matches expected wikitext structure.

**P3 — Update pyproject.toml dependency documentation — CLOSED**

Clarify the three-tier install in pyproject.toml comments and SETUP.md:
- Base: gallery works, no optional extras needed
- `[enhance]` (after P1 fix): enhance + batch + gallery work, Lanczos upscaling (cv2 + vtracer required, auto-installed)
- `[enhance]` with realesrgan manually installed: full Real-ESRGAN 4× upscaling activated automatically

**P4 — Wikipedia live edit test**

P4 depends on P2 (from-essay command). Goal: demonstrate the full write path — auth, targeted edit, diff review, submission — on real Wikipedia articles using primary source data from Markery databases. Graduated from zero-risk sandbox through to a mainspace citation or external link.

**What the article scan found (2026-05-20, read-only):**

| Article | Length | TSDR ref | Relevant gap | Markery data available |
|---|---|---|---|---|
| Chicago Pneumatic | 15,173 chars | None | External links section has 5 links, no TSDR; article has no mention of 1930 CP trademark filing | Serial 71299042, Reg 274,689, filed 1930-04-18; essay and wikitext draft already written |
| Soundex | 11,723 chars | None | Russell/Odell sentence uncited for trademark/patent filing; no trademark section | Serial 71246709 filed 1927-03-31; but owner chain complex (Kardex Systems now, Remington Rand historically) — requires attribution research before editing |
| Remington Rand | 16,502 chars | None | Mentions Rand Kardex as subsidiary; no trademark citations | SOUNDEX, VARIADEX, KARDEX pairs confirmed; good second-tier target |
| Kardex | 454 chars | None | Disambiguation stub; KARDEX trademark confirmed (serial 71426576, Reg 377,986) | Better as addition to Kardex Group article than the dab page |

Chicago Pneumatic is the primary test target: clean owner chain, existing essay, article already has a logo on Commons, and the External links gap is the lowest-risk entry point.

**Infrastructure needed before P4 can run:**

1. **Wikipedia account** — Must be created manually at en.wikipedia.org. Bot passwords are issued under Special:BotPasswords once logged in. Credentials go in `.env` as `WIKIPEDIA_USERNAME` and `WIKIPEDIA_BOT_PASSWORD`. The API client (`wikipedia/api.py`) already reads these.

2. **`markery wikipedia verify-credentials`** — New subcommand. Calls `client.login()`, reports success or the error from the API. No read or write operation beyond the login token exchange. Analogous to `markery trademark verify-credentials`. Add to `wikipedia/cli.py`.

3. **`markery wikipedia add-external-link`** — New subcommand for targeted read-modify-write on an External links section. Safer than full-page replacement for this class of edit. Signature: `markery wikipedia add-external-link <page-title> <url> <label> [--summary <msg>]`. Reads current wikitext, finds the `== External links ==` section, appends `* [<url> <label>]`, shows a unified diff, prompts for confirmation, then calls `edit_page()`. If the URL is already present, exits with a "already linked" notice.

**Test sequence (graduated):**

*Stage 4a — Sandbox* (zero risk)  
Write a dated test note to `Wikipedia:Sandbox` using the existing `submit` command with `--title "Wikipedia:Sandbox"`. Draft content: a single paragraph noting that this is a test edit from a research tool verifying the auth and write flow. Confirm the edit appears in the sandbox revision history. Verify the interactive diff-and-confirm flow works end-to-end. Revert is automatic (sandbox is periodically reset by Wikipedia bots).

*Stage 4b — External link addition* (minimal impact, mainspace)  
Add the TSDR filing URL to the Chicago Pneumatic article's External links section using `add-external-link`:
```
markery wikipedia add-external-link "Chicago Pneumatic" \
  "https://tsdr.uspto.gov/#caseNumber=71299042&caseType=SERIAL_NO&searchType=statusSearch" \
  "USPTO TSDR — CP trademark Serial No. 71299042 (filed 1930)" \
  --summary "Add primary USPTO filing record for the CP trademark (Serial No. 71299042, filed 1930-04-18)"
```
This adds one line to an existing section. No existing content is modified. The edit is additive and verifiable. Easily reverted by any editor.

*Stage 4c — Inline citation* (small content addition, mainspace)  
After Stage 4b is live and unreverted (give it 48 hours), add one sentence to the Chicago Pneumatic History section citing the 1930 trademark filing. Example: "The CP monogram design trademark (USPTO Serial No. 71299042) was filed on April 18, 1930, covering pneumatic tools, air compressors, and related apparatus.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71299042&caseType=SERIAL_NO&searchType=statusSearch|title=TSDR Serial No. 71299042|publisher=United States Patent and Trademark Office}}</ref>" Use `edit_page()` with read-modify-write, show full diff, confirm before submitting.

*Stage 4d — Second article* (deferred)  
After Stages 4a–4c complete, identify the next target. Remington Rand or the Soundex article (pending resolution of the owner attribution question: 1927 filer was almost certainly Rand Kardex Corporation or a predecessor, not Remington Rand itself, since the SOUNDEX filing predates the 1927 merger by months).

**Safety principles:**

- Never modify or remove sourced existing content — only add
- All added facts must cite a public primary source (TSDR URL or USPTO patent number)
- Always show and review the unified diff before confirming
- `bot: false` is already set in `api.py` — all edits are attributed to the account, not flagged as automated
- Edit summary must name the primary source (serial number and filing date)
- Minimum 48 hours between Stages 4b and 4c to monitor for reversions
- If any edit is reverted, treat it as a signal to reconsider the content before proceeding

---

### Phase Gate

P1 PASSED when: `markery enhance enhance <serial>` runs to completion without error in an environment with only `pip install -e ".[enhance]"` (no manual realesrgan install), and `model_used` reports `"lanczos-fallback"`. — PASSED 2026-05-22

P2 PASSED when: `markery wikipedia from-essay <essay_path> --serial <serial>` produces valid wikitext without requiring `confirmed.jsonl` to exist, for any project or no project. — PASSED 2026-05-22

P3 PASSED when: `SETUP.md` accurately describes the three dependency tiers and a new contributor can reach each tier by following the documented steps. — PASSED 2026-05-22

P4 PASSED when: Stage 4b (Chicago Pneumatic external link) is live on English Wikipedia and unreverted after 48 hours.

Phase PASSED when P1, P2, P3, and P4 all pass.

---

## Phase 10 — Common Layer: Project Types — CLOSED

**Opened:** 2026-05-21  
**Scope:** Add project type as a first-class concept in the common layer. Prerequisite for Phase 11 token-reduction tools and for type-aware orchestrator routing. Full design in `archive/COMMON-REVIEW-2026-05-21.md`.

---

### P1 — `common/project.py`: foundation module — CLOSED

1. Create `src/markery/common/project.py`
2. Define `ProjectType` enum: `MATCH_REVIEW_ESSAY`, `GALLERY_EXPLORATION`
3. Move `Project` dataclass from `config.py` to `project.py`; update `config.py` to remove it; update all import sites
4. Refactor `Project` path properties — match-review-essay-specific paths (`candidates`, `confirmed`, `rejected`, `pipeline_state`, `entities_file`, `objectives`, `brief`) protected by type check or moved to a typed subclass; `root` and `exists()` remain universal
5. Add `load_project(path: Path) -> Project` — reads `project.json` from project root, returns typed `Project`; raises with a clear message directing user to `markery project adopt` if `project.json` is absent
6. Add `detect_project_type(path: Path) -> ProjectType | None` — heuristic: presence of `entities.txt` or `confirmed.jsonl` → `MATCH_REVIEW_ESSAY`; presence of `essays/` or `output/` without match pipeline files → `GALLERY_EXPLORATION`; ambiguous → `None`
7. Update `common/__init__.py` to export `Project`, `ProjectType`, `load_project`

---

### P2 — Write `project.json` for existing projects — CLOSED

1. Write `projects/information-systems/project.json`: `{"type": "match-review-essay"}`
2. Write `projects/monthly-image-review/project.json`: `{"type": "gallery-exploration"}`
3. Verify `load_project()` returns the correct type for both

---

### P3 — `markery project init` — CLOSED

1. Add `project` to `_SUBCOMMANDS` in `cli.py`; add `cmd_project()` dispatch function
2. Implement `init` subcommand: prompt for project name if not given; prompt for type from a numbered list; scaffold directory per type's structure definition in `project.py`; write `project.json`, starter `README.md`, and `STATUS.md`
3. Structure definitions per type live in `project.py` — the single source of truth for what each type requires

---

### P4 — `markery project adopt` — CLOSED

1. Implement `adopt` subcommand
2. Flow: run `detect_project_type()`; display the inference with the signals found; prompt confirm or select from type list; write `project.json`
3. Handle `None` inference (ambiguous directory): present all type options without a pre-selected default

---

### P5 — Orchestrator type awareness — CLOSED

Note: implementation touches `specialist/orchestrator.py`, not the common layer, but is driven by this phase.

1. Add `project_type(path: Path) -> ProjectType` to `orchestrator.py` — delegates to `load_project()`
2. Update `enrich_signal_fields` to validate project type before dispatching; raise `TypeError` with a clear message if project is not `MATCH_REVIEW_ESSAY`
3. Add `Project` type annotations throughout `orchestrator.py` where applicable

---

### Phase Gate

P1 PASSED when: `from markery.common import Project, ProjectType, load_project` works; `load_project(Path("projects/information-systems"))` returns a `MATCH_REVIEW_ESSAY` project; `load_project(Path("projects/monthly-image-review"))` returns a `GALLERY_EXPLORATION` project. — PASSED 2026-05-22

P2 PASSED when: both existing projects have `project.json` committed and `load_project()` resolves both correctly. — PASSED 2026-05-22

P3 PASSED when: `markery project init test-project` creates a new directory with correct type-specific structure and `project.json`. — PASSED 2026-05-22

P4 PASSED when: `markery project adopt` (run on a project without `project.json`) infers the correct type, shows the signals found, prompts for confirmation, and writes `project.json`. — PASSED 2026-05-22

P5 PASSED when: `enrich_signal_fields` raises a typed error when passed a `GALLERY_EXPLORATION` project. — PASSED 2026-05-22

Phase PASSED when P1–P5 all pass. — PASSED 2026-05-22

---

## Phase 11 — Specialist Tools: Token Reduction and Model Accessibility — CLOSED

**Opened:** 2026-05-21  
**Dependency:** Phase 10 must be complete — all tools that accept a project argument require `load_project()` and type validation.  
**Scope:** Seven new specialist-owned CLI tools that shift project work from LLM token consumption toward deterministic code, and reduce context burden enough to make cheaper or local models viable for portions of the workflow. Full specifications in `archive/SPECIALIST-REVIEW-2026-05-21.md`. Implementation order follows dependency chain: auto-disposition → preflight → suggest-variants → card → digest → scaffold → validate.

---

### P1 — `markery match auto-disposition` (MATCHMAKER) — CLOSED

Applies deterministic rejection rules to candidates below a configurable score threshold. Writes rejection records to `rejected.jsonl` with `auto_rejected: true` flag. `--dry-run` reports without writing. Eliminates model review for below-floor candidates — typically 30–50% of the queue.

1. Add `cmd_auto_disposition()` to matchmaker CLI
2. Implement rejection rules: score threshold, date gap ceiling, class mismatch, company-name-mark flag
3. Read threshold and ceiling from `matches/auto_disposition.json` if present; fall back to CLI flags; default threshold 0.25
4. `--dry-run` output: table of candidates that would be rejected with reason strings
5. Verify: `markery match auto-disposition information-systems --dry-run` shows expected rejections without writing

---

### P2 — `markery match preflight` (MATCHMAKER) — CLOSED

Pre-runs all available enrichment for a project before any model session. Fetches signals for candidates above min-score; TSDR for uncertainty-band candidates lacking goods descriptions; figures for confirmed pairs lacking images. Writes `matches/preflight.json` recording what was fetched and skipped.

1. Add `cmd_preflight()` to matchmaker CLI
2. Sequence: signals enrichment → TSDR enrichment → figure fetch; each step reads DB state to determine what is missing
3. `preflight.json` format: per-step counts (fetched, skipped, quota-hit, already-present), timestamp
4. Verify: running preflight on a fully-enriched project produces an all-zero report with no errors

---

### P3 — `markery matchmaker suggest-variants` (MATCHMAKER) — CLOSED

Fuzzy-matches a canonical entity name against `assignee_name` in `patents.duckdb` and `own_name` in `trademarks.duckdb`. Returns ranked candidate variant strings with occurrence counts and source. Uses token overlap, edit distance, and common abbreviation expansion (Inc./Incorporated/Corp./Company/Co.).

1. Add `cmd_suggest_variants()` to matchmaker CLI
2. Implement matching: token overlap score + edit distance + abbreviation normalization
3. Output: ranked table showing patent variants and trademark variants separately with occurrence counts
4. Verify: `markery matchmaker suggest-variants "Remington Rand"` returns known variants in ranked order

---

### P4 — `markery historian card` (HISTORIAN) — CLOSED

Generates a compact (~250 token) fixed-format candidate summary block for a single slug from DB records — no model required. Structured fields optimized for model input: mark, goods, entity, patent, date gap, score, signals, essay/figure status. Written to stdout or `matches/cards/<slug>.md`.

1. Add `cmd_card()` to historian CLI
2. Implement field extraction from `trademarks.duckdb`, `patents.duckdb`, `entities.duckdb`, `candidates.jsonl`
3. Goods description truncated to first 100 chars + additional class count; no prose anywhere in the card
4. Verify: `markery historian card soundex-us1261167a` produces a parseable card matching DB records

---

### P5 — `markery historian digest` (HISTORIAN) — CLOSED

Produces a compact (~800–1,200 token) model-optimized project state summary. Dense structured blocks, no prose. Includes: confirmed/rejected/unreviewed counts, essay status by slug, next-review candidates ordered by score, enrichment status, preflight timestamp, available cards and scaffolds.

1. Add `cmd_digest()` to historian CLI
2. Implement state aggregation from `confirmed.jsonl`, `rejected.jsonl`, `candidates.jsonl`, `matches/` directory
3. Verify: `markery historian digest information-systems` fits within 1,200 tokens (measure with `tiktoken` or equivalent)

---

### P6 — `markery historian scaffold` (HISTORIAN) — CLOSED

Generates a structured essay skeleton for a confirmed pair. Factual sections pre-filled from DB records (frontmatter, primary sources, filing record, patent summary); interpretive sections left as titled prompt stubs. Written to `essays/<slug>.md`. Full field list in `archive/SPECIALIST-REVIEW-2026-05-21.md §scaffold`.

1. Add `cmd_scaffold()` to historian CLI
2. Factual section generation is pure DB read — no model. Prompt stubs are titled headings only
3. Verify: `markery historian scaffold soundex-us1261167a` produces a file with correct serial numbers, dates, and goods description pulled from DB; all factual fields match `trademarks.duckdb`

---

### P7 — `markery historian validate` (HISTORIAN) — CLOSED

Validates a completed essay against the DB. Checks: serial numbers resolve against `case_file`; patent numbers resolve against `patents`; dates and registration numbers match DB records; goods description excerpts match `statement` within edit-distance threshold; entity name matches a known variant; no cross-pair contamination. Structured report; exit code 1 on any failure.

1. Add `cmd_validate()` to historian CLI
2. Implement each check as a named function; collect results into a structured report
3. Report: one line per check, PASS/FAIL, discrepancy detail on failure
4. Verify: validate on a known-good essay returns all-PASS; a deliberate serial number error is caught

---

### Phase Gate

P1 PASSED when: `markery match auto-disposition information-systems --dry-run` correctly identifies below-floor candidates; `--reject-below` writes to `rejected.jsonl` with `auto_rejected: true`. — PASSED 2026-05-22

P7 PASSED when: `markery historian validate` catches a deliberate date error injected into a test essay. — PASSED 2026-05-22

Phase PASSED when P1–P7 all pass and at least one end-to-end cheap-model workflow has been demonstrated: digest + cards loaded into a small-context session, candidate review decisions written, validate run on the resulting essay without errors.

---

## Phase 12 — Hardening and Test Coverage — CLOSED

**Opened:** 2026-05-22  
**Trigger:** Phase 11 complete. Do not begin this phase while the architecture from Phases 10–11 is still settling — hardening code that is about to change produces wasted work.  
**Scope:** Harden existing CLI boundaries, close test coverage gaps across the full codebase (including all Phase 11 additions), re-enable CI, and complete a persona instruction card pass. Absorbs D012 (CI workflow), D013 (test coverage gaps), D016 (remove stale migrate-figures command), D017 (patent persona cards), D018 (trademark persona cards), and D019 (deduplicate matchmaker read functions) from DEFERRED.

---

### P1 — Hardening: CLI cleanup, input validation, and error messages

Target: system boundaries where bad input causes unhelpful failures, plus two small code-quality items (D016, D019) whose triggers have now fired.

1. Project name validation in all commands that accept `<project>` — clear error if the directory does not exist or `project.json` is absent (with hint to run `markery project adopt`)
2. Serial number and patent number format validation at CLI entry points — reject obviously malformed values before any DB or API call
3. Missing DB error messages — if `patents.duckdb`, `trademarks.duckdb`, or `entities.duckdb` are absent, surface the specific setup step required rather than a DuckDB IO error
4. Orchestrator type guard coverage — verify all cross-specialist functions added in Phase 10 P5 have type validation; add any that were missed
5. Remove `migrate-figures` from patent CLI (D016) — confirm no projects have on-disk PNGs remaining; remove `cmd_migrate_figures`, its argparse entry, and its dispatch table entry from `patent/cli.py`
6. Deduplicate matchmaker read functions (D019) — make `link.py` and `pipeline.py` import `read_confirmed`, `read_rejected`, and `read_state` from `queries.py` instead of defining them locally

---

### P2 — Test coverage: common layer and orchestrator

1. `common/auth.py` — credential loading, missing env var error paths
2. `common/project.py` — `load_project()` (valid, missing `project.json`, wrong type value), `detect_project_type()` (each signal combination), `Project` path properties per type
3. `common/config.py` — ROOT detection, DB path construction
4. `cli.py` — subcommand dispatch, unknown subcommand error path
5. `orchestrator.py` — all five existing functions plus `project_type()` added in Phase 10; type guard error paths

---

### P3 — Test coverage: build modules

Currently untested (from D013): the most operationally consequential module in each specialist.

1. `patent/build.py` — DB schema creation, record upsert, resume state
2. `patent/signals.py` — signal field enrichment against a test candidate set
3. `trademark/build.py` — bulk load, TSDR enrichment upsert
4. `publisher/build.py` — site build from a minimal test project fixture

---

### P4 — Test coverage: Phase 11 tools

All seven commands added in Phase 11 are untested at phase-open time.

1. `auto-disposition` — threshold logic, reason string generation, dry-run vs write behavior
2. `preflight` — per-step enrichment gating, `preflight.json` output format
3. `suggest-variants` — matching logic against known variant fixtures
4. `card` — field extraction, goods truncation, output format
5. `digest` — state aggregation, token budget (measure against 1,200 token ceiling)
6. `scaffold` — factual section population, prompt stub format, no-model requirement
7. `validate` — each check type; deliberate error injection for every check

---

### P5 — CI: re-enable workflow and badge

Recreate CI infrastructure deleted in Phase 7 (D012).

1. Recreate `.github/workflows/ci.yml` running `pytest` on push and PR
2. Verify CI passes on a clean checkout with the venv activated
3. Add CI badge back to `README.md`: `[![CI](https://github.com/<owner>/markery/actions/workflows/ci.yml/badge.svg)](https://github.com/<owner>/markery/actions/workflows/ci.yml)`

---

### P6 — Persona instruction cards (D017, D018)

Complete the instruction card pass deferred after Phase 8. Cards are short markdown files in each specialist's `persona/instructions/` directory that document one command each — purpose, inputs, outputs, failure modes.

**Patent specialist (D017):** Three commands currently undocumented:
1. `signals` — text signal enrichment for a project's candidates; inputs: project name; outputs: enriched candidate count; key failure: candidates.jsonl not yet generated
2. `fetch` — batch patent figure fetch for all confirmed pairs in a project; inputs: project name; outputs: figure count stored; key failure: EPO quota hit mid-batch
3. `verify-credentials` — EPO OPS OAuth2 token test; inputs: none; outputs: success/failure with token endpoint response

**Trademark specialist (D018):** Four commands currently undocumented:
1. `enrich-project` — batch TSDR fetch for all marks in a project's confirmed or candidates list; distinct from `enrich` (single serial) — document the distinction explicitly to prevent confusion
2. `fetch` — TSDR-only fetch into `extended_marks` without image download; distinct from `enrich` which fetches both
3. `status` — row counts for all trademark tables; inputs: none; outputs: table of counts
4. `verify-credentials` — USPTO API key test; inputs: none; outputs: success/failure

---

### Phase Gate

P1 PASSED when: CLI boundary guards, input validators, missing-DB messages, and deduplication items D016/D019 are complete. — PASSED 2026-05-22

P2 PASSED when: `pytest tests/` covers common layer and orchestrator with no failures. — PASSED 2026-05-22

P3 PASSED when: build modules for patent, trademark, and publisher have test coverage with no failures. — PASSED 2026-05-22

P4 PASSED when: all seven Phase 11 commands have at least one passing test each. — PASSED 2026-05-22

P5 PASSED when: CI workflow is green on a clean push and the badge is visible in README. — PASSED 2026-05-22

P6 PASSED when: all seven instruction cards exist and accurately describe current command behavior. — PASSED 2026-05-22

Phase PASSED when P1–P6 all pass and CI is green. — PASSED 2026-05-22

---

## Phase 13 — Public Readiness: Documentation and v0.3.0 — CLOSED

**Opened:** 2026-05-22  
**Trigger:** Phase 12 complete — CI must be green before tagging a public release.  
**Scope:** Make Markery usable by someone who discovers the repository for the first time, with no insider knowledge and no pre-existing project data. Culminates in a tagged v0.3.0 release. Absorbs D011 (GitHub Pages deployment) and D022 (Built with Markery footer) from DEFERRED.

**Goal state:** A researcher clones the repo, follows SETUP.md, and can run `markery project init` to start a new project — without asking for help and without reading any source code.

---

### P1 — Codebase and documentation audit

Conduct a structured audit using a PUBLIC-READINESS-REVIEW.md at repo root (archive when complete per the REVIEW file convention).

1. Walk every module for hardcoded assumptions: absolute paths, project-specific serial numbers or patent numbers, insider variable names, undocumented constants. Record each finding.
2. Walk every root document (`README.md`, `SETUP.md`, `CONTEXT.md`, `DESIGN.md`, `CLAUDE.md`) for: jargon with no definition, references to internal phase labels or session notes, prerequisites that are assumed but not stated, instructions that have drifted from current command names or flags.
3. Verify `markery --help` and each subcommand `--help` accurately describes current behavior.
4. Produce a gap list: items resolved inline (small fixes), items promoted to DEFERRED (larger scope), items that block the public release.

---

### P2 — Publisher output: footer and GitHub Pages (D022, D011)

Complete publisher output before the site goes public. Both items are natural to do together — the footer appears in every built page, and GitHub Pages is how the site is deployed.

1. Add "Built with Markery" footer to publisher-generated HTML (D022) — add a footer block to the Jinja template in `publisher/render.py`; footer text: "Built with [Markery](https://github.com/CosmoGSpacely/markery)"; make repo URL configurable via a `site_config` parameter so projects can override it
2. Verify footer appears correctly: run `markery site build information-systems`, inspect output HTML
3. Re-enable GitHub Pages deployment (D011) — diagnose the original `pages.yml` failure, recreate `.github/workflows/pages.yml` deploying the built site on push to main, verify Pages is enabled in repository settings
4. Confirm a full site build followed by a Pages deploy produces a live URL with the footer visible

---

### P3 — Public repo hygiene

1. Confirm `.gitignore` is comprehensive — no credential files, no large binaries, no user-specific paths that could be committed accidentally.
2. Verify the three committed `.duckdb` files are appropriate to share: no personal data, no private API responses beyond what the USPTO and EPO publicly provide, size is reasonable (~25–50 MB total).
3. Add `LICENSE` file if absent. Determine and record the intended license.
4. Review git history for any accidentally committed secrets (`.env` contents, API keys). If found, scrub with `git filter-repo` before proceeding.
5. Check that `CONTRIBUTING.md` or equivalent guidance exists for anyone who wants to submit a patch.

---

### P4 — SETUP.md: verified fresh-machine install

Rewrite SETUP.md so that the steps are executable in sequence by someone who has never seen the repo.

1. Prerequisites section: Python version requirement, system packages if any, Git LFS if needed for the `.duckdb` files.
2. Install section: clone → venv → `pip install -e "."` → verify with `markery --version`.
3. Credential setup: one section per API (EPO OPS, USPTO / TSDR, Wikipedia). For each: where to register, what keys to obtain, exact `.env` variable names, verification command (`markery patent verify-credentials`, `markery trademark verify-credentials`, `markery wikipedia verify-credentials`).
4. First-run section: `markery project init` to scaffold a project, `markery status` to confirm DB access, pointer to project-type-specific workflow docs.
5. Verify: perform a clean install in a fresh venv following only the written steps. Fix any step that fails or requires unlisted knowledge before marking passed.

---

### P5 — README overhaul

Rewrite `README.md` to lead with purpose, not structure.

1. Opening paragraph: what Markery is, what research problem it solves, what kind of output it produces. No implementation detail in the first screen.
2. Quickstart: three to five commands that produce visible output (e.g., `markery project init`, `markery status`, `markery enhance gallery`).
3. "How it works" section: brief description of the five specialists and the project model — enough for a stranger to understand the architecture before reading DESIGN.md.
4. Links section: SETUP.md (installation), CONTEXT.md (background and goals), DESIGN.md (engineering rationale), CONTRIBUTING.md.
5. CI badge (from Phase 12 P5).

---

### P6 — Tag v0.3.0

1. Bump version in `pyproject.toml` and `src/markery/__init__.py` from `0.2.1a0` to `0.3.0`.
2. Confirm CI is green on the current HEAD.
3. Tag: `git tag -a v0.3.0 -m "v0.3.0 — public readiness release"`.
4. Push tag: `git push origin v0.3.0`.

---

### Phase Gate

P1 PASSED when: audit is complete, gap list documented in PUBLIC-READINESS-REVIEW.md, all blocking gaps resolved or explicitly deferred with triggers. — PASSED 2026-05-22

P2 PASSED when: footer visible in a built site and GitHub Pages deployment is live. — PASSED 2026-05-22

P3 PASSED when: LICENSE file present, git history clean of secrets, `.duckdb` files verified appropriate to share. — PASSED 2026-05-22

P4 PASSED when: a clean venv install following only the written SETUP.md steps produces a working `markery --version` and `markery status` without any unlisted prerequisite. — PASSED 2026-05-22

P5 PASSED when: README leads with purpose, quickstart is verified to work, reviewed and approved before tagging. — PASSED 2026-05-22

P6 PASSED when: `git tag v0.3.0` is pushed, CI is green on the tagged commit. — PASSED 2026-05-22

Phase PASSED when P1–P6 all pass and v0.3.0 is pushed. — PASSED 2026-05-22

---

## Post-v0.3.0 Horizon

The following phases are sketched at summary resolution. They are not sequenced or gated yet — they exist so the direction is visible. Promote to full phase entries when Phase 13 is in progress.

---

### Phase 14 — Efficiency Baseline: Token and Model Benchmarking

**Goal:** Measure Markery's current token consumption and model sensitivity across real workflows, then improve both. This phase closes the gap between DESIGN.md's model-agnosticism principle and the reality of how sessions are run in practice.

**What it covers:**
- Define a benchmark suite: a fixed set of representative historian sessions (one card, one digest, one scaffold, one validate) run against two models — a capable paid model and a capable free-tier or open model
- Instrument token counts at each specialist boundary: prompt size in, completion size out, total per command
- Identify the top three token-cost hotspots (likely: persona system prompts, large candidates.jsonl payloads, full DB dumps passed in context)
- Apply targeted reductions: structure-aware truncation for large payloads, lazy-load patterns for context fields not needed in every call, sliding window strategies for long pipelines
- Re-run benchmark after each reduction and record the delta
- Define MVO (minimum viable output) contracts per command formally enough to be testable: a command passes the MVO test if its output is checkable by code without human inspection

**Free-model target:** By end of this phase, the gallery-exploration and card/digest historian workflows should be completable end-to-end on a free cloud model (Gemini Flash, Mistral free tier, or equivalent) without exceeding that model's context window or producing hallucinated structured data. Match-review-essay workflows (which require sustained judgment) may remain paid-model-preferred.

**Closes:** D021 reopen path (the model-agnosticism section in DESIGN.md commits to this direction; Phase 14 is where it is measured and acted on).

---

### Phase 15 — LIBRARIAN Specialist: Cross-Project Reference Retrieval

**Goal:** Build the sixth specialist when the two blocking conditions in D020 are met. Do not begin this phase until both are confirmed true.

**Blocking conditions (from D020):**
1. `references/` format is proven across at least two projects with curated, annotated excerpts
2. The historian has demonstrated a concrete need for cross-project retrieval that a single project's `references/` cannot satisfy

**What it covers:**
- Establish `library/works/<author-title-slug>/` structure at repo root: `metadata.json` (bibliographic record), `excerpts.md` (annotated passages), `index.md` (chapter/section map)
- Implement `markery library ingest <work-slug>` to add a work to the library corpus
- Implement two-tier retrieval: keyword search across all `excerpts.md` files (immediate, no dependencies), then semantic search over vector embeddings (DuckDB vector extension or LanceDB, with embedding step at ingest)
- Historian interface: `search_library(query) -> list[Excerpt]`, callable from any research session regardless of which project is active
- Persona and instruction cards per the Phase 12 P6 pattern

**Closes D020.**

---

### Phase 16 — PatentsView Bulk Import (D007)

**Goal:** Add an alternative patent acquisition path for projects with 1976+ scope where EPO OPS quota is a bottleneck or CPC class coverage gaps exist.

**What it covers:**
- Implement `markery patent bulk-import --tsv-dir <path> --year-start <YEAR> --year-end <YEAR> --classes <CPC> [...]`
- Read from PatentsView `.tsv.gz` bulk files using DuckDB `read_csv()` with `delim='\t'` and predicate pushdown for year and class filters
- Construct `patent_no` as `US{number}{kind}` to match existing schema
- Insert-if-not-exists semantics (idempotent against current schema)
- Specialist instruction card and verify step

**Trigger:** A project with 1976+ scope opens where EPO OPS quota is a genuine bottleneck, or where PatentsView's coverage of assignee names and abstracts is needed. Full design in `specialist/patent/BULK_CSV.md`.

**Closes D007.**
