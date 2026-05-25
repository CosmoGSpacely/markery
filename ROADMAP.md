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

## Phase 15 — LIBRARIAN Specialist: Acquisitions, Indexing, and Semantic Retrieval

**Trigger:** Phase 14 complete — v0.3.0 public, token benchmarks established.  
**Scope:** Build the sixth specialist with two distinct capabilities: (1) an acquisitions layer that fetches full text from Internet Archive and Project Gutenberg and uses Claude to extract relevant passages; (2) a retrieval layer with both keyword and semantic (vector) search. LIBRARIAN owns `library/` at repo root and makes secondary literature available to any historian session via compact context cards.

**Goal state:** By phase close, `markery librarian acquire` can fetch a public-domain work and populate its excerpts using Claude-assisted extraction; `markery librarian search` supports both keyword and semantic (embedding-based) modes; at least five works are indexed with real passages; the historian can load a context card in any session; D020 is closed.

**Source landscape:**
- **Internet Archive (primary):** No auth required for public domain works. Full text available as plain `.txt` or EPUB. Large collection strong in American business and industrial history 1870–1930.
- **Project Gutenberg via Gutendex (secondary):** No auth required. Human-proofread plain text — highest quality. Smaller collection; fills gaps for canonical titles IA also has but with better OCR.
- **Library of Congress:** Supplemental, for government reports and trade publications where IA coverage is thin.
- **Google Books:** Metadata and discovery only — API cannot return full text programmatically. Used to find an IA or Gutenberg copy of a known title, not as a text source itself.
- **HathiTrust:** Data API retired July 2024. Not viable for real-time access.

**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (local, no API key, ~80 MB). Fits the model-agnosticism principle; runs offline. Embeddings stored as JSON float arrays in `library/index.duckdb`; cosine similarity computed in Python with numpy at search time. Swappable via config for an API-based provider (OpenAI, Voyage AI) if scale or quality requires it.

**D020 blocking condition status (at phase open):**
- Condition 1 (format proven across two projects): NOT MET — `information-systems/references/` has three stub files; `monthly-image-review` has no `references/` directory. Met in P1.
- Condition 2 (concrete cross-project retrieval need): NOT MET — no second project holds references. Met in P1.

---

### P1 — Prove blocking conditions

Satisfy D020 conditions before writing a line of specialist code. This is manual work — the acquisitions tooling built in P2 will automate future corpus growth, but the format must be proven first with hand-curated content.

1. Populate real excerpts in `information-systems/references/` for at least two works. Yates (*Control Through Communication*) and Cortada (*Before the Computer*) both have IA-borrow access via their `ia_identifier` fields. Each passage block must have a verbatim quotation with page number and a context note. Stub `<!-- Add passage -->` comments do not count.
2. Create `projects/monthly-image-review/references/` with at least one work relevant to that project's scope — a history of American industrial tool design marks, Chicago Pneumatic's industry context, or branding in the 1920s–1930s manufacturing sector. Follow the format in `information-systems/references/README.md`.
3. In `projects/monthly-image-review/references/README.md`, name one specific passage in `information-systems/references/` that this project's historian would use — documenting the cross-project retrieval need concretely.
4. Commit all reference files. Verify: both directories have at least one work with real (non-stub) passage sections.

---

### P2 — Source adapters and acquisition CLI

Build the layer that fetches works from external sources. Output is normalized to a common format regardless of source.

**Source adapters** — one module per source in `src/markery/specialist/librarian/sources/`:

1. `ia.py` — Internet Archive adapter:
   - `search(query, max_results=10) -> list[IAResult]`: calls the IA search API (`archive.org/advancedsearch.php`), returns items with `identifier`, `title`, `creator`, `year`, `mediatype=texts`
   - `fetch_metadata(identifier) -> dict`: calls `/metadata/{identifier}`, returns structured metadata
   - `download_text(identifier, out_dir) -> Path`: downloads the `.txt` file (preferred) or falls back to EPUB; saves to `out_dir/<identifier>.txt`

2. `gutenberg.py` — Project Gutenberg adapter via Gutendex (`gutendex.com/books`):
   - `search(query, max_results=10) -> list[GutenbergResult]`
   - `fetch_metadata(book_id) -> dict`
   - `download_text(book_id, out_dir) -> Path`: downloads plain text format

3. `wikipedia.py` — Wikipedia discovery adapter (discovery only, not a text source):
   - `fetch_citations(article_title) -> list[WikiCitation]`: calls the Wikipedia API (`action=parse&prop=wikitext`), extracts `{{cite book}}` and `{{cite journal}}` templates, parses author/title/year/isbn/url fields into a `WikiCitation` dataclass
   - `resolve_to_source(citation) -> SourceResult | None`: for each citation, searches IA and Gutenberg for a matching work by title + author + year; returns the best match or None if not found
   - Wikipedia article prose is never used as a source — this adapter surfaces what Wikipedia's editors have already cited, not Wikipedia's own claims

4. `common.py` — shared `SourceResult` and `WikiCitation` dataclasses; `normalize_metadata() -> dict` for mapping source-specific fields to the `library/works/<slug>/metadata.json` schema; `WantsEntry` dataclass (title, author, year, isbn, source_article, added_at, status: `wanted | in-progress | acquired`).

**CLI commands:**

5. `markery librarian search-sources <query> [--source ia|gutenberg|all] [--top N]`: searches registered sources and prints a ranked results list with identifier, title, author, year, and source. No download. Used to discover works before acquiring them.

6. `markery librarian discover --wikipedia <article-title> [--add-wants]`: fetches the Wikipedia article's citations; for each, searches IA and Gutenberg; prints a three-column report:

   ```
   FOUND (IA)    cortada-before-the-computer    Before the Computer, Cortada 1993
   FOUND (GUT)   yates-control-through-comm     Control Through Communication, Yates 1989
   NOT FOUND     —                              The Punched Card, Austrian 1982
   NOT FOUND     —                              Office Management, Galloway 1919
   ```

   With `--add-wants`, NOT FOUND entries are appended to `library/wants.jsonl` with status `wanted` and `source_article` recorded.

7. `markery librarian wants [--status wanted|in-progress|acquired]`: prints the wants list with status, title, author, year, and source article. Default shows only `wanted` and `in-progress`.

8. `markery librarian wants-update <title-slug> --status <status> [--note <text>]`: updates a wants entry status (e.g., mark `in-progress` when ILL request is submitted, `acquired` when the copy arrives).

9. `markery librarian acquire <identifier> [--source ia|gutenberg]`: fetches metadata and full text for a work; creates `library/works/<slug>/` with `metadata.json` and `raw_text.txt`; prints the created slug. Does not extract passages — that is P4's job. If the work was in `wants.jsonl`, automatically updates its status to `acquired`.

10. `markery librarian enter <slug> --title <title> --author <author> --year <year> [--isbn <isbn>]`: manually registers a work that arrived via ILL or other non-digital acquisition. Creates `library/works/<slug>/metadata.json` with `source: manual` and an empty `excerpts.md`. No `raw_text.txt` is created — the user adds excerpts by hand. If the work was in `wants.jsonl`, updates its status to `acquired`.

11. `markery librarian raw-text <slug>`: prints the path to `raw_text.txt` for a work (for manual inspection before extraction).

---

### P3 — Library structure and migration

Establish the canonical `library/` schema and migrate existing per-project reference files.

1. Create `library/` at repo root:
   - `library/README.md` — schema documentation, sourcing guidelines, acquisition workflow
   - `library/wants.jsonl` — works identified but not yet obtainable digitally; one JSON record per line (title, author, year, isbn, source_article, added_at, status)
   - `library/works/<slug>/metadata.json` — structured metadata (source: ia|gutenberg|manual, author, title, year, isbn, ia_identifier, ia_access, gutenberg_id, acquired_at)
   - `library/works/<slug>/raw_text.txt` — full acquired text (absent for manual entries; never committed to git if >1 MB — add to `.gitignore`)
   - `library/works/<slug>/excerpts.md` — curated passages with page references and context notes
   - `library/works/<slug>/index.md` — topic index: one line per passage heading
2. Migrate the three `information-systems/references/` works (Yates, Cortada, Austrian/Hollerith) into `library/works/`. Carry all curated content.
3. Migrate `monthly-image-review/references/` work(s) on the same basis.
4. Convert per-project `references/` files to citation stubs: `see: library/works/<slug>`. Update both `references/README.md` files to describe the pointer convention.
5. Add `library/works/*/raw_text.txt` to `.gitignore` (texts can be multi-MB; re-acquirable on demand).
6. Verify: `library/` has at least four works; no passage content outside `library/`; raw texts excluded from git.

---

### P4 — Claude-assisted passage extraction

The acquisitions layer fetches raw text; this layer turns it into curated excerpts.

1. Implement `markery librarian extract <slug> --topics <topic> [<topic> ...] [--max-passages N]`:
   - Reads `library/works/<slug>/raw_text.txt`
   - Chunks the text into overlapping windows (~2,000 tokens each with 200-token overlap)
   - For each chunk, sends a prompt to Claude: "From the following passage, extract up to 3 verbatim quotations relevant to: {topics}. For each quotation, provide: the quoted text, an estimated page reference, and one sentence of context explaining its relevance."
   - Collects candidate passages across all chunks; deduplicates by similarity
   - Writes candidates to `library/works/<slug>/candidates.md` (staging area, not yet in excerpts.md)
2. Implement `markery librarian review <slug>`: interactive review of `candidates.md` — prints each candidate passage with an accept/reject/edit prompt; accepted passages are appended to `excerpts.md` with proper section heading; rejected passages are discarded.
3. Add `--auto-accept` flag to `extract` (non-interactive; writes directly to `excerpts.md`, skipping review). For use when the historian trusts the extraction quality. Default is interactive review.
4. Add `--tokens` flag to `extract` via existing `tokens.py`.
5. Verify: `markery librarian extract cortada-before-the-computer --topics "card index" "Remington Rand"` produces at least two candidate passages.

---

### P5 — LIBRARIAN persona and CLI scaffold

1. Create `src/markery/specialist/librarian/` with `__init__.py`, `cli.py`, `sources/` package, `persona/identity.md`, `persona/instructions/`.
2. Write `identity.md`: LIBRARIAN owns `library/` (reads and writes); reads `projects/*/references/` (citation stubs only); never touches DuckDB, candidates, or confirmed records; never modifies project `content/` or `site/`. Acquisition commands (fetch from external sources) are within scope.
3. Register `markery librarian` in the top-level CLI dispatcher.
4. Verify: `markery librarian --help` shows: `search-sources`, `discover`, `wants`, `wants-update`, `acquire`, `enter`, `raw-text`, `extract`, `review`, `index`, `search`, `list`, `card`.

---

### P6 — Keyword index and search

1. Implement `markery librarian index [--rebuild]`: parses all `library/works/*/excerpts.md`; extracts passage records (`work_slug`, `author`, `title`, `year`, `section`, `passage`, `context`); writes `library/index.jsonl`. The `--rebuild` flag forces a full reparse; default is incremental (only reindexes works whose `excerpts.md` is newer than the index entry).
2. Implement `markery librarian search <query> [--top N] [--mode keyword|semantic|both]`: in `keyword` mode, case-insensitive substring match across passage + section + context; returns ranked matches with citation and passage preview.
3. Implement `markery librarian list [--verbose]`: one line per work (slug, author, year, excerpt count, raw text present/absent).
4. Add `--tokens` flag to `search` and `list`.
5. Verify: `markery librarian search "card index" --mode keyword` returns at least one passage.

---

### P7 — Semantic (vector) search

1. Add `sentence-transformers` (`all-MiniLM-L6-v2`) to optional dependencies in `pyproject.toml` under `[project.optional-dependencies]` as `librarian = ["sentence-transformers>=2.2"]`. Do not require it for base install.
2. Extend `markery librarian index` with `--embed` flag: for each passage in `index.jsonl`, compute an embedding vector and store it in `library/index.duckdb` — table `passage_embeddings (work_slug TEXT, passage_id INT, embedding FLOAT[])`. Incremental: only embeds passages not already in the table.
3. Implement `markery librarian search <query> --mode semantic [--top N]`: embeds the query with the same model; loads all embeddings from `library/index.duckdb`; computes cosine similarity with numpy; returns top N passages ranked by similarity. Falls back to keyword mode with a warning if embeddings have not been built.
4. `--mode both`: runs keyword and semantic in parallel, merges results (deduplicated by passage_id), re-ranks by a weighted combination (default: 0.4 keyword presence + 0.6 semantic similarity).
5. Document the model choice in `library/README.md`: why `all-MiniLM-L6-v2`, how to substitute an API-based provider, the DuckDB embedding table schema.
6. Verify: `markery librarian search "systematic record-keeping" --mode semantic` returns the Yates passage about filing infrastructure even when "systematic record-keeping" does not appear verbatim.

---

### P8 — Historian context card

1. Implement `markery librarian card <query> [--top N] [--mode keyword|semantic|both]`: compact output (≤300 tokens) for loading into a historian session. Format per match: `[Author (Year)] Section — "passage text" (p. XX).`
2. `--out -` for stdout; default saves to `library/cards/<query-slug>.md`.
3. `--tokens` flag.
4. Verify: `markery librarian card "Remington Rand filing" --mode semantic` produces output ≤300 tokens containing at least one citation bracket.

---

### P9 — Tests, MVO contracts, and D020 close

1. Write `tests/test_librarian.py`: unit tests using `tmp_path` fixtures with synthetic library content (3 works, 5 passages each). Cover: `index` record structure; keyword search returns correct passage; semantic search returns passage (mock embeddings — patch `sentence-transformers` call); `list` enumerates works; `card` ≤300 tokens with citation markers; `extract` calls Claude with expected prompt structure (mock API); `acquire` creates correct directory structure (mock HTTP).
2. Add LIBRARIAN to `tests/benchmarks/mvo.md`: contracts for `search`, `list`, `card`, `index`.
3. All tests pass.
4. Mark D020 resolved in `DEFERRED.md`.

---

### Phase Gate

P1 PASSED when: two projects have `references/` with real excerpts; cross-project retrieval need documented.

P2 PASSED when: `markery librarian acquire` successfully fetches a work from IA; `search-sources` returns results for a known query; `markery librarian discover --wikipedia "Soundex" --add-wants` produces a found/not-found report and populates `library/wants.jsonl` for any NOT FOUND entries; `markery librarian wants` lists the queue.

P3 PASSED when: `library/` exists with at least four works; per-project `references/` are citation stubs; `raw_text.txt` gitignored.

P4 PASSED when: `markery librarian extract <slug> --topics <query>` produces candidate passages; `review` appends at least one accepted passage to `excerpts.md`.

P5 PASSED when: `markery librarian --help` shows all nine subcommands; `identity.md` written with correct scope.

P6 PASSED when: `markery librarian search <query> --mode keyword` returns real passages; `index.jsonl` valid JSON-L.

P7 PASSED when: `markery librarian search "systematic record-keeping" --mode semantic` returns the Yates passage without that exact phrase; `passage_embeddings` table exists in `index.duckdb`.

P8 PASSED when: `markery librarian card <query>` ≤300 tokens with citation markers.

P9 PASSED when: all MVO tests pass; D020 closed.

Phase PASSED when P1–P9 all pass.

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
