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
the missing layer on solid foundations, in this order: **harden the tests → fix the database →
make the library real → build the discovery loop → build the spawning pipeline.** Each phase is
fully specced in its `*_REVIEW.md`; the roadmap entries are the sequence + gates.

Foundations → backbone → acquisition → autonomous growth. After Phase 27 (hermetic tests),
the `projects/` and `site/` trees can be archived and rebuilt from the improved library/loops.

---

## Phase 27 — Test hermeticity & CI coverage  ·  plan: `archive/TESTS_REVIEW-2026-06-24.md` — CLOSED

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

Results 2026-06-24 (P1 — Hermetic MVO): added `MARKERY_ROOT`/`MARKERY_DATA_DIR`
env overrides to `common/config.py` so the CLI can be pointed at a synthetic repo;
added `tests/fixtures/synthetic.py` (temp corpus DBs + a synthetic project,
invented serials/patents) and rewrote `test_mvo.py` so card/digest/validate/scaffold
run hermetically against it. Real-corpus checks (`trademark inspect`, librarian,
all of `test_contract.py`'s DB/JSONL classes, `test_librarian`'s MVO class) moved
to a new `@pytest.mark.dataqa` lane (registered in `pyproject.toml`); fixed
`test_phase11_commands.py` to use a synthetic entities DB; made
`publisher/queries.py` image getters degrade gracefully when a DB file is absent.
CI split into a hermetic `test` job (`-m "not dataqa"`, +coverage) and a `dataqa`
job (`-m dataqa`). **Gate met:** hermetic lane is 744 passed with `data/` and
`projects/` moved aside; coverage held at 53% (floor 50). Decisions settled this
session: hermetic lane needs neither real DBs nor `projects/`; record images will
externalize to files (Phase 28 P3); the large DBs become gitignore+rebuild
artifacts (Phase 28 P3).

Results 2026-06-24 (P2–P5): **P2** — `tests/specialist/publisher/test_build_orchestrator.py`
drives the real `build_site`/`build_all`/`check_site` against the synthetic repo
(extended to the full publisher schema + a 1px PNG blob + a second annual-review
project); build.py 10%→78%, check.py 66%, reviews.py 86%. **P3** —
`test_cli_dispatch.py` runs every area/subcommand `--help` in-process (caught and
fixed a real crash: `markery historian --help` had an unescaped `%`); mocked-urlopen
tests for the ia/gutenberg/wikipedia source adapters; `test_cli_commands.py` drives
read-only commands (status, project onboard, historian prepare, site build-all+check)
in-process; markery/cli.py 20%→61%. **P4** — `test_enhancement.py` (upscale Lanczos
fallback, DB-backed gallery, binarize via importorskip). **P5** — ratcheted
`--cov-fail-under` 50→65; documented the hermetic-vs-dataqa split in `CLAUDE.md`.
Also fixed two latent test-isolation bugs in `test_phase11_commands.py` (card/scaffold
patched `config.DB` by rebinding, which only worked if `historian.cli` was first
imported under the patch — now patch the module's `DB` directly). **Gate met:** the
hermetic lane is **891 passed with `data/` and `projects/` moved aside**, coverage
**68%** (floor raised to 65); full suite 947 passed. `projects/` and `site/` are now
archivable. `TESTS_REVIEW.md` archived to `archive/TESTS_REVIEW-2026-06-24.md`.

**Gate:** `pytest` green with `projects/` moved aside; coverage non-decreasing and floor raised. — PASSED

---

## Phase 28 — Database layer  ·  plan: `archive/DATABASE_REVIEW-2026-06-24.md` — CLOSED

**Trigger:** the corpus is a curated, human-seeded slice committed as ~70 MB binaries, with
partial provenance (records lack a load/refresh timestamp; status can go stale), a hand-built
entity registry (38), and image blobs inside the DBs.
**Why second:** it's the deepest backbone; its asset-storage decision must be made *with* the
library refactor, and auto entity registration is a hard prerequisite for the spawning pipeline.

1. **Provenance + freshness** — record `fetched_dt`/`source`; `… refresh` for status; a real
   coverage manifest.
2. **Auto entity registration (companies + people)** — corpus owners/assignees →
   `company_entity`/variants (human-confirm), removing the hand-CSV requirement for new
   projects; and model **people** (inventors from `patent_inventors`, notable founders) as
   first-class data-layer entities with stable slugs — the *data-model* half of D072 (its
   essay/rendering half stays deferred).
3. **Asset storage + commit policy** — resolve blobs-in-DB vs files (with Phase 29); decide
   commit-vs-rebuild; document the rebuild recipe; add a synthetic test fixture.
4. **Coverage/expansion hooks** — a queryable coverage model the loops consult before fetching
   (EPO/TSDR; evaluate D007 PatentsView).

Results 2026-06-24: **P1** provenance (`fetched_dt`/`source` on patents+case_file,
self-migrating; `markery {patent,trademark} coverage` manifest, degrades on
un-migrated DBs). **P2** auto entity registration (`matchmaker/autoregister.py`;
`matchmaker register` companies + `register-people` inventors→`person_entity` with
stable slugs; removes hand-CSV). **P3** externalized record images to files
(`common/assets.py`; `mark_images`/`patent_figures` → `file`+`sha256`; real corpus
migrated 619 marks + 38 figures → 14 MB; DBs+`data/assets/` now gitignored
rebuildable artifacts; pre-migration snapshot archived; `data/REBUILD.md`). **P4**
queryable coverage model (`coverage_query`/`window_covered`/`missing_year_spans`;
`markery patent coverage --class X --year-start/-end`) the loops consult before
fetching — the EPO/TSDR expansion *fetch* itself lands in Phases 30–31. Hermetic
lane 922 passed, coverage 69% (floor 65); dataqa lane green on the migrated DBs.
Deferred: D007 PatentsView (unchanged); the asset/library interaction continues in
Phase 29.

**Gate:** records carry provenance + a refresh path; companies **and people** auto-register
from the corpus (human-confirmed, stable slugs); the asset-storage + commit decisions are made
and documented; existing specialist commands unregressed. — PASSED

---

## Phase 29 — Real digital library  ·  plan: `archive/LIBRARY_REVIEW-2026-06-24.md` — CLOSED

**Trigger:** "library" is fragmented — text works are global, P2 media is per-project (1 item),
record images live in DBs; no single rights-curated catalog.
**Why third:** it's the asset backbone both loops depend on; refactor it on the hermetic suite
and the Phase 28 asset-storage decision, before the loops populate/consume it.

1. **Global media collection + catalog** — `library/media/` + `catalog.jsonl`; migrate the P2
   item; `media.py`/`media-list` go global.
2. **Project references + build** — projects reference library items; publisher resolves refs
   into `site/<project>/`. Records (mark images, patent figures) stay in the DBs.
3. **Unify listing/search** across works + media.

Results 2026-06-24: **P1** global `library/catalog.jsonl` (loop-safe flat JSONL —
in-memory dedup by id/source_url/sha256, atomic rewrite; D073 trigger for a DB) +
global `library/media/` (`media-acquire`/`media-list`/`catalog` go global; binaries
gitignored, sha256 + snapshot for durability). **P2** `references/library.jsonl` +
`librarian use <id> --project`; `publisher` resolves refs → catalog → copies media
into `site/<project>/media/` + `media_index`. **P3** `librarian list` unifies works +
media via the catalog (`--kind`). **P4** (loop wiring) folded into Phase 30 — the
primitives (`media.acquire_commons` global+dedup, `catalog.add_ref`) are ready.
Hermetic lane 940 passed, coverage 70%. Records (mark images, patent figures) stay
in the DBs as files per Phase 28. `LIBRARY_REVIEW.md` archived to
`archive/LIBRARY_REVIEW-2026-06-24.md`.

**Gate:** one global rights-curated library (works + media); a project references an item and
the publisher renders it with attribution; `site check` green. — PASSED

---

## Phase 30 — Continuous historian discovery loop  ·  plan: `HISTORIAN_REVIEW.md`

**Trigger:** acquisition (media/literature/figures) is hand-driven; the discovery autonomy is
unbuilt.
**Why fourth:** it's the acquisition engine that **populates the library** (Phase 29) using the
database's coverage/provenance hooks (Phase 28), and the first real agentic loop in
markery-langgraph.

1. PD media adapters — LoC/NARA/DPLA/IA (**closes D069**) + Chronicling America newspapers.
2. Discovery log + historian relevance scoring; WorldCat/ILL book pipeline; eBay leads.
3. The continuous loop (`discovery_graph.py`): seed → discover → score → acquire/gate/log,
   with dedup, budgets, and human gates; scheduled.

**Gate:** one loop tick discovers, acquires a free item into the library, queues a want, logs
a lead, and human-gates a purchase/ILL on a real project; `site check` clean.

---

## Phase 31 — Site design pass + rebuild annual-review project/site  ·  plan: TBD (stub)

**Trigger:** `projects/` and `site/` were archived 2026-06-24 (see
`archive/PROJECTS-ARCHIVED-2026-06-24.md`); the first real rebuild is also the moment
to refresh the site design — and it must land **before** the spawning pipeline (32) so
spawned projects publish into the refreshed design rather than the old one.

Brief: do another **site design pass** (chrome, cards, timeline, typography — carry
forward the open items from the archived `SITE-REVIEW`), **then rebuild the
annual-review project and its site** on the improved database/library. Write the full
plan to a `SITE-REVIEW.md` when this phase opens.

**Gate:** the annual-review project rebuilds against the new data/library; the refreshed
design renders; `site check` clean.

---

## Phase 32 — Annual-review → project spawning pipeline  ·  plan: `PUBLISHER_REVIEW.md`

**Trigger:** projects are created by hand; the "platform grows itself" capability is unbuilt.
**Why last (the capstone):** it's the flagship agentic demonstration — it auto-registers
entities (28), references the library (29), benefits from discovery having populated it (30),
publishes into the refreshed design (31), and rides the hermetic suite (27). Most complex
(multi-specialist, EPO-quota), so it lands on solid foundations.

1. Technological-mark triage (`trademark tech-marks`: US-class gate + free-model goods rule).
2. Seed match → good-match filter → CPC-subclass expansion + re-match.
3. Richness branch (technology-area vs small-company) → human-gated project spawn → publish.
4. The loop (`spawn_graph.py`): seed → … → spawn → publish, with a dedup ledger, EPO budget,
   and the single human gate at project creation; scheduled.

**Gate:** one end-to-end tick takes a technological design mark through to a human-gated
project spawn and a clean portal build.

---

## Notes

- Sequence: **27 Tests → 28 Database → 29 Library → 30 Discovery loop → 31 Site design +
  rebuild → 32 Spawning pipeline** (foundations → backbone → acquisition → design refresh →
  autonomous growth). `projects/` and `site/` were archived 2026-06-24 (Phase 27 made the
  suite hermetic); they rebuild in Phases 31–32. The design pass (31) precedes spawning (32)
  so auto-spawned projects publish into the refreshed design.
- **When is a real project/site first needed?** Not until the end. Phases 28–30 validate
  against the hermetic synthetic-fixture project (`tests/fixtures/synthetic.py`), which
  already builds a full site + portal and passes `site check` — so their "site check green"
  gates are satisfiable without a rebuilt real project. The first phase that *requires* a
  real, non-synthetic project end-to-end is **Phase 31** (the design refresh + annual-review
  rebuild); **Phase 32** (the spawning pipeline) then auto-creates further projects on the
  refreshed design. Net: the corpus/library work (28–30) proceeds with `projects/`/`site/`
  archived.
- Deferred, independent of these phases: D070 (hosting), D071 (GEO), D072 (People), plus
  D007/D028/D068/D069.
