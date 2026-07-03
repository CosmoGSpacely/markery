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
| **technology** | a CPC area | the entities / marks / patents in it |
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

## 3. Data / structure — Decision 1, evaluated (not assumed)

The registry has two jobs in tension: it is **queried for matching** (join entity
variants ↔ corpus — favours a queryable store) *and* **human-curated** (merging the
four Westinghouses is a manual act — favours diffable files). The current CSV→DB setup
is the worst case: *two* representations. The fix is **one canonical form + a derived
index**; the choice of canonical is an explicit decision, decided on merits — **not by
analogy to the library** (whose flat-JSONL is itself up for reconsideration so the whole
system shares one deliberate philosophy).

- **Option A (recommended) — canonical flat files + ephemeral index.**
  `registry/entities.jsonl`, `registry/variants.jsonl`, `registry/persons.jsonl` are the
  source of truth (git-diffable, hand-curatable). A DuckDB index is rebuilt in-memory /
  on demand for matching. Justified here by small entity counts (hundreds), curation
  weight (dedup/merge is human), and the corpus DBs already carrying the heavy query
  load. Reconcile `library/catalog.jsonl` to the same philosophy.
- **Option B — canonical DuckDB.** Queryable, single store, but not hand-curatable or
  diffable; keeps a binary blob as the identity source of truth.

A focus is a manifest + its curation:
```
focus/<slug>/
  focus.json          {type: mark|patent|technology|entity|person, subject: <id>, title, selector?}
  content/            the essay(s)  (mark foci already exist as essays today)
  references/library.jsonl
  media/ or refs into library/     (per-focus media)
  confirmed.jsonl / rejected.jsonl (curation, where a focus documents matches)
```
`subject` is a global id (entity id / serial / patent_no / cpc / person id). A focus
**references** shared data; it never re-declares entities. Site: one site, foci as
cross-linked pages + browse indexes.

## 4. Folded in — patent coverage (was PATENT_REVIEW)

Building a focus *populates the corpus for its subject*, so coverage becomes "populate
a focus," not a standalone concern:

- **entity / mark / patent / person focus →** fetch that subject's patents by
  **applicant** (`patent build --applicant "<name>"`, EPO `pa=` — the generalizable
  primitive, no CPC-class guessing).
- **technology focus →** fetch the **CPC area** (`patent build --classes <CPC>`), the
  original PATENT_REVIEW P2b.
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

- **P1 — registry + focus schema.** Land `registry/` (Decision 1 form) as the single
  entity/person identity; define `focus.json`. Global-id resolver + ephemeral match index.
- **P2 — dedup existing entities.** Merge the duplicate Westinghouses (and others) into
  single global ids; a one-time migration with a mapping report.
- **P3 — migrate annual-design-review.** Its `essays/*.md` → **mark foci**; year galleries
  → the **browse index** layer. Retire the `annual-review` project type.
- **P4 — publisher: one site.** Portal-of-projects → one site of foci + indexes,
  cross-linked. Keep `site check` clean.
- **P5 — matchmaker on the global registry.** richness / seed-pairs / match read the
  global registry; retire per-project `entities.csv`/`variants.csv` and the standalone
  `entities.duckdb`-as-source.
- **P6 — spawn/discovery spawn foci** (five types) + the folded coverage-fetch (§4).

Each phase keeps the synthetic fixture + hermetic suite green (update the fixture to the
focus model as P1 lands). Retire the `match-review-essay` / `annual-review` /
`gallery-exploration` project types once foci replace them.

## 7. Decisions to confirm before P1

1. **Canonical registry form** — Option A (flat files + ephemeral index; reconcile the
   library) vs Option B (canonical DuckDB). *Recommend A.*
2. **Focus id/slug + cross-link scheme** — how a mark focus names its entity/patent
   links (stable ids across the site).
3. **Do all five focus types share one `focus.json` schema** (a `type` + `subject`), or
   do any warrant distinct handling? *Lean: one schema.*

## 8. What is preserved (do not lose)

Per-focus curation (`confirmed`/`rejected`/essays), the hermetic-test model, the single
human gate, free-by-default model-agnosticism, and honest provenance/attribution — all
carry through. The restructure removes redundancy (duplicate identity, double-declared
entities, portal-of-projects); it keeps every intellectual artifact.
