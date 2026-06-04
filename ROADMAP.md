# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.
Phases 14–15 closed 2026-06-01/2026-05-24. Archived to `archive/ROADMAP-2026-06-03.md`.

---

## Phase 16 — Wikipedia Account Building and Early Radio Project

**Trigger:** Phase 15 complete.  
**Scope:** Two independent workstreams. Track A closes the deferred Wikipedia Stage 4c/4d edits (D023, D024) by first building the account to five non-reverted mainspace edits — the blocking condition confirmed 2026-06-01. Track B launches `radio-pioneers`, a second research project on early American radio manufacturers (1920–1940), as a live end-to-end test of the full Markery pipeline.

**Goal state:** D023 and D024 live on Wikipedia; `radio-pioneers` has confirmed pairs, at least one validated essay, a working site build, and radio-domain secondary literature in the LIBRARIAN corpus.

---

### Track A — Wikipedia

---

### P1 — Four mainspace edits (account threshold)

Current state: account `CosmoGSpacely` has 3 confirmed non-reverted mainspace edits (Stage 4b external link 2026-05-22; Library Bureau CN fix 2026-06-02; Library Bureau absorption citation 2026-06-03). Two more required before D023 can be submitted. Edits must be spaced across days — one per day minimum.

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

### Track B — Early Radio Project — CLOSED

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

### P5 — Patent and trademark acquisition — CLOSED

1. Run trademark sweeps for each entity's variants. Identify which serials are already in `trademarks.duckdb` and which require TSDR enrichment via `markery trademark fetch`.
2. Run patent sweeps for CPC classes `H04B`, `H01J`, `H03F`, `H04R` over 1918–1940 via EPO OPS. If coverage is thin (radio CPC classes may be outside the current data window), document in `RESEARCH-AGENDA.md` as a scope note.
3. Run `markery patent signals` for any unreviewed patents in the candidate pool to populate abstract text.
4. Gate: ≥10 trademark records and ≥20 patent records in scope; no sweep errors.

---

### P6 — Candidate generation, first review cycle, and token baseline — CLOSED

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

### P7 — LIBRARIAN: secondary literature for radio domain — CLOSED

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

### P8 — Site build, Haiku essay test, and phase close — CLOSED

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

P8 PASSED when: `markery site build radio-pioneers` exits 0; one Wikipedia draft written; Haiku essay test result recorded; `tests/benchmarks/README.md` updated with radio-pioneers section. — PASSED 2026-06-03 (site build: 12 pages; Haiku essay: sterilamp-us2168861a PASS 6/6, 2,006p/922c tokens; Wikipedia draft: rca-patent-pool-manufacturing-split.md; README updated with full radio-pioneers token summary)

Phase PASSED when P1–P8 all pass.

---

## Phase 16.1 — Animal Marks: Second Example Project

**Trigger:** Phase 16 Track B complete. Track A (P1–P3) continues in parallel.  
**Scope:** A second end-to-end example project, purpose-built to surface further CLI bypasses, harden Haiku-native operation, and test project structure flexibility. The research domain — early American technology company trademarks containing animal imagery, filed 1930 or earlier — was chosen to differ structurally from radio-pioneers in three ways: (1) trademark-first discovery using design search codes rather than entity-first setup; (2) targeted per-assignee patent retrieval rather than broad CPC sweeps; (3) a richer research question (why did an engineering company put an animal in its mark?) that drives both the LIBRARIAN corpus and the Wikipedia contribution.

**Goal state:** A fully working `animal-marks-1930` project with confirmed pairs, validated essays, a site build, and secondary literature indexed. All API operations run on `claude-haiku-4-5-20251001` as the primary model — not as a test but as operational practice. Every CLI bypass encountered is logged to DEFERRED; every new D-entry updates Phase 17 P3.

**Haiku-native commitment:** Set `MARKERY_MODEL=claude-haiku-4-5-20251001` at the start of P1 and leave it set for the entire phase. There is no separate "Haiku simulation" step — Haiku is the model, Sonnet is not used. If a step fails on Haiku, document the failure mode and the minimum model tier, then continue.

**Known anticipated gap (D034):** No `markery trademark design-search` CLI command exists. Mark discovery in P1 will require a direct DuckDB query against the `design_search` table. Log as D034 on first occurrence.

---

### P1 — Animal marks discovery and project setup

The discovery path here is trademark-first: find the marks, then identify the entities — the reverse of how `radio-pioneers` was set up. This tests whether the matchmaker's entity-first assumption is a bottleneck for a different class of research question.

1. Query `trademarks.duckdb` directly: join `design_search` (codes beginning `03.` — USPTO animal category), `case_file` (filing date ≤ 1930-12-31), and `statement` (goods text containing technology keywords: electrical, motor, engine, apparatus, machine, radio, telephone, automobile, tool). Identify 4–6 entities with the most research-worthy animal-mark / technology-goods correspondence. Note the direct DB query as a D034 bypass — there is no `markery trademark design-search` command.
2. For each selected entity, identify which assignee name variants to use in `variants.csv`. Run `markery matchmaker suggest-variants` for each.
3. Run `markery project init animal-marks-1930` if the command exists (D027); otherwise scaffold manually and log the bypass.
4. Write `projects/animal-marks-1930/entities.csv`, `variants.csv`, `RESEARCH.md` (central argument: what does an animal communicate in a technology brand, and what does it tell us about the company's market positioning?), `RESEARCH-AGENDA.md` (candidate pairs to investigate; open questions about specific animal choices).
5. Set `MARKERY_MODEL=claude-haiku-4-5-20251001` — record it here as the operational model for all subsequent steps.

---

### P2 — Trademark enrichment and entity qualification

1. Run `markery trademark enrich-project animal-marks-1930` (or `markery trademark fetch <serial>` for each in-scope serial) to populate `extended_marks` with goods descriptions and mark images.
2. Run `markery matchmaker build --data-dir projects/animal-marks-1930` to load entities and variants.
3. Run `markery matchmaker validate-variants --data-dir projects/animal-marks-1930` to confirm all variant strings match actual DB records. Fix any zero-match variants before proceeding.
4. Qualify each entity: must have ≥1 animal-mark serial with technology goods in `extended_marks`. Entities that fail this check are removed from `entities.csv` — document the removal in `RESEARCH-AGENDA.md`.

---

### P3 — Targeted patent acquisition

The CPC sweep approach used in `radio-pioneers` returned +0 for pre-1940 patents in several classes. Here, use a narrower per-assignee strategy:

1. For each entity: run a targeted query to see what patents are already in `patents.duckdb` for that assignee name. Many large pre-1930 manufacturers will have some coverage from earlier sweeps.
2. For any entity with zero patents in DB: use `markery patent pull <patent_no>` for 2–3 known patents sourced from Google Patents or TSDR filing cross-references. Avoid broad CPC sweeps unless `markery patent coverage-check` returns > 0 for a class.
3. Run `markery patent signals animal-marks-1930` to populate abstract text for any candidates in the DB.
4. Gate: ≥5 patents total across all entities; ≥1 patent per entity that has a confirmed trademark in scope.

---

### P4 — Candidate generation and Haiku-native review

1. Run `markery matchmaker generate animal-marks-1930`.
2. Run `MARKERY_TOKEN_LOG=tests/benchmarks/animal-marks-p4.jsonl markery historian digest animal-marks-1930 --tokens`. Haiku is the operational model — no special framing.
3. Run `markery historian card animal-marks-1930 <slug> --tokens` for the top candidates. Target ≥3 confirmed pairs across ≥2 entities.
4. Note: the D031 `class_score` domain-specificity issue applies here too. Document whether the top-scoring candidates are genuinely strong or coincidental temporal proximity (as in radio-pioneers). Log any new scoring anomalies.
5. Write `confirmed.jsonl` entries. Note whether D029 (`markery matchmaker confirm`) is triggered.
6. `markery historian scaffold animal-marks-1930 <slug>` for each confirmed pair; expand essays (using Haiku as the drafting model — i.e., test `historian draft` preview if Phase 18 P5 is not yet implemented, note D030 bypass); run `markery historian validate animal-marks-1930 <slug>`.
7. Record all token counts. Flag any operation that Haiku cannot complete correctly.

---

### P5 — LIBRARIAN: secondary literature on animal imagery in American trademarks

The research question — why did a technology company choose an animal mark? — requires historical context that the patent/trademark DBs cannot provide.

1. Run `markery librarian discover --wikipedia "trademark" --add-wants` and `--wikipedia "Brand management"` to surface citation leads.
2. Run `markery librarian search-sources "trademark history" --source ia` and `"American advertising history" --source ia`. Target at least one open-access work covering pre-1930 American brand design or trademark practice.
3. Acquire confirmed open-access works with `markery librarian acquire`.
4. Run `markery librarian extract <slug> --topics "animal" "trademark" "brand" "advertising" "symbol" --tokens`. If using `--auto-accept`, note D032 bypass; if using interactive `review`, note terminal requirement.
5. Run `markery librarian index --embed`.
6. Load a context card before any essay session: `markery librarian card "animal trademark technology" --mode semantic`.

---

### P6 — Publisher, Wikipedia contribution, and phase close

1. Run `markery site build animal-marks-1930` and verify exit 0.
2. Identify the strongest Wikipedia contribution. The "why animal" angle is well-suited to adding cited context to a company or trademark article that currently lacks it. Write the draft to `projects/animal-marks-1930/wikipedia/`.
3. Append an `animal-marks-1930` section to `tests/benchmarks/README.md`: token summary (digest, card, extract, essay), confirmation that Haiku completed all steps, and a note on any steps that required fallback or correction.
4. D-number audit: list every new CLI bypass found during this phase. Verify each is in DEFERRED with a reopen trigger. Update Phase 17 P3 "Known gaps" section.

---

### Phase Gate

P1 PASSED when: `projects/animal-marks-1930/` scaffolded; ≥4 entities identified via design-search query; `MARKERY_MODEL` set to Haiku; D034 logged if design-search CLI is absent. — PASSED 2026-06-03 (5 entities: Mack Trucks/bulldog, Pratt&Whitney/eagle, Eagle Electric/eagle, Pathé/rooster, Albert Setzer MULE/mule; D034 logged — design_search queried via raw DuckDB; D027 triggered — project init crashes non-interactively, scaffolded manually; MARKERY_MODEL=claude-haiku-4-5-20251001 committed in RESEARCH.md)

P2 PASSED when: `validate-variants` exits 0 for all entities in scope; each entity has ≥1 animal-mark serial with technology goods in `extended_marks`. — PASSED 2026-06-04 (18/18 entities enriched via `markery trademark enrich`; all 18 qualify with technology goods confirmed from `statement` table; D038 logged — `enrich` stores raw JSON only, structured fields remain NULL; `enrich-project` inapplicable pre-candidates)

P3 PASSED when: ≥5 patents in `patents.duckdb` for animal-marks-1930 entities; `patent signals` run.

P4 PASSED when: ≥3 confirmed pairs in `confirmed.jsonl`; all pass `historian validate`; token counts in `tests/benchmarks/animal-marks-p4.jsonl`; all operations completed on Haiku (or failures documented).

P5 PASSED when: ≥1 secondary work indexed with passages relevant to animal mark symbolism; `markery librarian card "animal trademark" --mode semantic` returns ≥1 passage.

P6 PASSED when: `markery site build animal-marks-1930` exits 0; Wikipedia draft written; `tests/benchmarks/README.md` updated; all new DEFERRED entries confirmed present with reopen triggers.

Phase PASSED when P1–P6 all pass.

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

**Known gaps from Phase 16.1 P1 expansion (verify and test):**
These were discovered during the animal-marks-1930 entity expansion from 5 to 18 entities.
- D035 (CSV comma-in-name mis-parse): `markery matchmaker build` silently accepted a malformed `variants.csv` row where an unquoted comma in the variant name was parsed as a field delimiter; entity 16 (Pathé) appeared to build successfully but was never displayed by `validate-variants`. The "All variants matched" summary was misleading. Verify D035 is in DEFERRED with the corrected description.
- D036 (`trademark mark-status`): finding dead marks required two raw `case_file.cfh_status_cd` DuckDB queries — one to filter the candidate pool, one to verify the final 15-dead/3-live breakdown. No CLI command can report trademark status for marks in a project's scope. Verify D036 is in DEFERRED.
- D037 (`matchmaker clear`): after the D035 CSV bug corrupted entity 16, recovery required raw DuckDB `DELETE` statements. The `build` command is idempotent-add-only; there is no remove path. Verify D037 is in DEFERRED.

**Known gaps from Phase 16.1 P2:**
- D038 (`enrich` structured-fields): `markery trademark enrich` stores raw TSDR JSON but leaves `mark_text`, `status_cd`, `goods_desc`, `owner_name` NULL. P2 qualification fell back to `statement` table (goods) and `case_file.cfh_status_cd` (status) because `extended_marks` had no parsed data despite successful enrichment. Verify D038 is in DEFERRED.
- `enrich-project` reads from `confirmed.jsonl` or `candidates.jsonl` — neither exists at P2 stage. No CLI path to batch-enrich project-scoped marks before candidate generation. Logged here; promote to DEFERRED if recurs in a third project.

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
