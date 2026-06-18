# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.
Phases 14–15 closed 2026-06-01/2026-05-24. Archived to `archive/ROADMAP-2026-06-03.md`.
Phases 16–18 closed 2026-06-06. Archived to `archive/ROADMAP-2026-06-06.md`.
Phase 19 closed 2026-06-07. Archived to `archive/ROADMAP-2026-06-07.md`.
Phases 20–22 closed 2026-06-14. Archived to `archive/ROADMAP-2026-06-14.md`.

---

## Phase 23 — Free-model live project builds, tooling, and langgraph isolation

**Trigger:** Phase 22 complete. The OpenRouter free model `openai/gpt-oss-120b:free` is wired (`common/providers.py` model-id routing) and proven on the four-provider cross-provider benchmark — 6/6 on the deterministic MVO validator, judgments matching ground truth, at $0 (archived `archive/MODEL-REVIEW-2026-06-14.md`).

**Scope:** Take the model-agnosticism result from fixtures to real research. Build **two new research projects end-to-end using the free model alone for every LLM step** (candidate inference, essay drafting), proving the free model carries genuine project work — not just benchmark cards. Add the TSDR text-search tooling both project setups need to resolve marks to serials (D028). Properly isolate the markery-langgraph environment (D057).

Both projects are deliberately **tightly subclass-scoped** to keep the EPO patent corpus small and the build tractable: photographic equipment to **G03B**, precision tools to **G01B**. Only LLM steps run on the free model; patent/trademark **data fetch is EPO/USPTO-API-bound regardless of model** and paced by quota. The free model is rate-limited upstream (Venice) — runs retry 429/5xx with backoff; if a model is throttled mid-build, pause and resume rather than switching providers (switching would defeat the "free model alone" test).

**Goal state:** `photographic-equipment` and `precision-tools` each have ≥1 confirmed pair with a free-model essay that validates 8/8, a site that builds clean and passes `markery site check`, and a `markery tokens report` showing $0 for all LLM work; `markery trademark search-tsdr <mark-text>` resolves a mark name to serial/owner/filing without a manual external lookup; markery-langgraph runs its suite from its own isolated environment. After this phase, **D007 is the sole remaining deferred item.**

---

### P1 — D025: Photographic equipment project (Kodak / Ansco / Graflex, G03B, free model)

1. `markery project init photographic-equipment`; set `project.json` `model` to `openai/gpt-oss-120b:free` and `class_hints` to `["G03B"]`.
2. Entity registry — `entities.csv` (Eastman Kodak Company, Ansco / General Aniline & Film, Graflex Inc., Blair Camera Company) and `variants.csv` (patent-assignee and trademark-owner strings); `markery matchmaker build --data-dir projects/photographic-equipment`; `markery matchmaker validate-variants` clean.
3. `markery patent coverage-check --classes G03B --year-start 1890 --year-end 1940` before any fetch; then `markery patent build --classes G03B --year-start 1890 --year-end 1940` (quota-paced over multiple days as needed).
4. Resolve and fetch the target marks (KODAK, BROWNIE, KODACHROME, AUTOGRAPHIC, SPEEDEX, READYSET, GRAFLEX, SPEED GRAPHIC) via `markery trademark search-tsdr` (P3) → `markery trademark fetch <serial>`; set `focus_serials`.
5. `markery match photographic-equipment` to generate candidates; review with the free model — `markery historian card --infer` / `digest --infer` (model from `project.json`); confirm pairs via `markery matchmaker confirm`.
6. Draft essays with the free model (`markery historian draft`); each must validate **8/8** (`markery historian validate`). Human-finalize interpretive honesty where the validator can't (per the model-agnosticism boundary).
7. `markery site build photographic-equipment`; `markery site check photographic-equipment` exits 0.
8. `markery tokens report` over the project's token log — confirm $0 for all LLM steps; record token counts and any free-tier rate-limit interruptions in `projects/photographic-equipment/RESEARCH.md`.

### P2 — D026: Precision tools project (Snap-on / Starrett / Brown & Sharpe, G01B, free model) — CLOSED

Same end-to-end sequence as P1, with:
- Entities: Snap-on Tools Company, L.S. Starrett Company, Brown & Sharpe Manufacturing, Illinois Tool Works.
- Marks: SNAP-ON, STARRETT, and the others surfaced via `search-tsdr`.
- **CPC: `G01B` only** (measuring instruments — Starrett/Brown & Sharpe micrometers and gauges), 1910–1940. (B25B / B23B remain a future pass per D026.)
- Model: `openai/gpt-oss-120b:free` for all LLM steps; site builds clean; `markery tokens report` shows $0.

Results 2026-06-17: Built `precision-tools` end-to-end on `openai/gpt-oss-120b:free` — **3 confirmed pairs (L.S. Starrett), all essays validate 8/8, site clean (11 pages / 106 links / 0 broken), $0.0000** over 20 logged token records. Deviations from the plan: the marks were already in the local `trademarks.duckdb`, so `search-tsdr` (P3) was not needed — `suggest-variants` resolved them (14/14). The G01B 1910–1940 fetch loaded 3,766 patents in one clean pass (the P1 throttle fix held). Of the four entities, only Starrett and ITW had both a mark and a patent locally; Brown & Sharpe had patents but no local mark, Snap-on had marks but no G01B patents. The project anchored on Starrett (never acquired). **Two new findings:** (1) a *period-ownership anachronism* class the validator cannot catch — the free model confirmed MAGNAFLUX/DYKEM/DE VILBISS on ITW patents because the DB owner string reads `ILLINOIS TOOL WORKS INC.` today, but ITW acquired those brands decades later (Magnaflux 1987); rejected by the human gate on period-ownership grounds; (2) the three Starrett pairs are *owner-and-era*, not goods matches — the figurative mark's goods are hand tools, not the measuring instruments the patents cover — and every free-model "Connection" overclaimed an embodiment link, corrected by hand with editorial notes (as in P1). Also fixed a publisher bug this project surfaced: figurative marks (`trademark = NULL`) crashed `site build` in `landing.py`/`essays.py`/`queries.py`; now fall back to "(figurative)". Test count unchanged (publisher suite 145 green). D026 closed.

### P3 — D028: `markery trademark search-tsdr <mark-text>`

1. Implement a text-search path that takes a mark name (e.g. "KODACHROME", "STARRETT") and returns matching serial numbers, owner names, and filing dates — using the USPTO trademark API (`developer.uspto.gov/trademark-api`) since TSDR's primary endpoint is serial-keyed. Falls back gracefully (clear message) when the API is unavailable.
2. Register under `markery trademark search-tsdr`; MVO contract in `tests/benchmarks/mvo.md`; tests (mocked HTTP, like `tsdr_client`).
3. This is the enabler for P1/P2 step 4 — it removes the manual external-TSDR-lookup bypass. If it lands after P1/P2 begin, the documented manual workaround (external search + `markery trademark fetch <serial>`) covers the gap.

### P4 — D057: markery-langgraph isolated environment — CLOSED

1. `python3.12-venv`/`ensurepip` is unavailable and `sudo` was the blocker; establish isolation via a pip-installable manager that bundles its own pip — `virtualenv` (or `uv` if adopted) — creating `markery-langgraph/.venv` independent of the markery venv.
2. Reinstall `langgraph-markery` (`pip install -e .`) into the isolated env; confirm the langgraph suite (30 tests) passes from it; `config.check_contract` resolves `MARKERY_ROOT` via the D056 resolver.
3. Update `markery-langgraph/README.md` / `CLAUDE.md` setup to document the isolated-env step. Close D057.

Results 2026-06-18: The pre-existing `markery-langgraph/.venv` was the broken stub from the D057 blocker — `python -m venv` had created it but `ensurepip` failed, so it had a python symlink but **no pip**. Bootstrapped `virtualenv` 21.5.1 (bundles its own pip) into the markery venv, removed the stub, and recreated `.venv` with a working pip 26.1.2. Installed `langgraph-markery` editable with dev extras (`pip install -e '.[dev]'` → langgraph, anthropic 0.109.2, duckdb 1.5.4, pytest 9.1.0). **All 30 tests pass from the isolated env.** Verified true isolation: `import markery` fails from `.venv` (the repo only shells out to the CLI, never imports it), `config.resolve_markery_root()` finds the sibling `/home/wccogswell/markery` via the D056 resolver, and `check_contract` confirms contract 1.1. Updated `markery-langgraph/README.md` and `CLAUDE.md` to document the virtualenv setup and fixed a stale contract-version reference (1.0 → 1.1) in the README. D057 closed.

---

### Phase Gate

P1 PASSED when: `photographic-equipment` has ≥1 confirmed pair whose free-model essay validates 8/8; `markery site build` exits 0 and `markery site check` passes; every LLM step ran on `openai/gpt-oss-120b:free` and `markery tokens report` shows $0 for them; D025 closed.

P2 PASSED when: the same holds for `precision-tools` (CPC G01B); D026 closed. — PASSED

P3 PASSED when: `markery trademark search-tsdr <mark-text>` returns serial/owner/filing for a known mark and exits non-zero with an actionable message when unavailable; MVO contract + tests present; D028 closed.

P4 PASSED when: the markery-langgraph suite runs green from an isolated environment; setup docs updated; D057 closed. — PASSED

Phase PASSED when P1–P4 pass and `DEFERRED.md` is updated. After this phase, **D007 (`markery patent bulk-import`, PatentsView) is the only remaining open deferral.**

---
