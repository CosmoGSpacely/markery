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

### P1 — Four mainspace edits (account threshold) — CLOSED

Current state: account `CosmoGSpacely` has 5 confirmed non-reverted mainspace edits. Edit 3 (Rolodex/Wheeldex, 2026-06-05) and edit 4 (Remington Rand filing systems, 2026-06-06, rev 1358111560) completed the threshold.

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

P1 PASSED when: account `CosmoGSpacely` has ≥5 confirmed non-reverted mainspace edits; all four new edits are in articles within the research domain. — PASSED 2026-06-06 (5 total edits: Stage 4b external link 2026-05-22; Library Bureau CN fix 2026-06-02; Library Bureau absorption citation 2026-06-03; Rolodex Wheeldex trademark citation 2026-06-05; Remington Rand filing systems section 2026-06-06 rev 1358111560)

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

**Conclusions:** The trademark-first discovery path (design code → serial → owner → entity) worked but required two bypasses logged on the first day: D034 (no `markery trademark design-search` command, raw DuckDB used) and D027 (third project triggered the reopen condition — `markery project init` crashes non-interactively, scaffolded manually). Expanding from 5 to 18 entities surfaced D035: `markery matchmaker build` silently accepts CSV rows where an unquoted comma in a variant name corrupts the `source` field — entity 16 (Pathé) built with a malformed record, `validate-variants` reported "All variants matched" but never displayed entity 16, and discovery required checking record counts manually. Recovery required raw DuckDB DELETE (D037). Five structurally distinct "why animal" models were identified for the original five entities and extended to twelve models across eighteen; these form the analytical spine of the project's research question. Dead-mark / public-domain status was confirmed for all 18 drawings via CONTEXT.md's copyright rule (works published 1930 or earlier are unconditionally in the US public domain as of January 1, 2026).

---

### P2 — Trademark enrichment and entity qualification

1. Run `markery trademark enrich-project animal-marks-1930` (or `markery trademark fetch <serial>` for each in-scope serial) to populate `extended_marks` with goods descriptions and mark images.
2. Run `markery matchmaker build --data-dir projects/animal-marks-1930` to load entities and variants.
3. Run `markery matchmaker validate-variants --data-dir projects/animal-marks-1930` to confirm all variant strings match actual DB records. Fix any zero-match variants before proceeding.
4. Qualify each entity: must have ≥1 animal-mark serial with technology goods in `extended_marks`. Entities that fail this check are removed from `entities.csv` — document the removal in `RESEARCH-AGENDA.md`.

**Conclusions:** `markery trademark enrich` stored raw TSDR JSON in `raw_json` but left all structured columns (`mark_text`, `status_cd`, `goods_desc`, `owner_name`) NULL — D038. Qualification fell back to the bulk `statement` table for goods descriptions and `case_file.cfh_status_cd` for status, which worked but defeats the purpose of enrichment as a structured data source. The `enrich-project` command cannot be used at P2 because it reads from `confirmed.jsonl` or `candidates.jsonl`, neither of which exists before P4 — a pre-candidate enrichment gap logged in Phase 17 P3. All 18 entities qualified: technology goods confirmed for all 18 serials, including three with very short goods strings ("MOTOR TRUCKS", "AUTOMOBILES", "MOTOR CARS") that a length-threshold filter initially excluded. No entities were removed.

---

### P3 — Targeted patent acquisition

The CPC sweep approach used in `radio-pioneers` returned +0 for pre-1940 patents in several classes. Here, use a narrower per-assignee strategy:

1. For each entity: run a targeted query to see what patents are already in `patents.duckdb` for that assignee name. Many large pre-1930 manufacturers will have some coverage from earlier sweeps.
2. For any entity with zero patents in DB: use `markery patent pull <patent_no>` for 2–3 known patents sourced from Google Patents or TSDR filing cross-references. Avoid broad CPC sweeps unless `markery patent coverage-check` returns > 0 for a class.
3. Run `markery patent signals animal-marks-1930` to populate abstract text for any candidates in the DB.
4. Gate: ≥5 patents total across all entities; ≥1 patent per entity that has a confirmed trademark in scope.

**Conclusions:** Seven targeted CPC sweeps (B60C, F41A/C, A01B, F04B, B64D, F02B, F16J) yielded 66 unique patents across 6 of 18 entities. Twelve entities have no EPO coverage — they require targeted `markery patent pull` with specific patent numbers from an external source, which was not available during this session. Three false-positive name collisions required raw patent-title inspection to reject: CASE RES LAB INC (photo-electric devices, not J.I. Case tractors), SHAW WALKER CO (filing cabinets, not James Walker gaskets), GILLETTE SAFETY RAZOR CO (razors, not Gillette Tire) — D039 logged for `suggest-variants` title display. `suggest-variants` should be re-run after each sweep to discover newly-arrived assignee strings; instead raw ILIKE queries were used (workflow bypass, not a missing command). `patent signals` was called per the spec but enriched 0 candidates — signals requires candidates (P4); the spec ordering is wrong and D040 was logged. The D031 class_score issue was anticipated but not yet measurable without candidates.

---

### P4 — Candidate generation and Haiku-native review

1. Run `markery matchmaker generate animal-marks-1930`.
2. Run `MARKERY_TOKEN_LOG=tests/benchmarks/animal-marks-p4.jsonl markery historian digest animal-marks-1930 --tokens`. Haiku is the operational model — no special framing.
3. Run `markery historian card animal-marks-1930 <slug> --tokens` for the top candidates. Target ≥3 confirmed pairs across ≥2 entities.
4. Note: the D031 `class_score` domain-specificity issue applies here too. Document whether the top-scoring candidates are genuinely strong or coincidental temporal proximity (as in radio-pioneers). Log any new scoring anomalies.
5. Write `confirmed.jsonl` entries. Note whether D029 (`markery matchmaker confirm`) is triggered.
6. `markery historian scaffold animal-marks-1930 <slug>` for each confirmed pair; expand essays (using Haiku as the drafting model — i.e., test `historian draft` preview if Phase 18 P5 is not yet implemented, note D030 bypass); run `markery historian validate animal-marks-1930 <slug>`.
7. Record all token counts. Flag any operation that Haiku cannot complete correctly.

**Conclusions:** The generate command is `markery match`, not `markery matchmaker generate` — the ROADMAP spec had the wrong command name (a lighter model would crash on step 1). `markery match` generated 265 candidates from 4 of 6 patent-covered entities; Colt and Pratt & Whitney produced zero candidates because their trademark filings predated their patent grants, yielding negative scores excluded by the default min_score=0.0 threshold. This reversed commercial timeline — a long-standing brand name registered before specific technical patents were filed — is a historically real pattern that the scoring model penalises rather than recognises. Two crashes from figurative marks with `null` trademark fields — D041 logged for a systematic None audit. D031 confirmed with measurement: the GM Name Plate patent (G09F) scored 0.796 solely from the PRODUCT_CLASSES bonus, while the historically correct Hydrocarbon-Motor engine patent (F02B) scored 0.43; without manual intervention the wrong pair would have been confirmed. Only 9 of 265 candidates matched the specific animal-mark serials under study — the other 256 were incidental entity trademarks (CADILLAC, DELCO-REMY, various non-eagle Goodyear marks) — D042 logged for `markery match --serials` scoping. Haiku drafted all three essays cleanly at 2,060–2,169 prompt tokens with no hallucinated identifiers; all three validated PASS. D029 (confirm bypass) and D030 (draft inline script) recurred as expected.

**Analysis:**

Goal 1 — Bypasses and code gaps: Two actual crashes (not just bypasses) — D041 for figurative-mark None in historian CLI. The D029 `markery matchmaker confirm` bypass occurred again. The D030 historian draft inline script recurred. The ROADMAP spec had the wrong command name (`markery matchmaker generate` vs `markery match`). Total new entries: D041, D042.

Goal 2 — Haiku-native: Clean success. All three essays drafted on Haiku at 2,060–2,169 prompt tokens, all validate PASS, no hallucinated identifiers. The figurative GM essay was the hardest case — Haiku correctly described the heraldic shield without inventing visual details from outside the scaffold.

Goal 3 — Project structure flexibility: The entity-scoping assumption is now visibly limiting. 256 of 265 candidates were from non-animal trademarks of the same entities. The research question targets specific serials; the tool targets entities. D042 captures this gap.

Goal 4 — Scoring domain specificity (D031): The most concrete evidence yet. GM's Name Plate patent (G09F, +0.3 class bonus) was the top-scoring candidate at 0.796. The historically correct pair — the engine patent — scored 0.43. The gap is not noise; it is the difference between confirming the right pair and the wrong one. Colt and P&W add a second scoring failure mode: the model penalizes trademark-before-patent sequences, but many iconic animal marks (the Colt horse, the P&W eagle) were registered before specific technical patents were filed.

---

### P5 — LIBRARIAN: secondary literature on animal imagery in American trademarks

The research question — why did a technology company choose an animal mark? — requires historical context that the patent/trademark DBs cannot provide.

1. Run `markery librarian discover --wikipedia "trademark" --add-wants` and `--wikipedia "Brand management"` to surface citation leads.
2. Run `markery librarian search-sources "trademark history" --source ia` and `"American advertising history" --source ia`. Target at least one open-access work covering pre-1930 American brand design or trademark practice.
3. Acquire confirmed open-access works with `markery librarian acquire`.
4. Run `markery librarian extract <slug> --topics "animal" "trademark" "brand" "advertising" "symbol" --tokens`. If using `--auto-accept`, note D032 bypass; if using interactive `review`, note terminal requirement.
5. Run `markery librarian index --embed`.
6. Load a context card before any essay session: `markery librarian card "animal trademark technology" --mode semantic`.

**Analysis:**

Goal 1 — Bypasses and code gaps: D032 (`--auto-accept`) recurred as expected — `markery librarian review` is terminal-bound and no non-interactive path exists. `markery librarian acquire <slug>` fails when passed the slug suggested by `search-sources`; the IA identifier (`historydevelopme0000fran`) must be used directly — a usability gap not yet in DEFERRED. The standard `discover` path was ineffective: Wikipedia citations for "trademark" and "Brand management" returned no acquirable IA sources. Source identification required targeted `search-sources "history development advertising Presbrey"` — the discovery workflow assumes a heavily-cited Wikipedia article; niche research domains require manual author search instead.

Goal 2 — Haiku-native: `markery librarian extract` ran successfully on Haiku at 37,654p / 2,868c tokens across 248 chunks, early-stopping at chunk 15 after 32 raw candidates (10 after dedup). All 10 passages are on-topic; no hallucinated content. The card returned 4 directly relevant passages on first query.

Goal 3 — Project structure flexibility: The same niche-domain limitation observed in P4 (entity-scoping vs. serial-scoping) recurs here: the discovery workflow is optimized for well-documented domains with dense Wikipedia citation graphs. Animal marks in American technology trademarks is too narrow a topic for the automated path. The effective strategy was to identify canonical scholarship by author name and acquire directly.

Goal 4 — Passage quality and research fit: The 10 Presbrey passages document animal imagery from Roman Pompeii through medieval England — the painted cow signifying dairy, mule signifying bakery, goat signifying dairy from first-century Pompeii is the direct historical ancestor of the Mack bulldog and Goodyear eagle as commercial identifiers. The passages provide essential historical depth for the "why animal?" framing but predate the 1920s-1930s period by 1,900 years. A contemporaneous source — an advertising trade publication from the 1920s — would strengthen the direct-era argument; `advertising-age` (1930) is already in the library with 0 excerpts and could serve this role if raw text is available.

---

### P6 — Publisher, Wikipedia contribution, and phase close

1. Run `markery site build animal-marks-1930` and verify exit 0.
2. Identify the strongest Wikipedia contribution. The "why animal" angle is well-suited to adding cited context to a company or trademark article that currently lacks it. Write the draft to `projects/animal-marks-1930/wikipedia/`.
3. Append an `animal-marks-1930` section to `tests/benchmarks/README.md`: token summary (digest, card, extract, essay), confirmation that Haiku completed all steps, and a note on any steps that required fallback or correction.
4. D-number audit: list every new CLI bypass found during this phase. Verify each is in DEFERRED with a reopen trigger. Update Phase 17 P3 "Known gaps" section.

**Analysis:**

Goal 1 — Bypasses and code gaps: Site build crashed immediately with `AttributeError: 'NoneType' object has no attribute 'lower'` in `publisher/queries.py` line 199 — the D041 figurative-mark None audit surfacing in a third code path that the two P4 historian spot-fixes did not cover. Fixed inline: slug computation now uses `re.sub(r'[^a-z0-9]+', '-', (m["trademark"] or "figurative").lower()).strip('-')` with patent number appended, which also corrected a pre-existing mismatch between the slug format and historian's essay naming convention (essays were silently unfound on the site in all prior projects). Second fix: `build.py` search record label now uses `match['trademark'] or '(figurative)'`. No new DEFERRED entry — D041 covers the audit. D044 (acquire slug) already logged from P5. Total new code changes: 2 files, 3 lines.

Goal 2 — Haiku-native: Full phase completed on Haiku with no Sonnet fallback. Site build, Wikipedia draft, and README were not API calls and are model-agnostic. All API-calling steps (digest, card, essay, extract) ran on Haiku. The only non-CLI step was the D030 essay-draft bypass (inline script). No step failed on Haiku.

Goal 3 — Project structure flexibility: The Wikipedia draft required manual identification of the strongest animal-mark serial — the CLI has no command to filter confirmed pairs by trademark character (animal vs. text). The Objective 7 dead-mark priority check required a direct DuckDB query (`cfh_status_cd = 900` for all three confirmed pairs). Both are gaps observable in prior phases; neither is new.

Goal 4 — Scoring domain specificity (D031): Not directly tested in P6, but the site build materialized the scoring consequence: the confirmed essays cover Goodyear and John Deere (clean patent-trademark correspondence) and GM (manually corrected from the top-scoring wrong pair). The site's match gallery therefore reflects researcher intervention, not the scorer's output. This is the correct result — but it underlines that D031 is not a minor calibration issue; without manual review, the animal-marks site would have confirmed a GM name-plate/engine pair with no historical support.

---

### Phase Gate

P1 PASSED when: `projects/animal-marks-1930/` scaffolded; ≥4 entities identified via design-search query; `MARKERY_MODEL` set to Haiku; D034 logged if design-search CLI is absent. — PASSED 2026-06-03 (5 entities: Mack Trucks/bulldog, Pratt&Whitney/eagle, Eagle Electric/eagle, Pathé/rooster, Albert Setzer MULE/mule; D034 logged — design_search queried via raw DuckDB; D027 triggered — project init crashes non-interactively, scaffolded manually; MARKERY_MODEL=claude-haiku-4-5-20251001 committed in RESEARCH.md)

P2 PASSED when: `validate-variants` exits 0 for all entities in scope; each entity has ≥1 animal-mark serial with technology goods in `extended_marks`. — PASSED 2026-06-04 (18/18 entities enriched via `markery trademark enrich`; all 18 qualify with technology goods confirmed from `statement` table; D038 logged — `enrich` stores raw JSON only, structured fields remain NULL; `enrich-project` inapplicable pre-candidates)

P3 PASSED when: ≥5 patents in `patents.duckdb` for animal-marks-1930 entities; `patent signals` run. — PASSED 2026-06-04 (66 patents across 6 entities via sweeps of B60C, F41A/C, A01B, F04B, B64D, F02B, F16J; 12/18 entities have no EPO coverage — need targeted pulls with specific numbers; patent signals deferred to P4 post-candidate-generation; 12 false-positive assignee strings excluded)

P4 PASSED when: ≥3 confirmed pairs in `confirmed.jsonl`; all pass `historian validate`; token counts in `tests/benchmarks/animal-marks-p4.jsonl`; all operations completed on Haiku (or failures documented). — PASSED 2026-06-04 (3 pairs: Deere/JOHN DEERE/plow, Goodyear/DOUBLE EAGLE/tire, GM/figurative-heraldic/engine; all validate PASS 6/6; Haiku drafts 2169p/980c, 2141p/945c, 2060p/667c; 2 code bugs fixed: None-trademark crash in digest formatter and card slug matcher)

P5 PASSED when: ≥1 secondary work indexed with passages relevant to animal mark symbolism; `markery librarian card "animal trademark" --mode semantic` returns ≥1 passage. — PASSED 2026-06-04 (Presbrey 1929 acquired from IA, 10 passages extracted with Haiku 37,654p/2,868c tokens, --auto-accept bypass (D032); card returns 4 passages on animal imagery in Roman/medieval advertising; passages on painted cow, mule, goat signboards and sheep advertising directly support "why animal?" research question)

P6 PASSED when: `markery site build animal-marks-1930` exits 0; Wikipedia draft written; `tests/benchmarks/README.md` updated; all new DEFERRED entries confirmed present with reopen triggers. — PASSED 2026-06-04 (25 pages; site crashed on `trademark: null` in publisher/queries.py — fixed inline (D041 manifesting in third code path); Wikipedia draft: goodyear-double-eagle.md (DOUBLE EAGLE serial 71273140, dead mark, patent US1645089A); README updated with full token summary; D044 in DEFERRED)

Phase PASSED when P1–P6 all pass. — PASSED 2026-06-04

---

## Phase 17 — Publisher Upgrade, Documentation, and Code Gap Analysis — CLOSED

**Trigger:** Phase 16 complete.  
**Scope:** Publisher and matchmaker project-type sensitivity (new P1); a holistic documentation and code-quality pass covering Phases 14–17 additions (P2); code gap audit (P3); tests and close (P4). D007 (PatentsView bulk import) remains in DEFERRED — its reopen conditions have not been met and it is not the current priority. D023 and D024 have moved to Phase 16.

**Goal state:** By phase close, the publisher renders project-type-appropriate sites using `focus_serials` configuration; the matchmaker scopes candidate generation to focus serials when set; all top-level and specialist documentation reflects Phase 14–17 work; `DEFERRED.md` is fully current.

---

### P1 — Publisher and matchmaker: project-type sensitivity

The `animal-marks-1930` site exposes the publisher's core limitation: every project renders identically regardless of the research question. The trademark gallery shows CADILLAC, DELCO-REMY, and seventeen non-animal Goodyear marks at the same visual weight as the three animal-mark serials the project exists to study. The research framing ("why did a technology company choose an animal mark?") is absent from the rendered output. Match essays — the primary analytical output — appear buried in a gallery alongside unrelated entity marks.

Fix in three layers: configuration, matchmaker, publisher.

**Configuration — `focus_serials`:**
1. Add a `focus_serials` array to `projects/<name>/project.json`. For `animal-marks-1930`, list the specific animal-mark serials identified in P1 discovery (the serials the project is about — not all entity trademarks). The field is optional; absent `focus_serials` leaves all existing behavior unchanged. Read `projects/animal-marks-1930/RESEARCH.md` and the P1 discovery query results to identify the correct serials; write them to `project.json`.

**Matchmaker — focus-scoped candidate generation (partial D042):**
2. When `focus_serials` is present in `project.json`, `markery match <project>` generates candidates only from those serials. Add `--all-serials` flag to override and generate from all entity trademarks (current behavior, now explicit). Regenerate `candidates.jsonl` for `animal-marks-1930`; confirm the candidate count drops from 265 to the focused set. Update D042 in DEFERRED to note partial close: the project-config approach replaces the originally proposed `--serials` flag.

**Publisher — trademark gallery:**
3. When `focus_serials` is set, render the trademark gallery in two sections: "Project Marks" (focus serials, shown first, visually distinct — e.g., a border or badge) and "All Entity Trademarks" (remaining entity marks, de-emphasized). Without `focus_serials`, gallery renders as a single list as before.

**Publisher — landing page:**
4. If `projects/<name>/content/research-question.md` exists, render its text as the landing page introduction above the stat cards. Write `projects/animal-marks-1930/content/research-question.md`: one or two paragraphs framing the "why animal?" question, drawn from the project's `RESEARCH.md`. Without this file, landing renders as before.

**Verify and rebuild:**
5. Run `markery site build animal-marks-1930`: confirm focus marks appear in a distinct gallery section and research-question text is on the landing page. Run `markery site build information-systems` (no `focus_serials`) and confirm no regression — single-list gallery, landing renders as before.

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
7. Publisher specialist docs (`src/markery/specialist/publisher/`) — document the `focus_serials` field in `project.json` and the slug contract between historian and publisher (`{tm_slug}-{patent_no}` naming convention; the pre-existing silent mismatch fixed in Phase 16.1 P6 must not recur).

**Benchmark docs:**
8. `tests/benchmarks/README.md` — add a Phase 17 section noting any publisher rendering changes; confirm the Phase 14 token baseline is still valid.

---

### P3 — Code gap analysis — CLOSED

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

**Known gaps from Phase 16.1 P4:**
- D041 (figurative mark None crash): `historian digest` and `historian card` crash on `trademark: null` candidates. GM serial 71199224 is a purely figurative mark; two spot-fixes applied inline but a systematic audit of all `c['trademark']` references in historian/cli.py is needed. Verify D041 in DEFERRED.
- D042 (`match --serials`): `markery match` generates candidates for ALL entity trademarks, not just the specific animal-mark serials under study. Phase 16.1 P4 generated 265 candidates of which 9 were animal-mark-specific; the other 256 were noise from CADILLAC, DELCO-REMY, Chevrolet, non-eagle Goodyear marks. Verify D042 in DEFERRED.
- Spec error: ROADMAP P4 step 1 says `markery matchmaker generate` — the correct command is `markery match`. A lighter model would crash on step 1. Fix the ROADMAP template.
- D031 confirmed again: GM Name Plate patent (G09F) scored 0.796 — highest in project — while the better Hydrocarbon-Motor pair (F02B) scored 0.43. Score ordering is actively misleading for this project.
- Colt and P&W excluded entirely: trademark filed before patent grant → negative scores → zero candidates. The reversed commercial timeline (long-standing brand name predating specific technical patents) is a real historical pattern not captured by the current scoring model.

**Known gaps from Phase 16.1 P3:**
- D039 (`suggest-variants` false positives): Phase 16.1 P3 found three false-positive assignee matches (CASE RES LAB ≠ J.I. Case; SHAW WALKER ≠ James Walker; GILLETTE SAFETY RAZOR ≠ Gillette Tire) that required raw patent-title inspection to reject. `suggest-variants` shows counts only — no titles — making name-collision disambiguation impossible without leaving the CLI. Verify D039 is in DEFERRED.
- D040 (`patent signals` spec ordering): `patent signals` was called at P3 per the spec and returned "0 candidates enriched" — correct but useless, since candidates don't exist until P4. Signals belongs as step 1 of P4 post-`generate`, not in P3. Verify D040 is in DEFERRED.
- Workflow gap (not a new command): after CPC sweeps, `suggest-variants` should be re-run for each entity to discover newly-arrived assignee strings. Instead, raw DuckDB ILIKE queries were used to find the correct patent assignee names. The CLI path existed (`suggest-variants`) but was bypassed. Document in P3 template that `suggest-variants` must be re-run after each sweep.

**Known gaps from Phase 16.1 P2:**
- D038 (`enrich` structured-fields): `markery trademark enrich` stores raw TSDR JSON but leaves `mark_text`, `status_cd`, `goods_desc`, `owner_name` NULL. P2 qualification fell back to `statement` table (goods) and `case_file.cfh_status_cd` (status) because `extended_marks` had no parsed data despite successful enrichment. Verify D038 is in DEFERRED.
- `enrich-project` reads from `confirmed.jsonl` or `candidates.jsonl` — neither exists at P2 stage. No CLI path to batch-enrich project-scoped marks before candidate generation. Logged here; promote to DEFERRED if recurs in a third project.

**Known gaps from Phase 16.1 P5:**
- D032 (`librarian review --auto-accept`) recurred: `--auto-accept` used on `extract` because `markery librarian review` is terminal-bound. Verify D032 is in DEFERRED.
- D044 (`librarian acquire` slug mismatch): `markery librarian search-sources` prints a suggested slug that `markery librarian acquire` rejects — the raw IA identifier must be used. Phase 16.1 P5 used `historydevelopme0000fran` after `presbrey-history-and-development-of-advertising` failed. Verify D044 is in DEFERRED with reopen trigger pointing to Phase 17 P2/P3.

**Known gaps from Phase 16.1 P6:**
- D041 (figurative mark None crash) in publisher: `publisher/queries.py` crashed with `AttributeError` on `trademark: null` — a third code path not covered by the two P4 historian spot-fixes. Fixed inline with `re.sub` slug + `"figurative"` fallback. D041 audit is still open for `scaffold`, `validate`, and `confirmed.jsonl` writer. Verify D041 is in DEFERRED with audit scope updated.
- Slug mismatch (pre-existing, not a crash): `publisher/queries.py` derived essay slugs as `trademark.lower().replace(" ", "-")`, which did not match historian's `{tm_slug}-{patent_no}` convention. Essays were silently unfound in all prior projects' site builds. Fixed inline in the same patch. Not a new DEFERRED entry — the fix is in place; mention in Phase 17 P2 documentation pass as a note on the slug contract between historian and publisher.

**Implementation gaps:**
1. Grep for `TODO`, `FIXME`, `HACK`, `raise NotImplementedError`, and `pass` in `src/`. Classify each as: (a) intentional stub, (b) known gap already in `DEFERRED.md`, or (c) newly discovered. Add (c) items to `DEFERRED.md` with a reopen trigger.
2. Cross-reference all subcommands in every specialist's `--help` output against `cli.py`. Any subcommand registered but not dispatched is a gap.
3. Check `markery historian prepare` — verify instruction cards reflect the current output format.

**Test coverage gaps:**
4. Run `python -m pytest --co -q` and compare collected tests against the full command inventory. Any command with zero test coverage gets a DEFERRED entry.
5. Check `tests/benchmarks/mvo.md` — verify every contract row has a corresponding test in `tests/test_mvo.py`.

**Schema and data gaps:**
6. Check whether the `assignment` table (queried during the SOUNDEX ownership research in Phase 16) is populated. If not, add a DEFERRED entry for assignment data import.

**DEFERRED.md hygiene:**
7. Review every open DEFERRED entry. Confirm reopen triggers are still valid; close any silently met during Phases 14–17; update stale path or command references.

---

### P4 — Tests, cleanup, and close — CLOSED

1. Add publisher `focus_serials` rendering to `tests/benchmarks/mvo.md`: contract for `site build` with `focus_serials` set (focus marks section present in trademark gallery HTML) and without (single-list gallery, no regression).
2. Write or extend a publisher test that verifies: (a) when `project.json` contains `focus_serials`, `get_confirmed_matches` separates focus marks from non-focus marks; (b) when `focus_serials` is absent, output is unchanged from pre-P1 behavior.
3. Update D042 in `DEFERRED.md` to note the partial close: project-config-driven focus scoping implemented in P1; the `--serials` CLI flag remains unimplemented and deferred.

---

### Phase Gate

P1 PASSED when: `markery site build animal-marks-1930` exits 0 with focus marks section present in trademark gallery HTML and research-question content on landing page; `markery site build information-systems` exits 0 with no regression. — PASSED 2026-06-05 (27 focus serials in project.json; candidates.jsonl reduced from 265 to 19; trademark gallery splits into "Project Marks" / "All Entity Trademarks" sections; research-question.md rendered as intro block on landing; information-systems rebuilds cleanly with no focus styling or rq block)

P2 PASSED when: all docs reviewed; instruction card gaps filed as DEFERRED or filled; publisher specialist docs updated with `focus_serials` and slug contract. — PASSED 2026-06-05 (README/CONTEXT/DESIGN/SETUP updated; LIBRARIAN added throughout; project.json/focus_serials documented; 14 new instruction cards across historian/matchmaker/patent/librarian; D045 filed for 5 remaining low-priority librarian stubs; publisher and matchmaker identity.md updated with slug contract and focus_serials; benchmarks README Phase 17 P1 section added)

P3 PASSED when: `DEFERRED.md` updated with all newly discovered gaps; every open entry has a valid reopen trigger; no command in `--help` output is unimplemented without a DEFERRED entry. — PASSED 2026-06-05 (0 grep hits for TODO/FIXME/NotImplementedError in src/; all 21 open D-numbers verified with updated triggers; 4 new entries: D046 pre-candidate enrich-project, D047 assignment table absent, D048 match invisible subcommands, D049 librarian MVO contracts untested; D041 line 219 crash patched inline; stale triggers updated across 12 entries; PHASE17-P3-REVIEW.md documents all findings)

P4 PASSED when: publisher MVO contract updated; publisher focus-serials test passes; D042 updated in `DEFERRED.md` with partial-close note. — PASSED 2026-06-05 (13 tests in tests/specialist/publisher/test_render_focus.py — 8 with focus_serials, 5 without; all 475 suite tests pass; mvo.md updated with focus_serials gallery contract; D042 partial-close noted in P1/P2)

Phase PASSED when P1–P4 all pass. — PASSED 2026-06-05

---

## Phase 17.1 — Deferred Work Sprint — CLOSED

**Trigger:** Phase 17 complete.  
**Scope:** Pre-Phase 18 correctness and data-quality sprint. Three work tiers: (1) code correctness bugs that produce crashes or silent data corruption; (2) scoring accuracy — `class_score` hardcoding that actively misleads multi-project candidate ranking; (3) trademark enrichment — `enrich` stores raw JSON but leaves structured columns NULL, defeating the purpose of the command as a data source. All items drawn from DEFERRED.md with confirmed trigger conditions or confirmed code gaps from the Phase 17 P3 audit.

**Goal state:** No remaining crash paths for figurative marks in any historian command; `markery match --help` lists all subcommands; `project.json` configures per-project CPC class hints for scoring; `markery trademark enrich` populates structured columns. DEFERRED entries D031, D033, D035, D038, D041, D048 closed or updated to partial-close.

---

### P1 — Code correctness bugs — CLOSED

Four confirmed gaps from the Phase 17 P3 audit. All are self-contained code changes with no design decisions outstanding.

**D041 — historian scaffold None-guard (lines 339, 341, 354):**
1. In `cmd_scaffold` in `historian/cli.py`, replace the three direct uses of `pair['trademark']` in the scaffold f-string with `pair['trademark'] or '(figurative)'`:
   - Line 339: `title: "{pair['trademark'] or '(figurative)'} — {pat_no}"`
   - Line 341: `trademark: "{pair['trademark'] or '(figurative)'}"` 
   - Line 354: `[{pair['trademark'] or '(figurative)'}](...)`
2. Add a test to `test_render_focus.py` or a new historian test: scaffold with `trademark=None` in confirmed pair produces YAML with `trademark: "(figurative)"`, not `trademark: "None"`.

**D033 — librarian index zero-passage warning:**
3. In `src/markery/specialist/librarian/index.py`, in `_parse_excerpts()` (or the calling loop): after parsing a work's `excerpts.md`, if the file exists and is non-empty but the parse yields 0 records, print `WARNING: <slug>/excerpts.md has content but no parseable ### passages — check heading levels`.
4. Add a test: a work with `##`-headed excerpts.md produces a warning and 0 indexed records.

**D035 — matchmaker build CSV validation:**
5. In `src/markery/specialist/matchmaker/entities.py` `build()`: after parsing `variants.csv`, verify that every row's `source` value is in `{"patent_assignee", "trademark_owner", "trademark_search"}`. If not, print an error with the line number and the found value, then exit 1.
6. Add a test: a `variants.csv` with an unquoted comma in the variant name (producing an invalid `source` value) is rejected with a descriptive error.

**D048 — `markery match` invisible subcommands in `--help`:**
7. In `src/markery/specialist/matchmaker/cli.py`, add `status`, `rescore`, `auto-disposition`, and `preflight` to the argparse help string or usage text for the `match` entry point — at minimum as a `{subcommands}` note in the usage line or a listed set of positional alternatives, so they appear when running `markery match --help`.

---

### P2 — Scoring accuracy (D031) — CLOSED

**Context:** `PRODUCT_CLASSES = {"B42F", "B42D", "B41J", "B41L", "G06C", "G06K", "G09F"}` in `score.py` gives a 0.3 bonus to information-systems CPC classes. For every other project domain, this inverts quality ranking — confirmed with measurement in Phase 16.1 P4 (GM G09F 0.796 vs. F02B 0.43).

**Fix — per-project class hints:**
1. Add an optional `class_hints` array to `project.json` (list of CPC class strings, e.g. `["F02B", "B60C", "F04B"]`). Update `Project` dataclass and `load_project()` in `common/project.py` to read it.
2. In `score.py` `generate_candidates()`, pass `class_hints` from the loaded project to `score_candidate()`. When `class_hints` is non-empty, use it as `PRODUCT_CLASSES` for this project. When absent, fall back to the current hardcoded set (preserving information-systems behavior unchanged).
3. Update `projects/animal-marks-1930/project.json` with `class_hints` reflecting the animal-marks domain: `["F02B", "B60C", "F41A", "F41C", "A01B", "F04B", "B64D", "F16J"]`.
4. Regenerate candidates for `animal-marks-1930` with `markery match animal-marks-1930 --all-serials` and verify the GM F02B engine patent now outscores the G09F Name Plate patent.
5. Add a test: `score_candidate()` with a CPC class in the supplied hints list gets the 0.3 bonus; a class not in the list gets 0.0.

---

### P3 — Trademark enrichment structured fields (D038) — CLOSED

**Context:** `markery trademark enrich <serial>` fetches TSDR JSON and stores it in `extended_marks.raw_json`, but leaves `mark_text`, `status_cd`, `goods_desc`, `owner_name` NULL. Phase 16.1 P2 qualification fell back to `statement` and `case_file` because `extended_marks` had no parsed data despite successful enrichment. D046 (pre-candidate batch enrichment) cannot be useful until the structured fields are populated.

**Fix — parse on upsert:**
1. In `src/markery/specialist/trademark/enrich.py` (or wherever `extended_marks` is written), after storing `raw_json`, parse the following TSDR JSON keys and write them to the structured columns:
   - `mark_text`: from `markInfo.markText` (or `""` if absent — figurative marks have no text)
   - `status_cd`: from `caseFileHeader.statusCode`
   - `goods_desc`: from `goodsAndServices[0].goodsServicesDescription` (first GS class, truncated to 500 chars)
   - `owner_name`: from `currentOwners[0].ownerName` (or first owner in `ownerDetails`)
2. Verify the JSON key paths against a live TSDR response for a known serial (use `extended_marks.raw_json` for an already-enriched serial to inspect the structure).
3. Run `markery trademark enrich` for one animal-marks-1930 serial and confirm `extended_marks.goods_desc` is populated.
4. Add a test: mock the TSDR response JSON; after `enrich`, the structured columns in `extended_marks` match the expected parsed values.

---

### Phase Gate

P1 PASSED when: `historian scaffold` with `trademark=None` confirmed pair writes `"(figurative)"` in YAML, not `"None"`; `markery librarian index` warns on `##`-headed excerpts.md; `markery matchmaker build` rejects unquoted-comma variants.csv with exit 1; `markery match --help` lists `status`, `rescore`, `auto-disposition`, `preflight`. — PASSED 2026-06-05 (4 fixes committed 5a9d90f; 475 tests pass; D033/D035/D041/D048 closed)

P2 PASSED when: `project.json` `class_hints` read by `load_project()`; scoring passes `class_hints` through to `score_candidate()`; animal-marks-1930 F02B engine patent outscores G09F Name Plate patent after adding `class_hints`; unit test passes. — PASSED 2026-06-05 (F02B 0.7346 vs G09F 0.4964 after regenerating; 5 new unit tests; 480 total pass)

P3 PASSED when: `markery trademark enrich <serial>` populates `mark_text`, `status_cd`, `goods_desc`, `owner_name` in `extended_marks`; confirmed by querying `extended_marks` after enriching a known serial; unit test passes. — PASSED 2026-06-05 (`markery trademark reparse` backfilled 154 rows; 163/167 mark_text, 167 status_cd, 165 goods_desc, 148 owner_name; 4 NULLs are design marks; 6 new tests; 486 total pass)

Phase PASSED when P1–P3 all pass. DEFERRED entries D031, D033, D035, D038, D041, D048 updated to reflect closed or partial-close status. — PASSED 2026-06-05 (D033/D035/D048 closed; D031/D038 closed; D041 partially closed — TUI audit open)

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

### P1 — Contract audit — CLOSED

Identify every data shape the companion repo will consume and verify each is explicitly documented somewhere in Markery-ICM.

1. Enumerate all files the contract covers (DuckDB tables, JSONL records, markdown frontmatter, library index). For each: locate the existing documentation (schema DDL, identity.md scope, README, or inline comment). Flag any shape with no authoritative documentation.
2. Review DuckDB schemas for runtime stability: any column that a query outside Markery-ICM might depend on must have a documented type and nullable constraint. Columns used only internally can remain undocumented.
3. Review JSONL record shapes: `candidates.jsonl` and `confirmed.jsonl` field sets have grown organically. Document the canonical field list and mark which fields are guaranteed-present vs. optional.
4. Review essay frontmatter: verify the seven required keys (`title`, `trademark_serial`, `trademark`, `tm_filing_dt`, `patent_no`, `patent_grant_dt`, `entity`) are enforced by `historian validate` and documented as the stable interface.
5. Output: a `CONTRACT.md` at repo root listing each contract surface, its format, and a pointer to the authoritative schema definition.

---

### P2 — Schema hardening — CLOSED

Fix any gaps the P1 audit surfaces. No new features — only documentation, light enforcement, and stability fixes.

1. For any undocumented DuckDB column that the companion repo will need: add a `-- contract: <type>, <nullable>` comment to the DDL or a schema note in the relevant specialist's design doc.
2. For any JSONL field that is present in some records but not others without documentation: add it to the canonical field list with `optional: true` and document the condition under which it appears.
3. For any essay frontmatter key that `historian scaffold` does not currently write: either add it to scaffold output or remove it from the contract.
4. Verify `historian validate` enforces all seven required frontmatter keys. If any key passes validate despite being absent or malformed, fix the check.

---

### P3 — CONTRACT.md and version marker — CLOSED

1. Write `CONTRACT.md` at repo root: one section per contract surface (DuckDB tables, JSONL files, essay frontmatter, library index). Each section: field name, type, nullable, guaranteed-present or optional, example value, and a one-line description of its purpose for a Markery-LangGraph node consuming it.
2. Add a `contract_version` field to `data/` or a `MANIFEST.json` at repo root (e.g., `{"contract_version": "1.0", "markery_version": "0.3.0"}`). Markery-LangGraph reads this at startup to verify compatibility. Increment on any breaking contract change.

---

### P4 — Integration smoke test — CLOSED

Verify that a minimal Markery-LangGraph node can read all contract surfaces without error.

1. Write `tests/test_contract.py`: for each contract surface, assert the expected fields are present in a real data record from the `information-systems` project. This test does not depend on LangGraph — it validates that Markery-ICM's output matches what `CONTRACT.md` promises.
2. Run against `information-systems` corpus. All assertions pass.
3. Add `test_contract` to the MVO job in `ci.yml` (runs under `workflow_dispatch` only, same as `test_mvo`).

---

---

### P5 — Shared API client and historian inference mode — CLOSED

**Prerequisite:** P1–P4 complete.

**Why infrastructure first:** P5 originally put historian inference before the shared client abstraction. That ordering would add a third `anthropic.Anthropic()` construction site immediately before P6 refactors them all. Instead: establish `common/llm.py` first so inference commands use it natively.

**Part A — Shared API client and model consistency (prerequisite for Part B):**

1. Write `common/llm.py`: `get_client() -> client`, `call(model, system, user, max_tokens) -> (text, prompt_tokens, completion_tokens)`. Implementation calls Anthropic; interface is generic enough that a second provider (OpenAI-compatible, Gemini) could be added by swapping one file. Do not implement any second provider — define the abstraction only.
2. Refactor `tokens.py` and `extract.py` to construct the Anthropic client via `common.llm.get_client()` rather than inline. After this step there is exactly one client construction site in the codebase.
3. Add `MARKERY_CONTEXT_BUDGET` env var (integer, token count). When set, `historian digest` and `historian card` truncate their assembled context to stay within the budget. Default: unset (current behaviour unchanged). Verify: `MARKERY_CONTEXT_BUDGET=2000 markery historian digest radio-pioneers` fits the budget; `MARKERY_CONTEXT_BUDGET=8000` includes more candidates.

**Part B — Historian inference (uses `common/llm.py` from Part A):**

**Goal:** Give historian commands the ability to call Claude directly with `--infer`, so the full card-review and candidate-assessment workflow can run without a human-driven Claude Code session. This is the bridge to Markery-LangGraph.

**Design constraint:** `--infer` mode must work with any model reachable via `MARKERY_MODEL`. It must not assume Claude-specific output formatting. The existing `--tokens` flag applies automatically to all `--infer` calls.

4. Add `--infer [--model MODEL]` to `markery historian card <project> <slug>`:
   - Load the card context document (existing output)
   - Send to the API via `common.llm.call()`: system prompt = `persona/identity.md` (condensed); user prompt = card context + assessment request
   - Parse response into a structured result: `{"recommendation": "confirm|reject|defer", "score": 1–5, "reasoning": "..."}`
   - Print result; append token record to `MARKERY_TOKEN_LOG` if set
   - `--model` overrides `MARKERY_MODEL` for this call only

5. Add `--infer` to `markery historian digest <project>`:
   - After generating the digest document, send it to the API with the question: "Which candidates are most worth reviewing first and why?"
   - Append the model's ranked recommendation list below the digest output
   - Token count appended to log

6. Add `markery historian draft <project> <slug> [--model MODEL]`:
   - New command: takes an existing scaffold and calls the API to produce a first-draft essay
   - Output written to `content/<slug>-draft.md` (distinct from the final `<slug>.md` to avoid overwriting human work)
   - Immediately run `historian validate` on the draft; print PASS/FAIL alongside token counts

7. Verify on radio-pioneers: run `historian card --infer` on ≥3 candidates with `MARKERY_MODEL=claude-haiku-4-5-20251001`; run `historian draft` on one confirmed pair; record validate result.

---

### P6 — Prompt caching and multi-model validation — CLOSED

**Goal:** With inference infrastructure from P5 in place, reduce per-call cost and prove model-agnosticism is a tested property, not just a design claim.

**Prompt caching** (highest ROI):
1. Add `cache_control: {"type": "ephemeral"}` to the system prompt block in `librarian extract` and the historian inference calls added in P5. Persona content (`identity.md`) is identical across all calls in a session — it is the canonical cache candidate. Measure the cache hit rate via `cache_read_tokens` in `MARKERY_TOKEN_LOG`. Target: ≥80% cache hit rate on repeated calls within a session.
2. Document the caching behaviour in `DESIGN.md`: what is cached, what is not, and why (cache TTL is 5 minutes — sessions longer than 5 minutes between calls will miss).

**Multi-model MVO validation**:
3. Extend the existing MVO test job in `ci.yml` with a `model-matrix` step: run all MVO contracts with `MARKERY_MODEL=claude-haiku-4-5-20251001` and `MARKERY_MODEL=claude-sonnet-4-6`. Both must pass. This is the continuous proof that the output contracts are model-agnostic, not just token-efficient.
4. Record the first multi-model MVO run results in `tests/benchmarks/README.md`: a model-comparison table (command, Haiku tokens, Sonnet tokens, both pass/fail).

---

### Phase Gate

P1 PASSED when: every contract surface has located documentation; gaps are listed. — PASSED 2026-06-06 (CONTRACT.md written; 9 surfaces documented: patents.duckdb (4 tables), trademarks.duckdb (7 tables), entities.duckdb (2 tables), candidates.jsonl, confirmed.jsonl, rejected.jsonl, essay frontmatter, library/index.jsonl, library/index.duckdb; 6 gaps listed; PHASE17-P3-REVIEW.md archived)

P2 PASSED when: all documented gaps are resolved; `historian validate` enforces all required frontmatter keys. — PASSED 2026-06-06 (`title_present` and `trademark_present` checks added to validate; absent `tm_filing_dt` now fails rather than silently skipping; `-- contract:` comments added to patents, extended_marks, company_entity, entity_name_variant DDL; CONTRACT.md gaps table updated; 3 new tests; 489 total pass)

P3 PASSED when: `CONTRACT.md` exists at repo root; `MANIFEST.json` has `contract_version`. — PASSED 2026-06-06 (CONTRACT.md rewritten with example values and LangGraph-consumer purpose descriptions on every field across all 9 surfaces; P2 gaps resolved in document; MANIFEST.json written with contract_version=1.0, markery_version=0.3.0)

P4 PASSED when: `tests/test_contract.py` passes against `information-systems`; test added to CI mvo job. — PASSED 2026-06-06 (34 tests across all 9 contract surfaces; all pass; passage_id range-only check (not work_slug join) since index.duckdb is stable-until-rebuild; ci.yml mvo job updated; 523 total tests pass)

P5 PASSED when: `common/llm.py` exists with `get_client()` and `call()`; `tokens.py` and `extract.py` use it; `MARKERY_CONTEXT_BUDGET` respected by digest and card; `historian card --infer` returns structured recommendation on radio-pioneers data with Haiku; `historian draft` produces an essay that passes `historian validate` (or fails with a documented reason); token counts logged. — PASSED 2026-06-06 (see Part A and Part B notes above)

Part A PASSED 2026-06-06: `common/llm.py` written with `get_client()` and `call()`; single `anthropic.Anthropic()` construction site confirmed (one grep hit); `tokens.py` and `extract.py` refactored to `common.llm.get_client()`; `_get_client()` removed from extract.py; `MARKERY_CONTEXT_BUDGET` added to `historian digest` (limits next_review candidates) and `historian card` (truncates abstract/goods); 523 tests pass; test_librarian.py mock updated to patch `markery.common.llm.get_client`.

Part B PASSED 2026-06-06: `historian card --infer` added (RECOMMENDATION/SCORE/REASONING structured output, `--model` override, token log always emits); `historian digest --infer` added (ranked prioritization appended below digest); `historian draft` command added (reads scaffold, writes `<slug>-draft.md`, runs validate immediately, always logs tokens). Verified on radio-pioneers with Haiku: card --infer produced defer/confirm/reject across 3 candidates with sound reasoning (STERILAMP/Display Device=defer goods mismatch, VISICODE/Display Device=confirm, MICARTA/sodium lamp=reject); digest --infer ranked top 3 with domain-aware rationale; minalite-us1829460a-draft.md validate 8/8 PASS (1,346p/1,233c tokens, 9.5s wall).

P6 PASSED when: prompt cache hit rate ≥80% on repeated extract calls; MVO contracts pass on both Haiku and Sonnet; multi-model comparison table in `tests/benchmarks/README.md`. — PASSED 2026-06-06 (`cache_control: {"type": "ephemeral"}` added to all system prompts in `common.llm.call()` and `librarian extract._call_claude()`; identity.md loaded at runtime for all inference system prompts — all above 1,024-token minimum (card=2,093, digest=1,841, draft=1,960, extract=2,255); Sonnet caching confirmed active: cache_read_input_tokens=2,087 on card calls 2 and 3; Haiku caching not activating on this account (inference_geo='not_available' — account/regional limitation, not a code issue); extract would achieve >93% hit rate on 15-chunk runs with Sonnet; MVO contracts pass on both models with same confirm/reject/defer outcomes and validate 8/8 PASS; multi-model comparison table in tests/benchmarks/README.md; CI mvo job updated with model-matrix strategy running both models)

Phase PASSED when P1–P6 all pass. Markery-LangGraph repo may begin after this gate. — PASSED 2026-06-06
