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

## Phase 33 — DEFERRED pass + archive the demo projects — CLOSED

1. Walk **every** `DEFERRED.md` entry against the focus model: subsume / close / keep /
   reframe. (D072→person focus, D079→technology focus, D078→mark/tech triage, D073→Decision 1
   already annotated; review D070/D071/D007/D028/D068 for whether "one site / one database
   set" changes their triggers.)
2. Archive `rectigon-westinghouse` and `westinghouse-electric-manufacturing-company` (demos).

Results 2026-07-03: DEFERRED went 11 → 9 open. **Closed two:** D075 (1929/30 design-mark image
backfill — verified complete, 0 missing across 1928/29/30) and D068 (promoted to Phase 37 — the
focus model dissolves auto-page-per-record, so the 2,026-patent-detail-page bloat has no cause).
**Annotated the rest** with reorientation status: D070 (deploy target is one site; the loop never
publishes), D071 (the five focus types map cleanly onto schema.org JSON-LD), D028 (mark-name →
serial is how a mark focus is created from a name), D074 (leads attach to a focus), D007
(unchanged; pressure reduced by applicant-fetch). Deviation from plan: rather than moving the
demos to `archive/`, they were `git rm`-ed per the 88c4a96 precedent (history preserves them);
their gitignored artifacts and built sites were deleted. Registry entities 9001/9004 cleared;
entity **9** and orphan **9003** deliberately left as the genuine Westinghouse duplicate pair for
Phase 35 to merge. Site rebuilt (portal: 0 projects, 10 reviews), `site check` clean, 1035 tests
passing.

**Gate:** `DEFERRED.md` reflects the reorientation (every open item has a trigger consistent
with focus areas) — PASSED; `projects/` holds only `annual-design-review` — PASSED.

---

## Phase 34 — Global registry + focus schema  ·  STRUCTURE_REVIEW §3, P1 — CLOSED

Decisions 1–3 settled 2026-07-03 (STRUCTURE_REVIEW §7).

1. Land the **canonical registry DuckDB** (entities, variants, `entity_relation` for M&A /
   succession, `entity_alias` for dedup, persons) as the single identity — plus the
   **git-tracked deterministic export** that buys back durability/diffability.
2. Add a **stored, immutable `slug`** to every type (fixes company slugs being derived from
   the current name); define `focus.json` (`type` + `subject` + `slug` + optional `selector`)
   and the `[[type:slug]]` cross-link resolver with **alias redirects**; unresolved link = build
   failure. CPC becomes a browse facet, not a focus.
3. Migrate the synthetic fixture + hermetic suite to the focus model.

Results 2026-07-10: **Schema** — `matchmaker/entities.py` DDL grew `slug`/`founded`/`dissolved`
on `company_entity` plus new tables `entity_relation` (kind ∈ renamed_to|merged_into|
acquired_by|succeeded_by|subsidiary_of), `entity_alias` (retired_id, **retired_slug**,
survivor_id) and `person_alias`; an idempotent `_migrate_add_registry_columns` upgrades legacy
DBs in place and backfills unique slugs. Deviation from the §3.1 sketch: alias tables carry a
`retired_slug` so a merged slug redirects even after the retired row is deleted — Phase 35 no
longer has to keep duplicate rows alive for URL stability. **Slugs are stored on insert** —
`build`, `commit_company`, and the backfill all assign collision-free slugs; the publisher's
render-time slugify of the *current* name is retired in Phase 37/38. **Export** — a deterministic
`COPY ... TO` CSV snapshot (fixed column + row order) regenerated on every registry write
(`build`/`clear`/`register`/`register-people`) and on demand via new `markery matchmaker export`;
lands at git-tracked repo-root `registry/` (the real registry exported: 33 entities). **Focus
model** — new `common/focus.py`: the one `focus.json` schema for all five types (selector gated to
technology foci), `focus/<type>/<slug>/` layout, and a layout-agnostic `LinkResolver` for
`[[type:slug]]` that follows alias chains (cycle-safe), leaves foreign namespaces (media/figure)
untouched, and raises `UnresolvedLink` on any owned dangling link — the build-failure discipline.
`registry_link_maps(conn)` derives entity/person targets + alias redirects straight from the DB.
**Fixture** — `_build_entities` now builds the canonical schema via `open_db`, stores a real slug,
and seeds an `entity_alias`; `build_synthetic_repo` writes an entity + mark focus. No companion-
facing CLI signature changed, so `contract_version` stays 1.4 (the substantive contract/DESIGN
"one database set" edits ride Phase 38). +21 tests (`test_focus.py`, `test_focus_fixture.py`,
updated `test_entities.py`); 1056 hermetic tests passing.

**Gate:** one entity per real-world firm (deferred to Phase 35's dedup; schema + alias redirects
now support it) — PARTIAL; a focus references ids/slugs and declares nothing — PASSED;
cross-links resolve through aliases — PASSED; suite green on the new model — PASSED.

---

## Phase 35 — Dedup entities  ·  STRUCTURE_REVIEW P2

1. Merge duplicate identities (the four Westinghouses, etc.) into single ids via
   `entity_alias`, with a mapping report; retired slugs redirect.
2. **Distinguish dedup-merge from succession/M&A** — records that were always the same firm
   get merged; genuinely distinct firms where one succeeded/absorbed the other (Westinghouse
   Electric & Mfg Co → Westinghouse Electric Corporation, 1945; Greenfield Tap and Die → TRW →
   Kennametal) are recorded in `entity_relation`, **never collapsed**. Both may earn their own
   entity focus.

**Gate:** no duplicate identities; no succession wrongly collapsed; richness/seed resolve one
Westinghouse; old slugs still resolve.

---

## Phase 36 — Migrate annual-design-review to foci  ·  STRUCTURE_REVIEW P3

1. `essays/*.md` → **mark foci**; year galleries → the **browse/index** layer.
2. Retire the `annual-review` (and `match-review-essay`, `gallery-exploration`) project types.

**Gate:** annual-design-review renders as mark foci + browse indexes; `site check` clean.

---

## Phase 37 — Publisher: one site  ·  STRUCTURE_REVIEW P4

1. Portal-of-projects → **one site** of foci + indexes, cross-linked (mark↔entity↔patent↔
   person↔technology).
2. **Resolves D068** (promoted here from DEFERRED, Phase 33): the "2,026 patent detail pages"
   bloat dissolves — a patent gets a page only when *promoted to a patent focus*; the rest
   appear in browse indexes/galleries. No auto-page-per-record.

**Gate:** a single site; cross-links resolve; no per-project site subtrees; no auto-generated
detail page per corpus record.

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
- **DEFERRED after the Phase 33 pass (9 open):** D070 (hosting) + D071 (GEO) — publishing the one
  site; D007/D028 — corpus tooling; D074 (eBay leads); D072/D079 subsumed as person/technology
  focus types; D078 reframed as mark/technology triage; D073 folded into Decision 1.
  **Closed in the pass:** D075 (1929/30 image backfill — verified 0 missing), D068 (promoted to
  Phase 37; the focus model dissolves auto-page-per-record).
