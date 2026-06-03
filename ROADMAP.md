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

### P1 — Prove blocking conditions — CLOSED

Satisfy D020 conditions before writing a line of specialist code. This is manual work — the acquisitions tooling built in P2 will automate future corpus growth, but the format must be proven first with hand-curated content.

1. Populate real excerpts in `information-systems/references/` for at least two works. Yates (*Control Through Communication*) and Cortada (*Before the Computer*) both have IA-borrow access via their `ia_identifier` fields. Each passage block must have a verbatim quotation with page number and a context note. Stub `<!-- Add passage -->` comments do not count.
2. Create `projects/monthly-image-review/references/` with at least one work relevant to that project's scope — a history of American industrial tool design marks, Chicago Pneumatic's industry context, or branding in the 1920s–1930s manufacturing sector. Follow the format in `information-systems/references/README.md`.
3. In `projects/monthly-image-review/references/README.md`, name one specific passage in `information-systems/references/` that this project's historian would use — documenting the cross-project retrieval need concretely.
4. Commit all reference files. Verify: both directories have at least one work with real (non-stub) passage sections.

P1 PASSED — 2026-05-31. Yates and Cortada stubs are borrow-only and remain as stubs; two open-access public domain works added instead: Galloway (1918, `officemanagement00gall`, open) with 3 verbatim passages (pp. 146, 153–154, 164) and Leffingwell (1917, `scientificoffice00leff`, open) with 3 verbatim passages (pp. v, 58, 160). `monthly-image-review/references/` created with Leffingwell (different passage set, manufacturing-company focus). README documents cross-project need: Galloway pp. 153–154 from information-systems is required for monthly-image-review context.

---

### P2 — Source adapters and acquisition CLI — CLOSED

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

### P3 — Library structure and migration — CLOSED

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

### P4 — Claude-assisted passage extraction — CLOSED

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

P4 PASSED — 2026-05-31. Cortada is borrow-only (no raw_text.txt); verified with `galloway-office-management` instead — 5 candidates produced including a direct Remington Rand Visible Index Card File passage (p. 103) not previously in excerpts.md. `--tokens` confirmed (86,313 prompt / 2,614 completion tokens, 40 chunks, Haiku). `candidates.md` added to `.gitignore`.

---

### P5 — LIBRARIAN persona and CLI scaffold — CLOSED

1. Create `src/markery/specialist/librarian/` with `__init__.py`, `cli.py`, `sources/` package, `persona/identity.md`, `persona/instructions/`.
2. Write `identity.md`: LIBRARIAN owns `library/` (reads and writes); reads `projects/*/references/` (citation stubs only); never touches DuckDB, candidates, or confirmed records; never modifies project `content/` or `site/`. Acquisition commands (fetch from external sources) are within scope.
3. Register `markery librarian` in the top-level CLI dispatcher.
4. Verify: `markery librarian --help` shows: `search-sources`, `discover`, `wants`, `wants-update`, `acquire`, `enter`, `raw-text`, `extract`, `review`, `index`, `search`, `list`, `card`.

P5 PASSED — 2026-05-31. `persona/identity.md` written with full scope, source priority, and explicit limits. `persona/instructions/` created with three cards: `acquire.md`, `extract.md`, `wants.md`. `markery librarian --help` confirms all nine implemented subcommands (`index`, `search`, `list`, `card` are P6–P8 scope).

---

### P6 — Keyword index and search — CLOSED

1. Implement `markery librarian index [--rebuild]`: parses all `library/works/*/excerpts.md`; extracts passage records (`work_slug`, `author`, `title`, `year`, `section`, `passage`, `context`); writes `library/index.jsonl`. The `--rebuild` flag forces a full reparse; default is incremental (only reindexes works whose `excerpts.md` is newer than the index entry).
2. Implement `markery librarian search <query> [--top N] [--mode keyword|semantic|both]`: in `keyword` mode, case-insensitive substring match across passage + section + context; returns ranked matches with citation and passage preview.
3. Implement `markery librarian list [--verbose]`: one line per work (slug, author, year, excerpt count, raw text present/absent).
4. Add `--tokens` flag to `search` and `list`.
5. Verify: `markery librarian search "card index" --mode keyword` returns at least one passage.

P6 PASSED — 2026-06-01. `index.py` implemented with incremental/rebuild logic; `index.jsonl` has 7 valid records across Galloway (3) and Leffingwell (4). `markery librarian search "card index" --mode keyword` returns 5 passages. `list` shows all 5 works with excerpt counts and raw-text status. Semantic/both modes fall back to keyword with warning (P7 scope).

---

### P7 — Semantic (vector) search — CLOSED

1. Add `sentence-transformers` (`all-MiniLM-L6-v2`) to optional dependencies in `pyproject.toml` under `[project.optional-dependencies]` as `librarian = ["sentence-transformers>=2.2"]`. Do not require it for base install.
2. Extend `markery librarian index` with `--embed` flag: for each passage in `index.jsonl`, compute an embedding vector and store it in `library/index.duckdb` — table `passage_embeddings (work_slug TEXT, passage_id INT, embedding FLOAT[])`. Incremental: only embeds passages not already in the table.
3. Implement `markery librarian search <query> --mode semantic [--top N]`: embeds the query with the same model; loads all embeddings from `library/index.duckdb`; computes cosine similarity with numpy; returns top N passages ranked by similarity. Falls back to keyword mode with a warning if embeddings have not been built.
4. `--mode both`: runs keyword and semantic in parallel, merges results (deduplicated by passage_id), re-ranks by a weighted combination (default: 0.4 keyword presence + 0.6 semantic similarity).
5. Document the model choice in `library/README.md`: why `all-MiniLM-L6-v2`, how to substitute an API-based provider, the DuckDB embedding table schema.
6. Verify: `markery librarian search "systematic record-keeping" --mode semantic` returns the Yates passage about filing infrastructure even when "systematic record-keeping" does not appear verbatim.

P7 PASSED — 2026-06-01. Yates has no real passages (borrow-only stub); verified with Galloway instead: "The filing department has been called a systematized memory" ranks #1 for "systematic record-keeping" — correct semantic hit with no verbatim match. `passage_embeddings` table present in `index.duckdb` (7 embeddings, 384-dim MiniLM-L6-v2). Incremental re-run skips all 7 (already embedded). `--mode both` working. `library/index.duckdb` added to `.gitignore`.

---

### P8 — Historian context card — CLOSED

1. Implement `markery librarian card <query> [--top N] [--mode keyword|semantic|both]`: compact output (≤300 tokens) for loading into a historian session. Format per match: `[Author (Year)] Section — "passage text" (p. XX).`
2. `--out -` for stdout; default saves to `library/cards/<query-slug>.md`.
3. `--tokens` flag.
4. Verify: `markery librarian card "Remington Rand filing" --mode semantic` produces output ≤300 tokens containing at least one citation bracket.

P8 PASSED — 2026-06-01. `card "Remington Rand filing" --mode semantic` produces 258 tokens (estimated), 5 passages, all with `[Surname (Year)]` citation brackets. Default mode is semantic (falls back to keyword if embedding index absent). Passage text truncated at 120 chars to stay within token budget. `library/cards/` gitignored.

---

### P9 — Tests, MVO contracts, and D020 close — CLOSED

1. Write `tests/test_librarian.py`: unit tests using `tmp_path` fixtures with synthetic library content (3 works, 5 passages each). Cover: `index` record structure; keyword search returns correct passage; semantic search returns passage (mock embeddings — patch `sentence-transformers` call); `list` enumerates works; `card` ≤300 tokens with citation markers; `extract` calls Claude with expected prompt structure (mock API); `acquire` creates correct directory structure (mock HTTP).
2. Add LIBRARIAN to `tests/benchmarks/mvo.md`: contracts for `search`, `list`, `card`, `index`.
3. All tests pass.
4. Mark D020 resolved in `DEFERRED.md`.

P9 PASSED — 2026-06-01. 42 tests pass (7 index, 6 keyword search, 6 semantic search, 4 list, 4 card, 3 extract, 2 acquire unit tests; 10 MVO CLI tests). LIBRARIAN contracts added to `tests/benchmarks/mvo.md`. D020 closed in `DEFERRED.md`.

---

### Phase Gate

P1 PASSED when: two projects have `references/` with real excerpts; cross-project retrieval need documented.

P2 PASSED when: `markery librarian acquire` successfully fetches a work from IA; `search-sources` returns results for a known query; `markery librarian discover --wikipedia "Soundex" --add-wants` produces a found/not-found report and populates `library/wants.jsonl` for any NOT FOUND entries; `markery librarian wants` lists the queue.

P3 PASSED when: `library/` exists with at least four works; per-project `references/` are citation stubs; `raw_text.txt` gitignored.

P4 PASSED when: `markery librarian extract <slug> --topics <query>` produces candidate passages; `review` appends at least one accepted passage to `excerpts.md`.

P5 PASSED when: `markery librarian --help` shows all nine subcommands; `identity.md` written with correct scope. — PASSED

P6 PASSED when: `markery librarian search <query> --mode keyword` returns real passages; `index.jsonl` valid JSON-L. — PASSED

P7 PASSED when: `markery librarian search "systematic record-keeping" --mode semantic` returns the Yates passage without that exact phrase; `passage_embeddings` table exists in `index.duckdb`. — PASSED

P8 PASSED when: `markery librarian card <query>` ≤300 tokens with citation markers. — PASSED

P9 PASSED when: all MVO tests pass; D020 closed. — PASSED

Phase PASSED when P1–P9 all pass. — PASSED 2026-06-01

---

## Phase 16 — Wikipedia Account Building and Early Radio Project

**Trigger:** Phase 15 complete.  
**Scope:** Two independent workstreams. Track A closes the deferred Wikipedia Stage 4c/4d edits (D023, D024) by first building the account to five non-reverted mainspace edits — the blocking condition confirmed 2026-06-01. Track B launches `radio-pioneers`, a second research project on early American radio manufacturers (1920–1940), as a live end-to-end test of the full Markery pipeline.

**Goal state:** D023 and D024 live on Wikipedia; `radio-pioneers` has confirmed pairs, at least one validated essay, a working site build, and radio-domain secondary literature in the LIBRARIAN corpus.

---

### Track A — Wikipedia

---

### P1 — Four mainspace edits (account threshold)

Current state: account `CosmoGSpacely` has 1 confirmed non-reverted mainspace edit (Stage 4b external link, 2026-05-22). Four more required before D023 can be submitted. Space edits across ≥10 days — one per day minimum.

1. **Library Bureau — resolve `{{Citation needed}}`**: The sentence "It sold merchandise and services through a network of sales offices and distributors in the United States (46 in 1922), England (4), France (1), and Belgium." carries a `{{Citation needed|date=June 2023}}` tag. The 1921 Library Bureau catalog (Google Books, already linked in the article's References section) documents the office network. Add `<ref>{{cite book|title=Steel Card and Filing Cabinets|publisher=Library Bureau|year=1921|url=https://books.google.com/books?id=nkhIAAAAYAAJ&pg=PA1}}</ref>` after "Belgium"; remove the tag.

2. **Library Bureau — add absorption citation**: The lead sentence "In 1927, it was absorbed into Remington Rand" is uncited. The Los Angeles Times advertisement of June 21, 1927 (already cited as a reference in the article) announces Remington Rand's formation and names Library Bureau among its business services. Add it as an inline `<ref>` on that sentence.

3. **Rolodex — Wheeldex trademark citation**: The article states Rolodex "was an improvement to an earlier design called the *Wheeldex*" without sourcing the Wheeldex name. The USPTO trademark record for WHEELDEX (Serial No. 71321669, Scholfield Service, Inc.) is a primary source. Add one sentence: "The Wheeldex name was registered as a United States trademark by Scholfield Service, Inc. (USPTO Serial No. 71321669)." with a TSDR `<ref>`.

4. **Remington Rand or another domain article — citation or housekeeping**: After completing edits 1–3, identify the single best unsourced factual claim in the Remington Rand article or another article in the domain that the USPTO record or LIBRARIAN corpus directly supports. Make a genuine improvement — do not save this slot for a strategically motivated edit.

---

### P2 — D023: Chicago Pneumatic inline citation

Prerequisite: ≥5 confirmed non-reverted mainspace edits.

1. Confirm Stage 4b TSDR external link still live on the "Chicago Pneumatic" article.
2. Using `markery wikipedia` tooling, fetch current wikitext, insert at confirmed insertion point (after 1925 oil-well drilling paragraph, before 1939 impact wrench paragraph):
   ```wikitext
   The CP monogram design trademark (USPTO Serial No. 71299042) was filed on April 18, 1930, covering pneumatic tools, air compressors, and related apparatus.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71299042&caseType=SERIAL_NO&searchType=statusSearch|title=Trademark Serial No. 71299042|publisher=USPTO Trademark Status and Document Retrieval|access-date=2026-06-01}}</ref>
   ```
3. Review diff; submit with summary: "Add primary source citation for CP monogram trademark (USPTO Serial 71299042, April 1930)"
4. Monitor ≥48 hours; record edit URL in `projects/monthly-image-review/STATUS.md`.

Full draft and pre-submission checklist: `projects/monthly-image-review/wikipedia/d023-inline-citation.md`.

---

### P3 — D024: Soundex article

Prerequisite: D023 live ≥48 hours unreverted.

1. Fetch current Soundex article to confirm 1918 patent is still cited and trademark sentence is absent.
2. Insert trademark-only sentence after the 1922 patent sentence (before "A variation, American Soundex..."):
   ```wikitext
   The SOUNDEX trademark (USPTO Serial No. 71246709) was filed on March 31, 1927, by Rand Kardex Bureau, Inc., covering index cards and forms for phonetic indexing systems.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71246709&caseType=SERIAL_NO&searchType=statusSearch|title=Trademark Serial No. 71246709 — SOUNDEX|publisher=USPTO Trademark Status and Document Retrieval|access-date=2026-06-01}}</ref>
   ```
3. Edit summary: "Add primary source citation for SOUNDEX trademark filing (USPTO 71246709, 1927, Rand Kardex Bureau)"
4. Monitor ≥48 hours; record edit URL in `projects/information-systems/STATUS.md`.

Attribution basis: RAND KARDEX BUREAU, INC. confirmed as filing-date owner in `data/trademarks.duckdb`; see `projects/information-systems/RESEARCH.md §SOUNDEX Ownership Timeline`. Full draft: `projects/information-systems/wikipedia/d024-soundex-draft.md`.

---

### Track B — Early Radio Project

---

### P4 — Project setup: `radio-pioneers` — CLOSED

Target domain: early American radio manufacturers, 1920–1940. Vacuum tube patents, receiver circuit patents, and broadcast equipment patents map cleanly to branded product names. The RCA patent pool (GE, Westinghouse, AT&T, RCA as joint licensors) means that product trademarks are the primary evidence of each company's distinct commercial activity — patent ownership was pooled and cross-licensed, but brand names were proprietary.

Initial entity set:

| ID | Entity | Key trademark strings |
|---|---|---|
| 1 | Radio Corporation of America | RADIOLA, RADIOTRON, SUPERHETERODYNE |
| 2 | Westinghouse Electric and Manufacturing Company | RADIOPHONE, AERIOLA |
| 3 | Atwater Kent Manufacturing Company | ATWATERKENT |
| 4 | Zenith Radio Corporation | ZENITH |
| 5 | De Forest Radio Company | AUDION, OSCILLION |

CPC patent classes to sweep: `H04B` (radio transmission), `H01J` (vacuum tubes), `H03F` (amplifiers), `H04R` (loudspeakers, receiver components).

1. Create `projects/radio-pioneers/` with standard directory structure: `entities.csv`, `variants.csv`, `matches/`, `content/`, `site/`, `references/`.
2. Write `entities.csv` (IDs 1–5) and `variants.csv` with the trademark search strings above.
3. Write `projects/radio-pioneers/RESEARCH.md`: central argument and scope note on the patent pool structure and why trademarks are the primary evidence of commercial identity.
4. Write `projects/radio-pioneers/RESEARCH-AGENDA.md`: candidate confirmed pairs to investigate (De Forest AUDION vacuum tube patent + AUDION trademark; RCA transmitter patents + RADIOLA marks; Zenith early marks).

---

### P5 — Patent and trademark acquisition

1. Run trademark sweeps for each entity's variants. Identify which serials are already in `trademarks.duckdb` and which require TSDR enrichment via `markery trademark fetch`.
2. Run patent sweeps for CPC classes `H04B`, `H01J`, `H03F`, `H04R` over 1918–1940 via EPO OPS. If coverage is thin (radio CPC classes may be outside the current data window), document in `RESEARCH-AGENDA.md` as a scope note.
3. Run `markery patent signals` for any unreviewed patents in the candidate pool to populate abstract text.
4. Gate: ≥10 trademark records and ≥20 patent records in scope; no sweep errors.

---

### P6 — Candidate generation, first review cycle, and token baseline

1. Run `markery matchmaker generate radio-pioneers` to populate `candidates.jsonl`.
2. Run historian commands with token logging enabled:
   ```
   MARKERY_TOKEN_LOG=tests/benchmarks/radio-pioneers-p6.jsonl \
     markery historian digest radio-pioneers --tokens
   ```
   Then for each card reviewed:
   ```
   MARKERY_TOKEN_LOG=tests/benchmarks/radio-pioneers-p6.jsonl \
     markery historian card radio-pioneers <slug> --tokens
   ```
3. Review top-scoring candidates. Target ≥3 confirmed pairs across ≥2 entities.
4. **Haiku simulation:** after reviewing at least 3 candidates, run the Phase 14 P4 test harness against radio-pioneers data — load the digest + cards as context and send to `claude-haiku-4-5-20251001`. Verify: no hallucinated serial or patent numbers; response is structurally coherent. Record pass/fail and token counts in `tests/benchmarks/radio-pioneers-p6.jsonl`.
5. Aggregate the log: record mean prompt tokens for digest and card in `tests/benchmarks/README.md` alongside the Phase 14 baseline (digest=251, card=188 post-P3). Flag any command whose radio-pioneers count exceeds the baseline by >20% — that is a regression signal, not a gate failure, but it must be investigated before P8.
6. For each confirmed pair: `markery historian scaffold radio-pioneers <slug>`, expand manually, then `markery historian validate radio-pioneers <slug>`. All confirmed essays must pass validate.

---

### P7 — LIBRARIAN: secondary literature for radio domain

Key works to acquire (verify IA open-access before requesting):

| Work | Notes |
|---|---|
| Gleason Archer, *History of Radio to 1926* (1938) | Contemporary account covering RCA formation and patent pool |
| W. Rupert Maclaurin, *Invention and Innovation in the Radio Industry* (1949) | Business history of the patent-to-product pipeline; directly relevant to confirmed-pair methodology |
| Erik Barnouw, *A Tower in Babel* (1966) | Standard scholarly history of American broadcasting |

1. Run `markery librarian discover --wikipedia "Radio Corporation of America" --add-wants` to surface citations.
2. Run `markery librarian search-sources "radio history" --source ia` to find open-access texts.
3. Acquire confirmed open-access works with `markery librarian acquire`.
4. Run `markery librarian extract <slug> --topics "RCA" "RADIOLA" "patent pool" "vacuum tube" --tokens` on acquired texts. `extract` calls `claude-haiku-4-5-20251001` directly — record the prompt and completion token counts. Append results to `tests/benchmarks/radio-pioneers-p6.jsonl`. Run `markery librarian review` to accept relevant passages.
5. Run `markery librarian index --embed`.
6. Load a context card in the first historian session: `markery librarian card "radio receiver patents" --mode semantic`.

---

### P8 — Site build, Haiku essay test, and phase close

1. **Haiku essay test:** Take the scaffold for one confirmed pair and attempt a complete draft using `claude-haiku-4-5-20251001` as the session model. Run `markery historian validate radio-pioneers <slug>` on the result. Record: pass/fail, any fields that required manual correction, and completion token count. This is the open question left from Phase 14 P4 — Haiku was validated for card/digest but not for full essay generation.
2. Write at least one full validated essay (Haiku draft or manual expansion — whichever passes validate).
3. Run `markery site build radio-pioneers` and verify the site renders without error.
4. Create `projects/radio-pioneers/wikipedia/` with a draft file for the strongest Wikipedia contribution identified during the review cycle. Do not submit — save for a future phase.
5. Append a `radio-pioneers` section to `tests/benchmarks/README.md`: token summary table (digest, card, extract, essay), Haiku simulation result, and comparison to Phase 14 baseline.

---

### Phase Gate

P1 PASSED when: account `CosmoGSpacely` has ≥5 confirmed non-reverted mainspace edits; all four new edits are in articles within the research domain.

P2 PASSED when: D023 live on Wikipedia ≥48 hours unreverted; edit URL recorded in `projects/monthly-image-review/STATUS.md`.

P3 PASSED when: D024 live on Wikipedia ≥48 hours unreverted; edit URL recorded in `projects/information-systems/STATUS.md`.

P4 PASSED when: `projects/radio-pioneers/entities.csv`, `variants.csv`, and `RESEARCH.md` all exist. — PASSED 2026-06-02

P5 PASSED when: ≥10 trademark records and ≥20 patent records in scope; sweep complete without errors. — PASSED 2026-06-03 (10 TM records: RCA 3, Zenith 7; 2,885+ radio patents for RCA alone; 2,748 candidates generated; CPC coverage gaps for Zenith/De Forest documented in RESEARCH-AGENDA.md)

P6 PASSED when: ≥3 confirmed pairs in `confirmed.jsonl`; all pass `historian validate`; token counts recorded in `tests/benchmarks/radio-pioneers-p6.jsonl`; Haiku simulation pass/fail recorded. — PASSED 2026-06-03 (3 pairs: STERILAMP/Westinghouse, MINALITE/Westinghouse, VICTOR/RCA; all validate PASS; digest=249, card=195 tokens avg — within 5% of P14 baseline; Haiku simulation PASS, no hallucinations)

P7 PASSED when: ≥2 radio secondary works indexed; `markery librarian card "radio receiver" --mode semantic` returns at least one passage; `extract` token counts recorded. — PASSED 2026-06-03 (3 works acquired: Archer 1939 9 passages, Barnouw 1966 5 passages, Taussig 1922 4 passages; 25 total indexed passages, 18 new embeddings; card returns 5 passages; extract tokens: Archer 26,001p/2,986c, Barnouw 45,127p/3,595c, Taussig 64,981p/3,128c)

P8 PASSED when: `markery site build radio-pioneers` exits 0; one Wikipedia draft written; Haiku essay test result recorded; `tests/benchmarks/README.md` updated with radio-pioneers section.

Phase PASSED when P1–P8 all pass.

---

## Phase 17 — PatentsView Bulk Import, Documentation, and Code Gap Analysis

**Trigger:** Phase 16 complete.  
**Scope:** Patent data infrastructure (D007) and a holistic documentation and code-quality pass covering Phases 14–17 additions. D023 and D024 have moved to Phase 16.

**Goal state:** By phase close, `markery patent bulk-import` is implemented and tested; all top-level and specialist documentation reflects Phase 14–17 work; `DEFERRED.md` is fully current; D007 is closed.

---

### P1 — PatentsView bulk import (D007)

Full design is in `src/markery/specialist/patent/BULK_CSV.md`. Implement as specified there.

1. Implement `markery patent bulk-import download --year-start YEAR --year-end YEAR --out-dir PATH`: downloads the required PatentsView `.tsv.gz` files (`g_patent`, `g_assignee_disambiguated`, `g_cpc_current`) for the specified year range. Files are large; command must show progress and resume safely if interrupted.
2. Implement `markery patent bulk-import load --tsv-dir PATH --classes CPC [CPC ...] [--year-start YEAR] [--year-end YEAR]`: reads the `.tsv.gz` files with DuckDB `read_csv()` and predicate pushdown; constructs `patent_no` as `US{number}{kind}`; inserts into `patents` and `patent_classes` tables using insert-if-not-exists (idempotent against the existing EPO-sourced schema).
3. Verify schema compatibility: bulk-imported rows must pass the same queries that EPO-sourced rows pass. `app_dt` will be NULL for bulk-imported rows — document this in `BULK_CSV.md` and confirm no existing query hard-requires it.
4. Test against a narrow scope: one CPC class (`B42F`), year range 1976–1985. Confirm row counts match manual PatentsView query. Confirm no duplicate `patent_no` collisions with EPO-sourced rows in that range.
5. Add `markery patent bulk-import status --tsv-dir PATH`: reports row counts in the `.tsv.gz` files before load (sanity check before committing to a multi-hour import).

---

### P2 — Documentation pass

Review all user-facing and developer-facing documentation for staleness and gaps introduced across Phases 14–17. Update only what has drifted or is missing.

**Top-level docs:**
1. `README.md` — verify it reflects current capabilities; update the command inventory if any commands added in Phases 14–17 are absent; confirm the setup instructions still work end-to-end.
2. `DESIGN.md` — check whether the model-agnosticism section accurately describes the Phase 14 token instrumentation, Phase 15 LIBRARIAN embedding approach, and Phase 16 radio project structure; add any new architectural patterns.
3. `SETUP.md` — confirm all new optional dependencies (`sentence-transformers`, `anthropic`) are documented with install instructions and purpose.
4. `CONTEXT.md` — update the "what exists" summary to reflect the LIBRARIAN specialist, bulk-import capability, and `radio-pioneers` project.

**Specialist docs:**
5. Each specialist's `identity.md` — verify scope sections are current for any commands added in Phases 14–17.
6. Instruction cards (`persona/instructions/`) — audit against implemented commands. Any command reachable via `markery <specialist> --help` that has no instruction card is a gap. Create stub cards; note which require full content.
7. `src/markery/specialist/patent/BULK_CSV.md` — update with implementation decisions made during P1 (actual column mappings, `app_dt` NULL behavior, schema deviations from the design doc).

**Benchmark docs:**
8. `tests/benchmarks/README.md` — add a Phase 17 section noting the bulk-import command's token profile and confirming the Phase 14 baseline is still valid after bulk-import rows are added.

---

### P3 — Code gap analysis

Audit the full codebase for incomplete implementation, missing test coverage, and deferred items that Phase 14–17 work may have made satisfiable.

**Known gaps from Phase 16 P5 (address first):**
These were discovered during the radio-pioneers live-test and implemented as immediate hardening; verify they are complete and tested before broader audit.
- `matchmaker build` entity ID collision detection — silent skip when ID exists with different name was the root cause of radio-pioneers data corruption
- `markery matchmaker validate-variants <project>` — zero-match variant detection against actual DB strings
- `markery patent coverage-check` — dry-run EPO query to surface zero-coverage CPC classes before committing to a full sweep
- D027 (`project onboard`) and D028 (`trademark search-tsdr`) are in DEFERRED; promote here if a third project setup hits the same gaps

**Known gaps from Phase 16 P6 (verify and test):**
These were discovered during the radio-pioneers candidate review and Haiku simulation.
- D029 (`matchmaker confirm`): Phase 16 P6 wrote to `confirmed.jsonl` directly because no non-interactive CLI path exists — `markery review` requires a raw-mode terminal. Verify D029 is in DEFERRED with correct reopen trigger.
- D030 (`historian simulate`): Phase 16 P6 ran the Haiku simulation as an inline Python script (`/tmp/radio_haiku_sim.py`) rather than a CLI command. Verify D030 is in DEFERRED. No P6-equivalent test should be hand-scripted again.
- D031 (`class_score` domain specificity): `PRODUCT_CLASSES` in `score.py` hardcodes information-systems CPC classes. For radio-pioneers, G09F (display/advertising) patents scored 0.3 higher than H01J (vacuum tubes) and H04B (radio) patents with identical date proximity — the top-scoring candidates were cross-product-line coincidences, not genuine matches. Fix design is in D031; verify it is correctly specified before audit is complete.

**Known gaps from Phase 16 P7 (verify and test):**
These were discovered during the radio-pioneers secondary literature acquisition.
- D032 (`librarian review --auto-accept`): Phase 16 P7 wrote `excerpts.md` directly for all three acquired works because `markery librarian review` is interactive (terminal-bound) and `--auto-accept` only exists on `extract` (which would repeat expensive API calls). No CLI path exists to accept an already-generated `candidates.md` non-interactively. Verify D032 is in DEFERRED.
- D033 (`librarian index` format validation): Phase 16 P7 initially wrote `excerpts.md` with `##` headings; the indexer requires `###`. `markery librarian index --rebuild` reported success ("8 work(s)") with zero new passages and gave no warning. The mismatch was discovered only by manually checking record counts. Verify D033 is in DEFERRED.

**Implementation gaps:**
1. Grep for `TODO`, `FIXME`, `HACK`, `raise NotImplementedError`, and `pass` in `src/`. Classify each as: (a) intentional stub, (b) known gap already in `DEFERRED.md`, or (c) newly discovered. Add (c) items to `DEFERRED.md` with a reopen trigger.
2. Cross-reference all subcommands in every specialist's `--help` output against `cli.py`. Any subcommand registered but not dispatched is a gap.
3. Check `markery historian prepare` — verify instruction cards reflect the current output format.

**Test coverage gaps:**
4. Run `python -m pytest --co -q` and compare collected tests against the full command inventory. Any command with zero test coverage gets a DEFERRED entry.
5. Check `tests/benchmarks/mvo.md` — verify every contract row has a corresponding test in `tests/test_mvo.py`.

**Schema and data gaps:**
6. Document any data-quality constraints that Phase 17 P1 exposed: `app_dt` NULL for bulk-imported patents, assignee disambiguation differences between EPO OPS and PatentsView.
7. Check whether the `assignment` table (queried during the SOUNDEX ownership research in Phase 16) is populated. If not, add a DEFERRED entry for assignment data import.

**DEFERRED.md hygiene:**
8. Review every open DEFERRED entry. Confirm reopen triggers are still valid; close any silently met during Phases 14–17; update stale path or command references.

---

### P4 — Tests, cleanup, and close

1. Add `markery patent bulk-import` to `tests/benchmarks/mvo.md`: contract for `status` (prints row counts, exits 0) and `load` (idempotent on re-run — no duplicate rows on second load of same data).
2. Write `tests/test_bulk_import.py`: test `status` against a synthetic fixture `.tsv.gz` (10-row subset); test `load` inserts expected rows and is idempotent. No real PatentsView download required.
3. Mark D007 resolved in `DEFERRED.md` with a note on test scope and the `app_dt`-NULL constraint.

---

### Phase Gate

P1 PASSED when: `markery patent bulk-import load` runs without error on B42F/1976–1985; row counts match PatentsView; no duplicate collisions with EPO-sourced rows.

P2 PASSED when: all docs reviewed; instruction card gaps filed as DEFERRED or filled; `BULK_CSV.md` updated.

P3 PASSED when: `DEFERRED.md` updated with all newly discovered gaps; every open entry has a valid reopen trigger; no command in `--help` output is unimplemented without a DEFERRED entry.

P4 PASSED when: bulk-import MVO tests pass; D007 marked resolved in `DEFERRED.md`.

Phase PASSED when P1–P4 all pass.

---

## Phase 18 — Shared Data Contract: Markery-ICM Preparation for Markery-LangGraph

**Trigger:** Phase 17 complete; Markery-LangGraph repo initiated.  
**Scope:** Any changes Markery-ICM requires to make the shared data contract between the two repos formal, stable, and documented. This phase exists entirely in service of the companion repo. No new specialist features; no new research capabilities. If Phase 17's code gap analysis (P3) surfaces contract-relevant gaps, they are promoted here.

**What Markery-LangGraph depends on (the contract):**
- DuckDB schemas for `patents.duckdb`, `trademarks.duckdb`, `entities.duckdb`
- JSONL record shapes for `candidates.jsonl`, `confirmed.jsonl`, `rejected.jsonl`
- Essay frontmatter keys in `projects/<name>/content/*.md`
- `library/index.jsonl` passage record shape and `library/index.duckdb` embedding schema (Phase 15)
- Score field semantics (structural + semantic ceiling; 0.80 cap)

Full architecture decision and repo relationship documented in `archive/GITHUB-REVIEW-2026-05-25.md`; `CONTRACT.md` supersedes that document as the authoritative interface definition once written.

---

### P1 — Contract audit

Identify every data shape the companion repo will consume and verify each is explicitly documented somewhere in Markery-ICM.

1. Enumerate all files the contract covers (DuckDB tables, JSONL records, markdown frontmatter, library index). For each: locate the existing documentation (schema DDL, identity.md scope, README, or inline comment). Flag any shape with no authoritative documentation.
2. Review DuckDB schemas for runtime stability: any column that a query outside Markery-ICM might depend on must have a documented type and nullable constraint. Columns used only internally can remain undocumented.
3. Review JSONL record shapes: `candidates.jsonl` and `confirmed.jsonl` field sets have grown organically. Document the canonical field list and mark which fields are guaranteed-present vs. optional.
4. Review essay frontmatter: verify the seven required keys (`title`, `trademark_serial`, `trademark`, `tm_filing_dt`, `patent_no`, `patent_grant_dt`, `entity`) are enforced by `historian validate` and documented as the stable interface.
5. Output: a `CONTRACT.md` at repo root listing each contract surface, its format, and a pointer to the authoritative schema definition.

---

### P2 — Schema hardening

Fix any gaps the P1 audit surfaces. No new features — only documentation, light enforcement, and stability fixes.

1. For any undocumented DuckDB column that the companion repo will need: add a `-- contract: <type>, <nullable>` comment to the DDL or a schema note in the relevant specialist's design doc.
2. For any JSONL field that is present in some records but not others without documentation: add it to the canonical field list with `optional: true` and document the condition under which it appears.
3. For any essay frontmatter key that `historian scaffold` does not currently write: either add it to scaffold output or remove it from the contract.
4. Verify `historian validate` enforces all seven required frontmatter keys. If any key passes validate despite being absent or malformed, fix the check.

---

### P3 — CONTRACT.md and version marker

1. Write `CONTRACT.md` at repo root: one section per contract surface (DuckDB tables, JSONL files, essay frontmatter, library index). Each section: field name, type, nullable, guaranteed-present or optional, example value, and a one-line description of its purpose for a Markery-LangGraph node consuming it.
2. Add a `contract_version` field to `data/` or a `MANIFEST.json` at repo root (e.g., `{"contract_version": "1.0", "markery_version": "0.3.0"}`). Markery-LangGraph reads this at startup to verify compatibility. Increment on any breaking contract change.

---

### P4 — Integration smoke test

Verify that a minimal Markery-LangGraph node can read all contract surfaces without error.

1. Write `tests/test_contract.py`: for each contract surface, assert the expected fields are present in a real data record from the `information-systems` project. This test does not depend on LangGraph — it validates that Markery-ICM's output matches what `CONTRACT.md` promises.
2. Run against `information-systems` corpus. All assertions pass.
3. Add `test_contract` to the MVO job in `ci.yml` (runs under `workflow_dispatch` only, same as `test_mvo`).

---

---

### P5 — Historian inference mode (Level 2)

**Prerequisite:** P1–P4 complete. The data contract must be stable before adding inference on top of it — inference mode reads the same surfaces the contract defines, and the contract tests (P4) serve as the regression suite.

**Goal:** Give historian commands the ability to call Claude directly with `--infer`, so the full card-review and candidate-assessment workflow can run without a human-driven Claude Code session. This is the bridge to Markery-LangGraph.

**Design constraint:** `--infer` mode must work with any model reachable via `MARKERY_MODEL`. It must not assume Claude-specific output formatting. The existing `--tokens` flag applies automatically to all `--infer` calls.

1. Add `--infer [--model MODEL]` to `markery historian card <project> <slug>`:
   - Load the card context document (existing output)
   - Send to the API: system prompt = `persona/identity.md` (condensed); user prompt = card context + assessment request
   - Parse response into a structured result: `{"recommendation": "confirm|reject|defer", "score": 1–5, "reasoning": "..."}`
   - Print result; append token record to `MARKERY_TOKEN_LOG` if set
   - `--model` overrides `MARKERY_MODEL` for this call only

2. Add `--infer` to `markery historian digest <project>`:
   - After generating the digest document, send it to the API with the question: "Which candidates are most worth reviewing first and why?"
   - Append the model's ranked recommendation list below the digest output
   - Token count appended to log

3. Add `markery historian draft <project> <slug> [--model MODEL]`:
   - New command: takes an existing scaffold and calls the API to produce a first-draft essay
   - Output written to `content/<slug>-draft.md` (distinct from the final `<slug>.md` to avoid overwriting human work)
   - Immediately run `historian validate` on the draft; print PASS/FAIL alongside token counts
   - This is the primary test of whether a given model can complete the full essay workflow end-to-end

4. Verify on radio-pioneers: run `historian card --infer` on ≥3 candidates with `MARKERY_MODEL=claude-haiku-4-5-20251001`; run `historian draft` on one confirmed pair; record validate result.

---

### P6 — Token efficiency and model-agnostic hardening

**Goal:** Close the gap between the model-agnosticism principle (documented in DESIGN.md) and the reality of how sessions run. After P5, every API-calling path in Markery goes through a single configurable model. This phase makes that configuration robust and reduces per-call cost.

**Prompt caching** (highest ROI):
1. Add `cache_control: {"type": "ephemeral"}` to the system prompt block in `librarian extract` and the new historian inference calls. Persona content (`identity.md`) is identical across all calls in a session — it is the canonical cache candidate. Measure the cache hit rate via `cache_read_tokens` in `MARKERY_TOKEN_LOG`. Target: ≥80% cache hit rate on repeated calls within a session.
2. Document the caching behaviour in `DESIGN.md`: what is cached, what is not, and why (cache TTL is 5 minutes — sessions longer than 5 minutes between calls will miss).

**Context budget control**:
3. Add `MARKERY_CONTEXT_BUDGET` env var (integer, token count). When set, historian commands that assemble context — `digest`, `card` — truncate their output to stay within budget. Default: 4000 (sized for Haiku's cost-efficient range). Higher values allow richer context on larger models without code changes.
4. Verify: set `MARKERY_CONTEXT_BUDGET=2000`, run `historian digest radio-pioneers`, confirm output fits the budget. Set to 8000, confirm more candidates are included.

**Multi-model MVO validation**:
5. Extend the existing MVO test job in `ci.yml` with a `model-matrix` step: run all MVO contracts with `MARKERY_MODEL=claude-haiku-4-5-20251001` and `MARKERY_MODEL=claude-sonnet-4-6`. Both must pass. This is the continuous proof that the output contracts are model-agnostic, not just token-efficient.
6. Record the first multi-model MVO run results in `tests/benchmarks/README.md`: a model-comparison table (command, Haiku tokens, Sonnet tokens, both pass/fail).

**Provider abstraction** (forward-looking, minimal):
7. Extract the `anthropic.Anthropic` client construction from `extract.py` and the new inference calls into a shared `common/llm.py` module: `get_client() -> client`, `call(model, system, user, max_tokens) -> (text, prompt_tokens, completion_tokens)`. The implementation calls Anthropic; the interface is generic enough that a second implementation (OpenAI-compatible, Gemini) could be dropped in by changing one file. Do not implement any second provider — define the abstraction only.

---

### Phase Gate

P1 PASSED when: every contract surface has located documentation; gaps are listed.

P2 PASSED when: all documented gaps are resolved; `historian validate` enforces all required frontmatter keys.

P3 PASSED when: `CONTRACT.md` exists at repo root; `MANIFEST.json` has `contract_version`.

P4 PASSED when: `tests/test_contract.py` passes against `information-systems`; test added to CI mvo job.

P5 PASSED when: `historian card --infer` returns structured recommendation on radio-pioneers data with Haiku; `historian draft` produces an essay that passes `historian validate` (or fails with a documented reason); token counts logged.

P6 PASSED when: prompt cache hit rate ≥80% on repeated extract calls; `MARKERY_CONTEXT_BUDGET` respected by digest and card; MVO contracts pass on both Haiku and Sonnet; `common/llm.py` abstraction in place.

Phase PASSED when P1–P6 all pass. Markery-LangGraph repo may begin after this gate.
