# Markery Roadmap

Active phases for the **focus-area reconfiguration**. Each phase is the sequence + gate;
full detail lives in `STRUCTURE_REVIEW.md`. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.
Phases 14–15 closed 2026-06-01/2026-05-24. Archived to `archive/ROADMAP-2026-06-03.md`.
Phases 16–18 closed 2026-06-06. Archived to `archive/ROADMAP-2026-06-06.md`.
Phase 19 closed 2026-06-07. Archived to `archive/ROADMAP-2026-06-07.md`.
Phases 20–22 closed 2026-06-14. Archived to `archive/ROADMAP-2026-06-14.md`.
Phase 23 closed 2026-06-18 (P3/D028 deferred to `DEFERRED.md`). Archived to `archive/ROADMAP-2026-06-18.md`.
Phases 24–26 closed 2026-06-23. Archived to `archive/ROADMAP-2026-06-23.md`.
Phases 27–31 closed 2026-06-28; Phase 32 (spawning pipeline) built P1–P4 then superseded by the focus-area reorientation. Archived to `archive/ROADMAP-2026-07-03.md`.

---

## Re-centering (2026-07-03) — One Markery

The distraction has been failing to commit to **one of each**: **one library, one project,
one site, one database set** — one registry of identity. Segregated projects each
re-declared their entities (Westinghouse is four different ids), stored variants twice
(per-project CSVs → rebuilt `entities.duckdb`), and built into separate site subtrees
stitched by a portal.

The reconfiguration collapses all of that into **one Markery**: a single cross-linked site
that is a web of **documented subjects — focus areas** of five types (**mark, patent,
technology, entity, person**), each an essay + media/images + library references, over one
shared corpus and one global registry. Full plan and the open decisions in
`STRUCTURE_REVIEW.md`.

**Invariants held through every phase:** per-focus curation (confirmed/rejected/essays), the
single human gate, free-by-default model-agnosticism (D077), honest provenance/attribution,
and a green hermetic suite (the synthetic fixture migrates to the focus model in Phase 34).

---

## Phase 33 — DEFERRED pass + archive the demo projects

1. Walk **every** `DEFERRED.md` entry against the focus model: subsume / close / keep /
   reframe. (D072→person focus, D079→technology focus, D078→mark/tech triage, D073→Decision 1
   already annotated; review D070/D071/D007/D028/D068 for whether "one site / one database
   set" changes their triggers.)
2. Archive `rectigon-westinghouse` and `westinghouse-electric-manufacturing-company` (demos).

**Gate:** `DEFERRED.md` reflects the reorientation (every open item has a trigger consistent
with focus areas); `projects/` holds only `annual-design-review`.

---

## Phase 34 — Global registry + focus schema  ·  STRUCTURE_REVIEW §3, P1

1. Decide Decision 1 (canonical registry form — flat files + ephemeral index vs canonical
   DuckDB; "one database set") and land `registry/` as the single entity + person identity.
2. Define `focus.json` (`type` + `subject` + optional `selector`); a global-id resolver and
   the ephemeral match index.
3. Migrate the synthetic fixture + hermetic suite to the focus model.

**Gate:** one entity per real-world firm; a focus references ids and declares nothing; suite
green on the new model.

---

## Phase 35 — Dedup entities  ·  STRUCTURE_REVIEW P2

1. Merge duplicate identities (the four Westinghouses, etc.) into single global ids with a
   mapping report; rewrite references.

**Gate:** no duplicate identities; richness/seed resolve one Westinghouse.

---

## Phase 36 — Migrate annual-design-review to foci  ·  STRUCTURE_REVIEW P3

1. `essays/*.md` → **mark foci**; year galleries → the **browse/index** layer.
2. Retire the `annual-review` (and `match-review-essay`, `gallery-exploration`) project types.

**Gate:** annual-design-review renders as mark foci + browse indexes; `site check` clean.

---

## Phase 37 — Publisher: one site  ·  STRUCTURE_REVIEW P4

1. Portal-of-projects → **one site** of foci + indexes, cross-linked (mark↔entity↔patent↔
   person↔technology).

**Gate:** a single site; cross-links resolve; no per-project site subtrees.

---

## Phase 38 — Matchmaker + richness on the global registry  ·  STRUCTURE_REVIEW P5

1. `richness` / `seed-pairs` / `match` read the global registry; retire per-project
   `entities.csv`/`variants.csv` and `entities.duckdb`-as-source (**one database set**).

**Gate:** matching uses global identity; `entities.duckdb` is derived/ephemeral only.

---

## Phase 39 — Spawn + discovery spawn foci; coverage folded in  ·  STRUCTURE_REVIEW P6 (+ archived PATENT_REVIEW)

1. `spawn_graph` spawns **foci** (five types) behind the one gate; ledger dedups by global id.
2. Per-focus build: published essay + all-source discovery (books/newspapers/media/images) +
   library refs — for every focus type.
3. Coverage-fetch folded in: building a focus populates its subject's patents (applicant-fetch
   for mark/patent/entity/person; CPC-fetch for technology), pre-gate coverage flag, bounded +
   resumable, defer-on-quota.

**Gate:** one end-to-end tick takes a subject through to a **human-gated focus** with essay +
media + references, published into the one site.

---

## Notes

- **Doc updates ride their phase.** The 🟡 builder docs are accurate for the current codebase,
  so each is updated by the phase that changes its subject: DESIGN ("Projects as Independent
  Research Units", "Why Three Databases") in Phase 34/38; CONTEXT/CLAUDE (project → focus
  lifecycle, tier table, CLI-first) in Phase 36/37; CONTRACT (entities/candidates/confirmed/
  essay schemas) in Phase 34/38 with a `contract_version` bump; README at Phase 37.
- **Deferred, independent of the reconfiguration:** D070 (hosting), D071 (GEO) — publishing the
  one site; D007/D028/D068 — corpus/tooling. Revisit their triggers in the Phase 33 pass.
