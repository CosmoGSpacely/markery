# STRUCTURE_REVIEW — Reconfigure Markery around focus areas

Status: **planning** · opened 2026-07-03. Supersedes and folds in `PATENT_REVIEW.md`
(archived on this file's creation). Archive to `archive/STRUCTURE_REVIEW-<date>.md` on
completion, then `git rm`.

---

## 1. Problem

The current structure carries redundancy and false segregation:

- **Entity identity is not global.** The same firm is re-declared per project with a
  different id — Westinghouse is entity `9`, `9001`, `9003`, `9004`. The "global
  registry" (`data/entities.duckdb`) is really a *union of per-project declarations*,
  so one company appears N times. Everything downstream (richness, dedup, the spawn
  ledger) inherits the duplication.
- **Entity/variant data is declared twice.** Each project holds `entities.csv` +
  `variants.csv`; `matchmaker build` rebuilds those into `entities.duckdb`. Two
  representations of the same facts — the DB is not a source of truth, just an
  aggregation.
- **"Projects" are heavyweight for what they are.** Each is a self-contained directory
  with its own `site/` subtree, stitched by a portal — but Markery is *one* website.
  A focus is a *lens* over shared data, not a container that re-declares the data.

The `annual-design-review` project already shows the target in embryo: its
`essays/*.md` (e.g. `chicago-pneumatic-cp.md`) are mark-foci-in-prose — mark metadata,
"The Company" (entity cross-ref), "The Mark", products-from-goods, a media note.

## 2. The model — five focus types, each a *documented subject*

Markery becomes **one website: a cross-linked web of documented subjects** ("focus
areas"). Five focus types, each producing an **essay + media/images + library
references**, all cross-linked:

| focus | subject | cross-links to |
|---|---|---|
| **mark** | a trademark (RECTIGON, De-Ion, CP) | its entity; matched patents |
| **patent** | a single patent | assignee (entity); inventors (persons) |
| **technology** | a *curated* technology area (may span several CPC classes; one class may host several areas — H01H holds breakers, thermal relays, tap-changers) | the entities / marks / patents curated into it |
| **entity** | a company | its marks, patents, people |
| **person** | an inventor / founder | their patents, entities |

This unifies what are currently separate mechanisms: match-review-essay (a mark+patent
pair → two foci + a connection), the annual review (a gallery of mark foci), **D072
people** (person foci), **D079 technology-area** (technology foci). Foci replace
"projects."

**Indexes are not foci.** Browse views — marks-by-filing-year (today's annual review),
patents-by-person, marks-in-a-technology — are *generated navigation* over foci and the
corpus, not documented subjects themselves. The annual review's year galleries become
the browse/index layer; a notable mark is *promoted* to a mark focus with an essay.

## 3. Data / structure — Decisions 1–3, **settled 2026-07-03**

### 3.1 Decision 1 — the registry is **canonical DuckDB**

The registry is not merely a lookup table of names. Entities carry **many variants**, and
the historical record is **relational and temporal**: firms are renamed, acquired, merged,
and succeeded. Our own data already showed this — `WESTINGHOUSE ELECTRIC & MFG CO` →
`WESTINGHOUSE ELECTRIC CORPORATION`; `Greenfield Tap and Die` → `TRW` → `KENNAMETAL`
(the `own_type_cd` 30→40+ assignment chain behind the original-applicant fix). Modelling
mergers & acquisitions in flat JSONL would be poor; this is what a relational store is for.
Entity counts are small *today*, but the M&A graph makes the registry the richest, most
curated data we own. **Canonical: DuckDB.** No ephemeral-index indirection — the registry
*is* the query surface, joined against the corpus as matching does today.

**Consequence — durability.** A canonical registry can no longer be gitignored-and-rebuilt
(today `entities.duckdb` is rebuilt from per-project CSVs). Losing it would lose irreplaceable
curation. The corpus DBs (`patents`, `trademarks`) keep their current lifecycle — large,
gitignored, rebuildable from EPO/USPTO. The registry gets the opposite treatment: a
**deterministic, git-tracked export** (CSV/JSONL dump, regenerated on write) alongside the DB,
so curation is diffable, reviewable and recoverable. The DB is canonical for reads/writes;
the export is the durability + review artifact. *This is the one thing flat files gave for
free, and it must be bought back explicitly.*

**Schema sketch** (registry DB):
```
company_entity(entity_id PK, canonical_name, entity_type, industry, slug, founded, dissolved)
entity_name_variant(variant_id PK, entity_id FK, variant_name, source)   -- patent_assignee | trademark_owner
entity_relation(from_entity, to_entity, kind, effective_date, source)    -- M&A / succession
entity_alias(retired_id, survivor_id)                                     -- dedup merges
person_entity(person_id PK, canonical_name, slug, kind)
person_name_variant(variant_id PK, person_id FK, variant_name, source)
person_alias(retired_id, survivor_id)
```

**Merge ≠ succession — do not conflate them.** Phase 35 depends on this distinction:
- **Dedup merge** (`entity_alias`): records that were *always the same real firm* — the four
  Westinghouses (ids 9 / 9001 / 9003 / 9004, all naming *Westinghouse Electric & Manufacturing
  Company*). Merge into one id; alias the retired ids so URLs and cross-links keep resolving.
  Not a historical event.
- **Succession / M&A** (`entity_relation`, kind ∈ `renamed_to | merged_into | acquired_by |
  succeeded_by | subsidiary_of`, with `effective_date`): *distinct* real firms where one became
  or absorbed the other — *Westinghouse Electric & Mfg Co* → *Westinghouse Electric Corporation*
  (1945). A historical fact worth documenting; **both may deserve their own entity focus.**

A naive "merge everything named Westinghouse*" would wrongly collapse the 1945 successor into
its predecessor. The dedup pass must separate the two.

### 3.2 Decision 2 — identity, slug, cross-links

**A technology area is an editorial concept, not a classification code.** CPC is *many-to-many*
with technology areas in both directions (H01H hosts breakers *and* thermal relays; "battery
charging & rectification" spans H02M + H02J). So CPC is a **selector**, never an identity.

| focus | identity | slug (stored, immutable) |
|---|---|---|
| **mark** | USPTO serial | `mark/rectigon-71153780` (name + serial: readable *and* collision-proof) |
| **patent** | patent no | `patent/us1389147a` |
| **entity** | internal registry id | `entity/westinghouse-electric-manufacturing-company` |
| **person** | internal registry id | `person/john-w-fitzgerald` |
| **technology** | **internal** registry id | `technology/arc-quenching-circuit-interruption` |

- **Slugs are stored fields, never derived at render.** (Today `person_entity` stores a slug with
  collision suffixes; `company_entity` has none and the publisher slugifies the *current* name —
  so a rename silently moves the URL. That gap is fixed here.)
- **Cross-links use `[[type:slug]]`**, resolved through the existing `build_link_index`:
  `[[entity:westinghouse-electric-manufacturing-company]]`, `[[patent:us1389147a]]`,
  `[[technology:arc-quenching-circuit-interruption]]`. Resolution passes through the **alias**
  tables, so merged/retired slugs redirect rather than 404. **An unresolved cross-link fails the
  build** (same integrity discipline as `site check`).
- **CPC is a browse facet, not a focus.** It gets an index page (`/cpc/h01h/`) listing the
  technology areas, patents and marks touching it. `[[cpc:h01h]]` is a distinct namespace linking
  to that index — consistent with *indexes are not foci* (§2).

### 3.3 Decision 3 — one `focus.json` schema for all five types

```jsonc
// focus/<type>/<slug>/focus.json
{ "type": "technology",                       // mark|patent|technology|entity|person
  "subject": "tech-0007",                     // the identity above
  "slug": "arc-quenching-circuit-interruption",
  "title": "Arc-Quenching Circuit Interruption",
  "selector": { "cpc": ["H01H", "H02B"], "years": [1915, 1940] } }  // technology only
```
A focus directory:
```
focus/<type>/<slug>/
  focus.json          manifest (selector gathers candidates)
  members.jsonl       CURATED membership — technology foci (selector over-includes)
  content/            the essay(s)   (mark foci exist as essays today)
  references/library.jsonl
  confirmed.jsonl / rejected.jsonl   (where a focus documents matches)
```
A focus **references** shared data by id/slug; it never re-declares entities.

### 3.4 The governing principle — derive vs curate

> **Derive every edge the corpus already knows; store only the curated ones.**

- **Derived (never stored):** mark→entity (owner), patent→entity (assignee), patent→person
  (inventor), patent→CPC (`patent_classes`). Computed from the corpus at index/render time.
- **Curated (stored once):** technology↔patents/marks (`members.jsonl` — because a CPC selector
  over-includes, exactly as the US-class tech gate did: *necessary, not sufficient*), and
  mark↔patent (the confirmed match, already `confirmed.jsonl`).
- **Back-links are derived, never duplicated.** A patent page showing *"part of: arc-quenching
  interruption"* is computed by indexing every technology focus's `members.jsonl`. One source of
  truth per relation — the same discipline that kills the duplicate-entity problem.

## 4. Folded in — patent coverage (was PATENT_REVIEW)

Building a focus *populates the corpus for its subject*, so coverage becomes "populate
a focus," not a standalone concern:

- **entity / mark / patent / person focus →** fetch that subject's patents by
  **applicant** (`patent build --applicant "<name>"`, EPO `pa=` — the generalizable
  primitive, no CPC-class guessing).
- **technology focus →** fetch the CPC classes named in its **`selector.cpc`**
  (`patent build --classes <CPC …>`), the original PATENT_REVIEW P2b. The fetch gathers
  candidates; `members.jsonl` curates which of them actually belong (§3.4).
- **Pre-gate coverage flag** — a cheap EPO count (`pa=`/`coverage-check`) vs local, shown
  at the human gate so approval authorises a bounded, resumable fetch (±window,
  per-subject cap, defer-on-quota via the fetch log). Same resumable/graceful-degradation
  spine as D077 (closed).

Defaults carried from PATENT_REVIEW §7: ±10y window, ~2,500-patent cap, lazy per-focus
fetch, `--allow-fetch` off by default.

## 5. Folded in — the agentic loops (spawn + discovery)

- **`spawn_graph.py` spawns foci**, not standalone projects. Its shape survives (dedup
  ledger → assemble proposals with coverage flag → **one human gate at focus creation**
  → build), but the unit is a focus of one of the five types, and the ledger dedups by
  `(type, subject-id)` **against the global registry** (killing the duplicate-entity
  problem at the source).
- **Per-focus build** = the same all-source pass we built: essay (free model, published),
  discovery (books / newspapers / media / images, relevance-scored), library refs, media
  — for *every* focus type ("essay + media + library if possible").
- **Discovery loop** populates a focus's `references/library.jsonl`; free-first model
  chain + unscored re-score (D077) already in place.
- **Model-agnostic, free-by-default, token-thrift** (D077) and the single-gate /
  local-preview-only / never-publish invariants (Phase 32 P4) all carry over unchanged.

## 6. Migration — bounded, phased, hermetic-green

Scope reducers agreed: **archive `rectigon-westinghouse` and
`westinghouse-electric-manufacturing-company`** (demos); migrate only
**`annual-design-review`**.

- **P1 — registry + focus schema. DONE (Phase 34, 2026-07-10).** Landed the **canonical
  registry DuckDB** (§3.1 schema: entities, variants, `entity_relation`, `entity_alias` +
  `retired_slug`, persons, `person_alias`) as the single identity; added the **git-tracked
  deterministic export** (`registry/` CSVs, regenerated on every write; `markery matchmaker
  export`). Stored `slug` on every type; `focus.json` (§3.3) + the `[[type:slug]]` resolver
  with cycle-safe alias redirects and build-failure on dangling links (`common/focus.py`).
  Fixture migrated. 1056 hermetic tests.
- **P2 — dedup existing entities.** Merge the duplicate Westinghouses (and others) into
  single ids via `entity_alias`, with a mapping report. **Must distinguish dedup-merge from
  succession/M&A** (§3.1) — record real successions in `entity_relation`, never collapse a
  1945 successor into its predecessor.
- **P3 — migrate annual-design-review.** Its `essays/*.md` → **mark foci**; year galleries
  → the **browse index** layer. Retire the `annual-review` project type.
- **P4 — publisher: one site.** Portal-of-projects → one site of foci + indexes,
  cross-linked. Keep `site check` clean.
- **P5 — matchmaker on the global registry.** richness / seed-pairs / match read the
  canonical registry directly; retire per-project `entities.csv`/`variants.csv` (the
  double declaration). Publisher reads stored slugs instead of slugifying current names.
- **P6 — spawn/discovery spawn foci** (five types) + the folded coverage-fetch (§4).

Each phase keeps the synthetic fixture + hermetic suite green (update the fixture to the
focus model as P1 lands). Retire the `match-review-essay` / `annual-review` /
`gallery-exploration` project types once foci replace them.

## 7. Decisions — settled 2026-07-03

1. **Canonical registry form → canonical DuckDB** (§3.1). Rationale: entity counts are small
   *today*, but variants plus mergers & acquisitions make the registry a relational, temporal
   graph — the richest curated data we own. Buys back durability with a git-tracked export.
2. **Identity / slug / cross-links** (§3.2). Technology identity is **internal** (CPC is a
   selector, not an identity); slugs are **stored, immutable**; cross-links are `[[type:slug]]`
   resolved through alias tables; unresolved links fail the build; CPC is a browse facet.
3. **One `focus.json` schema** for all five types (§3.3). ✅

**Still open (before Phase 39):** the **human-gate UX**. The gate exists in the graph but has
no human surface — the runner prints "awaiting human decision" and exits, and `MemorySaver`
means a pause does not survive the process. Needs (a) a **durable checkpointer**, (b) a review
surface, (c) a response mechanism. Proposed two-touch design: a cheap batched CLI review
(`markery focus review` — tiered clean/review piles with coverage flags) *before* spending
EPO/model budget; then, since foci build locally and never publish, a richer **browse-the-built-
focus** review to keep or discard. To be specced before Phase 39.

## 8. What is preserved (do not lose)

Per-focus curation (`confirmed`/`rejected`/essays), the hermetic-test model, the single
human gate, free-by-default model-agnosticism, and honest provenance/attribution — all
carry through. The restructure removes redundancy (duplicate identity, double-declared
entities, portal-of-projects); it keeps every intellectual artifact.
