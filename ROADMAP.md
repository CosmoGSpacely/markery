# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.
Phases 14–15 closed 2026-06-01/2026-05-24. Archived to `archive/ROADMAP-2026-06-03.md`.
Phases 16–18 closed 2026-06-06. Archived to `archive/ROADMAP-2026-06-06.md`.
Phase 19 closed 2026-06-07. Archived to `archive/ROADMAP-2026-06-07.md`.
Phases 20–22 closed 2026-06-14. Archived to `archive/ROADMAP-2026-06-14.md`.
Phase 23 closed 2026-06-18 (P3/D028 deferred to `DEFERRED.md`). Archived to `archive/ROADMAP-2026-06-18.md`.
Phases 24–26 closed 2026-06-23 (24 P1–P5 + 26 done; 24 P6/P7 and 25 deferred → D070–D072). Archived to `archive/ROADMAP-2026-06-23.md`.

---

## Re-centering (2026-06-23)

A stock-take found Markery is a strong **toolkit** (clean CLI, specialist boundaries, data
layer) but thin on the thing it's meant to be: an **agentic pattern that grows a research
platform with little supervision**. The orchestration layer (markery-langgraph) is ~3% of the
code and runs one workflow; the autonomy lives in plan docs, not code. The next phases build
the missing layer on solid foundations, in this order: **harden the tests → make the library
real → build the discovery loop → build the spawning pipeline.** Each phase is fully specced
in its `*_REVIEW.md`; the roadmap entries are the sequence + gates.

Foundations → backbone → acquisition → autonomous growth. After Phase 27 (hermetic tests),
the `projects/` and `site/` trees can be archived and rebuilt from the improved library/loops.

---

## Phase 27 — Test hermeticity & CI coverage  ·  plan: `TESTS_REVIEW.md`

**Trigger:** the suite couples to real `projects/`/corpus data (can't archive `projects/`;
CI validates data, not code) and coverage is a mediocre 53% partly inflated by that coupling.
**Why first:** it's the safety net for every later refactor (library, loops), and the
hermetic-MVO rewrite is the prerequisite for archiving `projects/` and "starting again."

1. **Hermetic MVO + dataqa split** — rewrite `test_mvo` against a synthetic project + temp
   DBs; move real-corpus checks under an optional `@pytest.mark.dataqa` lane. Suite passes
   with `projects/` absent.
2. **Coverage** — hermetic end-to-end `build_site`/`build_all`/`check_site` test (the 299-miss
   orchestrator), CLI-dispatch tests, mocked-HTTP source adapters, enhancement transforms.
3. **Ratchet** `--cov-fail-under` 50 → 60 → 70 as coverage lands.

**Gate:** `pytest` green with `projects/` moved aside; coverage non-decreasing and floor raised.

---

## Phase 28 — Real digital library  ·  plan: `LIBRARY_REVIEW.md`

**Trigger:** "library" is fragmented — text works are global, P2 media is per-project (1 item),
record images live in DBs; no single rights-curated catalog.
**Why second:** it's the data backbone both loops depend on; refactor it on the now-hermetic
suite, before the loops populate/consume it.

1. **Global media collection + catalog** — `library/media/` + `catalog.jsonl`; migrate the P2
   item; `media.py`/`media-list` go global.
2. **Project references + build** — projects reference library items; publisher resolves refs
   into `site/<project>/`. Records (mark images, patent figures) stay in the DBs.
3. **Unify listing/search** across works + media.

**Gate:** one global rights-curated library (works + media); a project references an item and
the publisher renders it with attribution; `site check` green.

---

## Phase 29 — Continuous historian discovery loop  ·  plan: `HISTORIAN_REVIEW.md`

**Trigger:** acquisition (media/literature/figures) is hand-driven; the discovery autonomy is
unbuilt.
**Why third:** it's the acquisition engine that **populates the library** (Phase 28), and the
first real agentic loop in markery-langgraph.

1. PD media adapters (D069: LoC/NARA/DPLA/IA) + Chronicling America newspapers.
2. Discovery log + historian relevance scoring; WorldCat/ILL book pipeline; eBay leads.
3. The continuous loop (`discovery_graph.py`): seed → discover → score → acquire/gate/log,
   with dedup, budgets, and human gates; scheduled.

**Gate:** one loop tick discovers, acquires a free item into the library, queues a want, logs
a lead, and human-gates a purchase/ILL on a real project; `site check` clean.

---

## Phase 30 — Annual-review → project spawning pipeline  ·  plan: `PUBLISHER_REVIEW.md`

**Trigger:** projects are created by hand; the "platform grows itself" capability is unbuilt.
**Why last (the capstone):** it's the flagship agentic demonstration — it references the
library (28), benefits from discovery having populated it (29), and rides the hermetic suite
(27). Most complex (multi-specialist, EPO-quota), so it lands on solid foundations.

1. Technological-mark triage (`trademark tech-marks`: US-class gate + free-model goods rule).
2. Seed match → good-match filter → CPC-subclass expansion + re-match.
3. Richness branch (technology-area vs small-company) → human-gated project spawn → publish.
4. The loop (`spawn_graph.py`): seed → … → spawn → publish, with a dedup ledger, EPO budget,
   and the single human gate at project creation; scheduled.

**Gate:** one end-to-end tick takes a technological design mark through to a human-gated
project spawn and a clean portal build.

---

## Notes

- **No `DATABASE_REVIEW` yet.** Data-layer improvements (more media/figures, corpus expansion
  beyond the curated slice, auto entity registration) are folded into the loops: acquisition
  in Phase 29, corpus/subclass expansion + entity registration in Phase 30. Promote a
  standalone DB phase if the data model itself needs rework.
- Deferred, independent of these phases: D070 (hosting), D071 (GEO), D072 (People), plus
  D007/D028/D068/D069.
