# PATENT_REVIEW — Automated patent coverage for the spawn loop

Status: **planning** · opened 2026-06-30 · drives Phase 32 P2b + a `patent build` extension.
Archive on completion to `archive/PATENT_REVIEW-<date>.md`, then `git rm PATENT_REVIEW.md`.

---

## 1. Problem

The local patent corpus was built from ~118 **CPC class×year** fetch windows targeting the
first-generation product's focus (electronics/radio: H01J/H04B ~80–100% complete vs EPO).
Power/mechanical/chemical classes are near-empty (1915–1935: H01H 36/11,681 ≈ 0.3%, H02M
27/1,008, H01M 3/2,716). So `matchmaker richness` / `seed-pairs` are a **floor distorted by
corpus coverage**, not a true measure — see [[project_patent_corpus_cpc_bias]] and the ROADMAP
P2b correction.

Consequence for the spawn loop (Phase 32 P4): a spawned project is only as evidenced as the
corpus happens to be for that entity. We proved the fix manually — fetching H01H (breakers)
and H02M/H02J (rectifiers) took De-Ion from ~2 to 1,237 seed pairs and RECTIGON to 253
rectifier pairs — but that required **domain knowledge of each entity's CPC classes**
(`patent build --classes H01H …`). That does not generalize.

## 2. Core idea — fetch by applicant, not by class

Don't guess an entity's CPC classes. EPO supports applicant search (`pa="<name>"`), proven in
the corpus-bias probe (`epo_client.search` with a `pa=` CQL returns the entity's patents across
**all** classes). So the loop asks EPO for *this entity's own patents* over the mark era —
breakers, rectifiers, whatever they actually hold — bounded and deduped. No class-guessing, no
over-fetching unrelated patents. This turns the manual De-Ion/RECTIGON fix into an automatic
property of every spawn.

## 3. Design

Two touch-points in the spawn loop, plus one new primitive.

**Primitive — `markery patent build --applicant "<name>"`.** Build CQL
`pa="<name>" AND pd within "<y0>0101,<y1>1231" AND pn=US` (vs the existing `cpc=...`), reusing
the same paging / insert-if-not-exists / `--resume` / `data/patents_fetch_log.json` machinery.
Accept repeated `--applicant` (one per entity variant name, OR-ed) to handle spellings.

**Pre-gate — honest coverage flag (count-only, no fetch).** Replace the current local thin/ok
heuristic with a real EPO signal: one `pa=<entity> pd within <era>` **count** (like
`coverage-check`, range 1-1) vs the local count. The proposal shows the truth, e.g.
*"Westinghouse — EPO ~1,900 in 1915–1935; corpus 412; approving fetches ~1,500 (budget N)."*
Cost/commitment (the EPO spend) is thus surfaced at the **single existing human gate**.

**Post-gate — bounded fetch, then build.** For each approved entity:
`patent build --applicant <variants> --year-start <era-low> --year-end <era-high> --resume`,
capped by a budget, **then** match → discovery → essay → site, so the project builds on the
enriched corpus.

## 4. Bounding (EPO is quota-bound — this is the crux)

- **Year window:** mark filing era ± `COVERAGE_WINDOW` years (proposed default **±10**).
- **Per-entity cap:** pre-flight count; if over `COVERAGE_MAX_PATENTS` (proposed default
  **2,500**), narrow the window (or top years) rather than fetch unbounded.
- **Daily-quota guard + resume:** EPO has a ~daily ceiling. The fetch log already makes runs
  restartable; on quota exhaustion the loop **defers the remainder** and marks the project
  *"coverage partial — re-run to complete"* (same graceful-degradation principle as D077). A
  batch of approved entities is a **resumable fetch queue**.
- **Opt-out:** gate the whole fetch behind `--allow-fetch` (default off) so a spawn can also run
  corpus-only when EPO is unavailable or quota is precious.

## 5. Work plan

### P1 — `patent build --applicant` primitive
1. Add an applicant CQL builder beside `_cql` (`patent/build.py`); thread `--applicant` (repeatable)
   through `cmd_build` and `build()`; mutually-inclusive with the existing class mode.
2. Reuse `_fetch_window`/paging/`--resume`/fetch-log unchanged (window keyed by applicant+years).
3. Tests: hermetic, mocked `EPOClient.search` — CQL shape, paging, dedup/idempotency, fetch-log
   record. **Gate:** `patent build --applicant "X" --year-start --year-end` fetches & inserts
   against a mocked EPO; re-run is a no-op via `--resume`.

### P2 — pre-gate coverage count → honest proposal flag
1. `matchmaker`/`patent` helper: `entity_epo_count(name, y0, y1)` (one `pa=` count) + local count.
2. Wire into the spawn `assemble` node: each proposal carries `{epo_count, local_count, gap,
   coverage: ok|thin|gap, est_fetch}`; tiering uses the real gap, not the local heuristic.
3. Tests: mocked EPO count → flag/tier correctness. **Gate:** proposals show a real EPO-vs-local
   coverage line; a known-thin entity (power-class) flags `gap`.

### P3 — post-gate bounded fetch in `spawn_approved` (langgraph)
1. Tool wrapper `run_patent_coverage(entity_variants, y0, y1, max)` → `patent build --applicant …`.
2. In `spawn_approved`, after `seed-project`/`build-entities` and **before** `match`: if
   `--allow-fetch`, run the bounded fetch (resume; defer + mark `coverage_partial` on quota).
3. Re-`seed-pairs`/`match` reflect the enriched corpus automatically.
4. Tests: mocked wrapper — fetch called with the entity's variants + era window; `coverage_partial`
   recorded on a simulated quota stop; skipped when `--allow-fetch` off. **Gate:** a clean live
   spawn of a power-era entity acquires its real classes and the preview shows them.

### P4 — (scale, may defer) persistent fetch-drain service
A sibling to the discovery loop: enqueue applicant-fetch jobs at gate time; a scheduler drains
within daily quota; projects (re)build as their corpus fills. Ship P1–P3 inline first; promote to
the queue only if batch sweeps exceed daily quota in practice. (Likely a DEFERRED entry, not P4.)

## 6. Relationship to D077 — CLOSED 2026-06-30

The post-gate fetch (P3) and the discovery/relevance loop share the same **resumable +
graceful-degradation** spine: bounded external calls, defer-on-limit, mark-partial, re-run to
complete. **D077 is now closed** (free-model fallback chain `config.model_chain` + `llm.call_chain`,
free-first with an opt-in paid backstop via `MARKERY_ALLOW_PAID`; relevance/draft routed through it;
model-outage items logged `unscored` and re-scored on a later discovery tick). P3 reuses the same
pattern for the **corpus/EPO** limit, so both external dependencies degrade identically — the loop
is robust to LLM rate limits today and to EPO quota once P1–P3 land.

## 7. Decisions to confirm before P1

- **Budget defaults:** `COVERAGE_WINDOW = ±10y`, `COVERAGE_MAX_PATENTS = 2500/entity`. (Adjustable.)
- **Fetch timing:** lazy per-approved-entity (cheaper; flag is an estimate) **vs** batch-fetch the
  whole approved set at gate time (accurate flags, front-loads quota). Plan assumes **lazy**.
- **`--allow-fetch` default OFF** (spawn is corpus-only unless explicitly told to grow the corpus).

## 8. Test & quota notes

All hermetic tests mock `EPOClient.search` (no live EPO). One **live** validation per phase gate
(bounded, `--resume`). Contract: `patent build --applicant` is a new `markery` surface; if the
spawn loop shells it, bump `MANIFEST.json` and `langgraph_markery` `_EXPECTED_VERSION` to 1.5.
