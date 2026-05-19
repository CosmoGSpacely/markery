# Project Review — information-systems

Research and publication work for the information-systems project. Covers current state, content gaps, and the Phase 7 plan. For tool development (specialist code, CLI, schema changes), see `SPECIALIST_REVIEW.md`.

---

## Current State

### Confirmed pairs

| Mark | Serial | Entity | Status |
|---|---|---|---|
| SOUNDEX | 71246709 | Rand Kardex Bureau | ✅ Essay written |
| SOUNDEX QUICK AS A FLASH | 71255821 | Rand Kardex Bureau | ✅ Confirmed |
| KARDEX | 71467213 | Remington Rand | ✅ Essay written |
| VARIADEX | 71461278 | Remington Rand | ✅ Confirmed |
| VI-DEX | 71235764 | Wilson Jones | ✅ Confirmed |
| REDIREF | 71237470 | Wilson Jones | ✅ Confirmed |
| HANDIREF | 71254950 | Wilson Jones | ✅ Confirmed — **essay missing** |
| SHANNON | ~1930 | Yawman & Erbe | ✅ Confirmed |

### Entities in registry

| Entity | Coverage |
|---|---|
| Remington Rand (+ predecessors) | KARDEX, VARIADEX, SOUNDEX, SOUNDEX QUICK AS A FLASH |
| Wilson Jones | VI-DEX, REDIREF, HANDIREF |
| Yawman & Erbe | SHANNON |
| Rand Kardex Bureau | SOUNDEX, SOUNDEX QUICK AS A FLASH |

**Missing from registry:** Smead Mfg. (SMEAD'S TELL VISION SYSTEM, serial 71403472), Library Bureau (SOUNDEX citation-chain precursor), WHEELDEX owner (serial 71321669 — owner unknown, needs research before adding).

### Patent corpus

Current CPC classes loaded: B42F, B42D.

**Missing for full information-systems scope:** B41J (typewriters), B41L (duplicating), G06C (calculating machines), G06K (data recognition), G09F (display devices). These are in `OBJECTIVES.md` scope and required before Smead Mfg. or Library Bureau candidates can be generated.

### Site status

Site infrastructure is in place (Phase 4 CI, gh-pages deploy). Content pages written: SOUNDEX essay, KARDEX essay, entity pages for current confirmed entities, landing page. Site has not been built and published since Phase 3 content was written. A full build-and-publish cycle has not been tested end-to-end with the Phase 6B publisher improvements.

### Wikipedia targets

From `OBJECTIVES.md`:

| Target | Type | Status |
|---|---|---|
| SOUNDEX | Enrich existing article | Draft not yet written |
| KARDEX | Create new article | Draft not yet written |

---

## Phase 7 Plan

Phase 7 is entirely project work — no tool code changes. It depends on Phase 6D being available for fetch operations, but the data expansion (7A) and content writing (7B) can proceed independently before fetch is needed.

### 7A — Corpus Expansion and Entity Registration

**Goal:** patents.duckdb covers all seven CPC classes; Smead Mfg. and Library Bureau are in the entity registry; new candidates are generated and enriched.

**Steps:**

1. **Fetch remaining CPC classes** (D001 — tool already supports this):
   ```bash
   markery patent build --resume   # add B41J B41L G06C G06K G09F
   markery status                  # confirm row counts
   ```

2. **Research WHEELDEX owner** — serial 71321669, filed 1931-12-01. Query TSDR or the bulk `owner` table directly to identify the filing party before adding to registry.

3. **Add entities to registry** — edit `src/markery/specialist/matchmaker/build.py`:
   - Smead Mfg. with variant "Smead Manufacturing Company"
   - Library Bureau (Dewey's bureau; predecessor role in SOUNDEX citation chain)
   - WHEELDEX owner once identified

4. **Rebuild entity registry:**
   ```bash
   markery matchmaker build
   markery matchmaker status     # confirm new entities
   ```

5. **Generate new candidates:**
   ```bash
   markery match information-systems --force --full
   ```
   Review `candidates.jsonl` for new Smead Mfg. and Library Bureau pairs.

6. **Confirm any new pairs** — add to `confirmed.jsonl`; write essay stubs in `content/`.

**Phase gate:** `patents.duckdb` includes all seven CPC classes; Smead Mfg. and Library Bureau appear in `markery matchmaker list`; at least one new pair is reviewed.

---

### 7B — Content Completion

**Goal:** All confirmed pairs have essays; all entity summaries are written; enrichment pages are in place.

**Priority order (from OBJECTIVES.md):**

**Highest priority — match essays:**

1. **HANDIREF** (serial 71254950, Wilson Jones, filed 1927-09-19) — companion mark to REDIREF, filed the same day, never essayed. Write `content/match-handiref.md`. Structure: filing context, patent connection, relation to REDIREF as simultaneous filing, archival note on the Wilson Jones loose-leaf specialization.

**High priority — deepen existing essays:**

2. **SOUNDEX** — the canonical exemplar. Deepen the two-patent, two-mark structure (Russell 1918, Odell 1922; serial 71246709 and 71255821). This is the essay to be linked from the landing page and used as the Wikipedia enrichment source.

3. **KARDEX** — strongest single-pair note; best Wikipedia target. Add secondary-source grounding: Yates on visible index systems (*Structuring the Information Age*, 2005), Cortada on Remington Rand's product evolution (*Before the Computer*, 1993).

**Medium priority — entity summaries:**

4. **Remington Rand** — corporate succession: Remington Typewriter → Rand Kardex Bureau → Remington Rand; central to SOUNDEX, VARIADEX, KARDEX. Write `content/entity-remington-rand.md`.

5. **Wilson Jones** — loose-leaf specialization distinct from Remington Rand's indexing focus; covers VI-DEX, REDIREF, HANDIREF. Write `content/entity-wilson-jones.md`.

6. **Library Bureau** — precursor entity relevant to the SOUNDEX citation chain; Melvil Dewey's supply company, acquired by Remington Rand. Write `content/entity-library-bureau.md`.

**Lower priority — enrichment pages:**

7. **`content/sources.md`** — consolidated primary and secondary source bibliography. Include: USPTO serial numbers, patent publication numbers, Yates (1989, 2005), Cortada (1993), Austrian (1982), Chandler (1977).

8. **`content/timeline.md`** — annotated timeline from first Library Bureau patents (pre-1900) through Remington Rand's post-1939 commercial continuity. Anchor events: Library Bureau founding (~1876), Holmes–Dewey patents, SOUNDEX filing (1927), KARDEX filing (1939).

**Phase gate:** `content/` directory contains an essay for every confirmed pair; entity summaries for Remington Rand, Wilson Jones, Library Bureau; sources.md and timeline.md stubs.

---

### 7C — Site Build and Publish

**Goal:** A complete end-to-end site build from all content, verified in a browser, deployed to gh-pages. First full publish since Phase 3.

**Steps:**

1. **Build locally:**
   ```bash
   markery site build information-systems
   ```
   Review `projects/information-systems/site/` in a browser. Check:
   - Landing page narrative
   - All entity pages render with correct cross-links
   - All match essays render
   - Timeline and sources pages
   - Search page returns results
   - No broken `[[Slug]]` references (broken links appear as literal text, not `<a>`)
   - Open Graph metadata present (`og:title`, `og:description`, `og:image`)

2. **Fix any build issues** — broken cross-links, missing content file references, CSS regressions.

3. **Deploy:**
   ```bash
   git add projects/information-systems/site/
   git push   # triggers gh-pages CI
   ```
   Confirm live URL loads. Check Open Graph preview with a link-preview tool.

4. **Smoke test live site** — verify canonical URL, check that all inter-page links resolve, confirm mark images load.

**Phase gate:** Live site at gh-pages URL serves all pages with no broken links; Open Graph preview shows correct title and image.

---

### 7D — Wikipedia Publishing

**Goal:** Submit the SOUNDEX enrichment and the KARDEX draft article to Wikipedia using `markery wikipedia draft` and `markery wikipedia submit`.

**SOUNDEX enrichment (existing article):**

Wikipedia already has a SOUNDEX article. The target is to add a "History" section grounded in the confirmed patent-trademark pair.

1. Draft the section:
   ```bash
   markery wikipedia draft information-systems soundex
   ```
   This writes `projects/information-systems/wikipedia/soundex.wiki`.

2. Review the wikitext. Verify:
   - Neutral point of view
   - No original research — every claim is grounded in a cited primary source (patent publication number, trademark serial number) or a cited secondary source (Yates, Cortada)
   - Wikilinks to existing articles (Remington Rand, Rand Kardex Bureau, phonetic algorithm)
   - `{{cite patent}}` and `{{cite web}}` templates used correctly

3. Submit:
   ```bash
   markery wikipedia submit information-systems soundex "SOUNDEX" "Add history section: patent-trademark correspondence, Russell 1918 patent and 1927 trademark filing"
   ```
   The command shows a unified diff of the proposed change against the current article and prompts `[y/N]` before submitting.

**KARDEX new article:**

KARDEX does not have a Wikipedia article. The target is to create one.

1. Draft the article:
   ```bash
   markery wikipedia draft information-systems kardex
   ```

2. Review and revise wikitext. A new article requires:
   - Lead paragraph establishing notability (Remington Rand's branded visible index system, 1930s–1950s)
   - Sources section with at least two independent secondary sources (Yates 2005, Cortada 1993)
   - Categories: `[[Category:Office supplies]]`, `[[Category:Remington Rand]]`, `[[Category:Trademarks]]`
   - No promotional tone — encyclopedic register throughout

3. Submit or stage for review:
   ```bash
   markery wikipedia submit information-systems kardex "KARDEX" "Create article: Remington Rand's visible card-index system"
   ```
   For a new article, prefer staging in Wikipedia's draft namespace (`Draft:KARDEX`) first, then moving to mainspace after community review.

**Phase gate:** SOUNDEX article on Wikipedia includes a History section with sourced patent-trademark correspondence; KARDEX draft is in Wikipedia draft namespace or mainspace.

---

## Deferred Project Work

Items not yet in a phase — held pending tool support or research completion.

| Item | Depends on | Notes |
|---|---|---|
| WHEELDEX pair confirmation | Owner identification research | Serial 71321669; owner unknown; cannot add to registry until identified |
| SMEAD'S TELL VISION SYSTEM essay | 7A corpus expansion | Need B42F/B41J patent candidates for Smead before confirming a pair |
| Pre-1900 patent citation chains | Phase 6D `markery patent citations` | Holmes–Dewey filing cabinet patents reach into 1890s; needs citation-chaining tool |
| Post-1939 trademark continuity | Phase 6D `markery trademark entity-forward` | Remington Rand continued filing into the 1940s–1950s; documents commercial continuity |
| Patent figure illustrations in essays | Phase 6D + D003 (patent drawings) | Currently essays cite patent numbers; they cannot display the technical drawings |
