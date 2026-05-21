# Specialist Tool Review — Token Reduction & Model Accessibility

**Date:** 2026-05-21  
**Status:** Concept — not yet promoted to ROADMAP or DEFERRED  
**Scope:** Specialist-owned CLI tools that shift project work from LLM token consumption toward deterministic code, and that reduce the context and output burden enough to make cheap cloud models or local models viable for portions of the workflow.

---

## Problem Statement

The current project workflow is heavily token-dependent at three points:

1. **Session setup** — The historian opens a session, reads BRIEF.md, and then issues a chain of enrichment requests (signals, figures, trademark enrichment) before useful work can begin. Each request requires model context and response.

2. **Candidate review** — Each candidate requires the model to synthesize a join across mark record, patent record, score breakdown, goods description, and date analysis — context that is entirely deterministic and currently reconstructed in tokens every session.

3. **Essay production** — Essays mix factual content (filing date, serial number, goods description, assignee chain, patent claims) with interpretive content (historical significance, industry context). The factual portion is fully derivable from the DB; the model currently produces both.

The result: even a routine research session with a few candidate reviews and one essay draft costs meaningfully in tokens, and the context burden is too large for local models (typical 4K–8K window) and steep for cheap cloud models with limited reasoning ability.

---

## Proposed Tools

### 1. `markery match preflight <project>` — MATCHMAKER

**What it does:** Runs all available enrichment for a project before the model is involved. Specifically: signals enrichment (`markery patent signals`) for every candidate above min-score; TSDR fetch for all candidates in the uncertainty band (0.40–0.60) that lack goods descriptions; figure fetch for all confirmed pairs that lack figures in `patent_figures`. Writes a preflight report to `matches/preflight.json` recording what was fetched and what was skipped (quota hit, already present, etc.).

**What it eliminates:** The entire setup phase of a historian session — the back-and-forth where the model identifies what enrichment is missing and requests it. A session starting after preflight has everything in the DB already; the historian reads, it does not request.

**Token reduction:** Eliminates ~3–5 round-trips of enrichment requests per session.  
**Model accessibility:** Reduces session footprint significantly; sessions become self-contained reads rather than iterative fetch cycles.

---

### 2. `markery historian card <slug>` — HISTORIAN

**What it does:** Generates a fixed-format, compact (~250 token) candidate summary block for a single candidate slug. Sources all data from the DB — no model required. Format is optimized for model input, not human reading: structured fields, no prose, maximum information density. Output written to stdout or optionally to `matches/cards/<slug>.md`.

**Card content:**
- Mark: name, serial, filing date, registration status, owner name as filed
- Goods: truncated goods description (first 100 chars + count of additional classes)
- Entity: canonical name, match variant used, source (patent assignee / trademark owner)
- Patent: number, grant date, CPC class + description, title
- Date gap: years between patent grant and trademark filing, direction (mark before/after patent)
- Score: total, temporal component, class component, semantic bonus (if enriched), model used
- Signals: abstract excerpt if fetched, goods overlap terms if computed
- Status: essay exists Y/N, figure in DB Y/N

**What it eliminates:** The model reconstructing this picture from BRIEF.md + DB queries every time it encounters a candidate. With cards pre-generated, a cheap or local model receives a structured input it can act on directly.

**Token reduction:** Replaces ~400–800 tokens of model-side synthesis per candidate with a deterministic pre-computed block.  
**Model accessibility:** Primary enabling tool for local model candidate review. A local model with a 4K context window can load a digest (see tool 7) + 5–10 candidate cards and make Y/N decisions without any DB access or synthesis.

---

### 3. `markery historian scaffold <slug>` — HISTORIAN

**What it does:** Generates a structured essay skeleton for a confirmed pair with factual sections pre-filled from DB records and interpretive sections left as titled prompts. Written to `essays/<slug>.md` (or a staging path if the essay already exists).

**Pre-filled sections (code-generated):**
- Frontmatter: slug, entity, trademark serial, patent number, filing date, grant date, date gap
- **Primary Sources** section: formatted TSDR citation with URL, formatted patent citation with URL
- **Filing Record** section: full goods and services description from `statement` table, design search codes with descriptions, disclaimer if present, registration number and status
- **Patent Summary** section: title, CPC class + description, grant date, assignee as filed, abstract (if fetched via signals)

**Prompt stubs left for the model:**
- `## [Entity] — [Mark Name]` — opening interpretive paragraph
- `## Historical Context` — industry and period context
- `## The Mark` — visual/design analysis and brand significance
- `## Products and Market Position` — what the goods list reveals about the company's scope
- `## Significance` — why this pair matters for the research argument

**What it eliminates:** The model writing factual sections from scratch — serial numbers, dates, legal descriptions, goods text — which are the most error-prone and verifiable portions of an essay. The model writes only narrative.

**Token reduction:** Roughly 40–60% of final essay word count is pre-filled. For a 1,200-word essay, the model produces ~500–700 words of narrative rather than the full 1,200.  
**Model accessibility:** Transforms essay production into a narrative completion task — well within the capability of cheaper models. Combined with `validate` (tool 4), cheap model essays become trustworthy.

---

### 4. `markery historian validate <slug>` — HISTORIAN

**What it does:** Checks a completed essay file against the DB and reports any factual discrepancies. Pure code, no model. Checks performed:

- Every USPTO serial number cited in the essay resolves against `case_file`
- Every patent number cited resolves against `patents`
- Filing dates, grant dates, and registration numbers quoted in the essay match the DB records
- Goods description excerpts match the `statement` table (within edit distance threshold for paraphrase)
- Entity name used in the essay matches a known variant in `entities.duckdb`
- No cross-contamination: serial numbers and patent numbers belong to the same confirmed pair (catches copy-paste errors between essays)

Output: a structured report listing each check, pass/fail, and the discrepancy if any. Returns exit code 1 if any check fails.

**What it eliminates:** A model-side verification pass after essay writing — currently the historian re-reads the essay to check its own facts against what it remembers from the DB query. Code does this instantly and exhaustively.

**Token reduction:** Eliminates one full verification round-trip per essay.  
**Model accessibility:** Acts as a trust layer for cheap and local model essays. A cheap model writes into a scaffold; the validator catches factual errors without requiring a second expensive model pass to review. Makes cheap-model output safe enough to commit.

---

### 5. `markery matchmaker suggest-variants <canonical_name>` — MATCHMAKER

**What it does:** Fuzzy-matches a canonical entity name against `assignee_name` in `patents.duckdb` and `own_name` in `trademarks.duckdb`. Returns a ranked list of candidate variant strings with occurrence counts and source (patent assignee / trademark owner). Matching uses token overlap, edit distance, and common abbreviation expansion (Inc. / Incorporated / Corp. / Company / Co.).

Example output:
```
Canonical: Remington Rand

Patents (assignee_name):
  "REMINGTON RAND INC."          — 47 patents
  "REMINGTON RAND CORPORATION"   — 12 patents
  "RAND KARDEX CORPORATION"      — 8 patents

Trademarks (own_name):
  "REMINGTON RAND, INC."         — 23 marks
  "REMINGTON RAND"               — 6 marks
  "REMINGTON RAND LIMITED"       — 2 marks (foreign)
```

**What it eliminates:** The exploratory DB querying phase of entity registration — currently done through iterative model-mediated queries (`show me all assignees that look like X`). The operator picks from a ranked list rather than discovering through a token-burning discovery loop.

**Token reduction:** Replaces an open-ended exploration with a single CLI call. For a new entity, saves 3–8 round-trips.  
**Model accessibility:** Removes entity setup as a token cost entirely. Any operator (not just a model) can run `suggest-variants` and build `entities.csv` from the output.

---

### 6. `markery match auto-disposition <project> [--reject-below <score>] [--dry-run]` — MATCHMAKER

**What it does:** Applies deterministic rejection rules to candidates that fall clearly outside the decision-relevant range. For each candidate below the threshold (default: 0.25), writes a rejection record to `rejected.jsonl` with a machine-generated reason string and sets a `auto_rejected: true` flag so the disposition is distinguishable from human review.

Rejection reasons generated:
- `score_below_floor: 0.12 < 0.25` — score threshold
- `date_gap_exceeds_ceiling: 41 years` — configurable maximum gap
- `company_name_mark: draw_cd=1000, no_design_element` — existing exclusion logic surfaced as a disposition
- `class_mismatch: no_project_classes_in_patent` — zero CPC class overlap with project signal set

`--dry-run` reports what would be rejected without writing. Default threshold is configurable per project via a `matches/auto_disposition.json` settings file so it can be tuned without code changes.

**What it eliminates:** Interactive historian review for candidates that score 0.12 with a 40-year date gap — cases that require no judgment. These currently pass through the review queue and cost tokens.

**Token reduction:** Depends on candidate volume, but in practice the below-floor population is often 30–50% of total candidates. Eliminating those from the review queue halves or better the model's review workload.  
**Model accessibility:** Concentrates model attention (and token budget) on the uncertainty band where judgment actually matters. Makes cheap/local model review tractable by reducing queue size to the genuinely ambiguous cases.

---

### 7. `markery historian digest <project>` — HISTORIAN

**What it does:** Produces a compact, model-optimized project state representation distinct from BRIEF.md. Where BRIEF.md is human-readable prose and structured markdown, the digest is a dense structured block designed to convey maximum state in minimum tokens — targeting ~800–1,200 tokens total.

**Digest content (structured, not narrative):**
```
PROJECT: information-systems  PREPARED: 2026-05-21T09:00
CONFIRMED: 8  REJECTED: 23  UNREVIEWED: 14
ESSAYS: 3 complete, 5 missing [slugs...]
NEXT_REVIEW: soundex-us1261167a (0.68), variadex-us2152606a (0.61), ...
ENRICHED: signals=6/14, figures=8/8, tsdr=5/14
PREFLIGHT_STATUS: complete 2026-05-21T08:55
CARDS_AVAILABLE: [list of slugs with pre-generated cards]
SCAFFOLD_AVAILABLE: [list of slugs with pre-generated scaffolds]
```

**What it enables:** A local model with a small context window loads the digest, reads one or two candidate cards (tool 2), and has enough context to act — write a review decision, continue an essay — without loading the full BRIEF or querying the DB. The digest is the index; the cards are the detail.

**Token reduction:** Marginal for large-context models. Significant for local models — it's the difference between fitting in context and not.  
**Model accessibility:** Primary enabling infrastructure for local model sessions alongside tool 2 (card). Together they define a complete small-context interface to the project state.

---

## Summary

| Tool | Specialist | Primary token saving | Local model relevance |
|---|---|---|---|
| `preflight` | MATCHMAKER | Eliminates setup enrichment round-trips | Reduces session footprint |
| `card` | HISTORIAN | Replaces per-candidate synthesis (~400–800 tokens each) | Primary enabler — structured fixed-format input |
| `scaffold` | HISTORIAN | ~50% of essay output is pre-filled | Transforms essay work into narrative completion |
| `validate` | HISTORIAN | Eliminates post-essay verification pass | Trust layer for cheap/local essay output |
| `suggest-variants` | MATCHMAKER | Replaces entity discovery loop | Removes entity setup as token cost |
| `auto-disposition` | MATCHMAKER | Removes 30–50% of review queue | Concentrates budget on uncertain cases |
| `digest` | HISTORIAN | Marginal for large-context models | Essential for small-context models alongside `card` |

### Dependency order for implementation

If these move to the roadmap, the natural sequence is:

1. `auto-disposition` — standalone, no dependencies, immediate queue reduction
2. `preflight` — standalone, reduces setup cost immediately  
3. `suggest-variants` — standalone, removes entity setup token cost
4. `card` — depends on signals/enrichment being available (preflight helps); primary local model enabler
5. `digest` — depends on cards existing; completes the small-context interface
6. `scaffold` — depends on card structure being settled (shares field definitions); highest essay-quality impact
7. `validate` — depends on scaffold structure (validates against the factual section format); completes the cheap-model trust loop
