# Annual-Review → Project Spawning Pipeline — Plan

A plan to grow the **annual design-mark review** (Phase 24 P4) into a continuous discovery
pipeline that, for *technological* design marks, looks for matching patents, expands the
promising patent subclasses to find more matches, and then **spawns a new project** — a
**technology-area project** when the subclass is rich, or a **small company project** when it
isn't. Each stage is owned by an existing specialist so the whole thing can run unattended in
**markery-langgraph** (which only shells out to the `markery` CLI).

Status: planning. No code yet. Archived to `archive/` on completion.

---

## 1. Goal

From the design marks surfaced by the annual reviews, automatically find the ones worth
turning into research projects:

```
annual-review design marks
   └─(1) keep only the TECHNOLOGICAL ones
        └─(2) seed a patent match for each (owner + era)
             └─(3) keep only those with GOOD matches
                  └─(4) expand the matched patent SUBCLASS(es) → re-match → more pairs
                       └─(5) rich subclass?  → TECHNOLOGY-AREA project
                             sparse?         → SMALL COMPANY project
                                  └─(6) scaffold, populate, publish to the portal
```

The pipeline is continuous, idempotent, budget-aware (EPO quota is the scarce resource), and
**human-gated at the one irreversible step — creating a new project**.

---

## 2. Current state (what we build on)

- **Annual reviews (P4)** already enumerate design marks per year (`mark_draw_cd LIKE '3%'`,
  by filing month) with owner, goods/services, and images — the input surface for stage 1.
- **`markery match <project>`** generates patent–trademark candidate pairs from
  `entities.duckdb`, with `--entity <name>`, `--serials <serial …>`, `--auto-fetch` (pull the
  owner's patents from EPO if missing), `--min-score`, and `--all` (→ `matches_all.jsonl`).
- **`markery matchmaker`** — `suggest-variants` (rank assignee/owner strings for a canonical
  name), `build` (register entities/variants), `confirm`.
- **`markery patent`** — `build` (EPO OPS), `coverage-check` (dry-run expected counts before a
  sweep), `search` (local DB), `pull`, `citations`.
- **`markery historian card --infer --json`** — the proven relevance/recommendation scorer
  (free model + human gate), reused here for "good match?" and "rich enough?" judgments.
- **`markery project init / adopt / onboard`** — scaffold and inspect projects.
- **`markery site build-all`** — builds every project + the portal (Phase 26); a new project
  becomes a portal card automatically.
- **markery-langgraph** — CLI-only LangGraph workflow with checkpointer + `interrupt()` human
  gate + `check_contract()`; today runs candidate review, here gets a second graph.

---

## 3. The pipeline (stage by stage)

### Stage 1 — Triage *technological* design marks  ·  owner: **TRADEMARK**
Not every design mark is worth a patent search — a stylized logo for a soap is branding, not
technology. The selection rule is a **two-signal filter** (see §5 for the exact lists),
grounded in the 1929–1930 review data: a cheap deterministic **class gate** narrows the field,
then the **free model judges the goods/services text** on the survivors.

These marks predate Nice classification, so the class signal is the **old US class schedule**.
In the review data the field is dominated by branding classes — US 46 foods (106 marks) and
US 39 clothing (67) — while the apparatus classes are exactly the technology ones. **Class gate
(auto-pass):** US **19** vehicles, **21** electrical apparatus/machines/supplies, **23**
cutlery, machinery & tools, **26** measuring & scientific appliances, **34** heating/lighting/
ventilating apparatus, **44** dental/medical/surgical appliances; **borderline (reach the
model, must show a clear apparatus in goods):** US **13** hardware & plumbing/steam-fitting,
**31** filters/refrigerators, **35** belting/hose/machinery packing. Everything else is skipped
without a model call.

**Free-model judgment (the actual rule it applies):** for each class-gated mark, read the
goods/services and decide *"does this describe something a utility patent would cover — a
machine, apparatus, device, instrument, mechanism, engine, electrical equipment, or a
method/process — as opposed to a consumable, material, content/media, or simple
non-mechanical article?"* This is needed because the class gate is necessary but not
sufficient: US 26 holds both *"weighing scales"* (include) and *"motion pictures reproduced in
copies for sale"* (exclude); US 23 holds *"centrifugal and vacuum pumps"* (include) alongside
*"razor blades"* (a simple article — exclude/low). Output: a ranked list of technological
design marks (serial, owner, goods, class, model verdict + one-line reason).

### Stage 2 — Seed a patent match  ·  owner: **MATCHMAKER** (+ **PATENT** auto-fetch)
For each technological mark, resolve its **owner → entity** (`matchmaker suggest-variants`
then `build` if new), then seed a candidate search scoped to that owner/mark:
`markery match --serials <serial> --auto-fetch` (or `--entity <owner>`), which pulls the
owner's patents from EPO if absent and writes candidate pairs. PATENT owns the corpus fetch;
MATCHMAKER owns candidate generation + the entity registry.

### Stage 3 — Keep only GOOD matches  ·  owner: **HISTORIAN**
Score the seed candidates with `historian card --infer`. "Good" = score ≥ threshold (and the
goods↔patent-subject correspondence is honest — the essay discipline: no embodiment claim
unless goods match). No good matches → the mark is technological but has no patent
correspondence; **log and drop** (recorded so it isn't re-processed). Good matches → carry the
matched patents' **CPC subclass(es)** forward.

### Stage 4 — Expand the subclass, re-match  ·  owner: **PATENT** (+ **MATCHMAKER**)
Take the CPC subclass(es) of the good matches and widen from one owner to a **technology
area**: `patent coverage-check` (dry-run counts to budget the sweep), then `patent build`
scoped to those subclasses over the era, pulling more patents. Re-run `markery match` across
the design marks (and their owners) that fall in that subclass space to surface **more pairs**
— other companies' marks matching patents in the same technology. PATENT owns subclass
expansion (and the EPO quota budget); MATCHMAKER owns the re-match.

### Stage 5 — Richness branch  ·  owner: **orchestrator** (HISTORIAN judgment, human-gated)
Assess the expanded space (counts from `project onboard` / `patent search` / `match --all`):
- **Rich** — many entities and many good matches across the subclass(es) → a
  **technology-area project** (scope = the CPC subclass(es), multiple companies).
- **Sparse** — essentially one company's marks/patents → a **small company project** (scope =
  that single entity).
The branch + the new project's name/scope is the **human gate** (creating a project is
consequential). HISTORIAN supplies the rich-vs-sparse recommendation; a human approves.

### Stage 6 — Scaffold, populate, publish  ·  owner: **PUBLISHER** (+ specialists to fill)
`markery project init <slug>` with the chosen scope (`class_hints` = subclass(es) for a
tech-area project; the single entity for a company project); register entities/variants
(MATCHMAKER), build/enrich marks (TRADEMARK), build patents (PATENT), generate + confirm
matches (MATCHMAKER + HISTORIAN review), draft essays (HISTORIAN), then **PUBLISHER**
`site build-all` — the project appears as a portal card.

---

## 4. Specialist ownership (summary)

| Stage | Owns it | Command(s) | Produces |
|---|---|---|---|
| 1 Technological triage | **TRADEMARK** (free model) | new `trademark tech-marks --year <Y>` — US-class gate + free-model goods/services judgment (§5) | list of technological design marks (+ reason) |
| 2 Seed match | **MATCHMAKER** + PATENT | `matchmaker suggest-variants`/`build`, `match --serials/--entity --auto-fetch` | seed candidate pairs |
| 3 Good-match filter | **HISTORIAN** | `historian card --infer --json` + threshold | good pairs + their CPC subclasses |
| 4 Subclass expansion + re-match | **PATENT** + MATCHMAKER | `patent coverage-check`, `patent build --cpc <subclass>` (new flag), `match --all` | widened corpus + more pairs |
| 5 Richness branch | **orchestrator** (HISTORIAN judgment) | counts via `project onboard`/`patent search`; **human gate** | decision: tech-area \| company \| drop |
| 6 Scaffold + publish | **PUBLISHER** (+ all specialists) | `project init`, then trademark/patent/matchmaker/historian populate, `site build-all` | a new published project |

Each specialist stays inside its scope (per the repo contract); the langgraph loop is the
only cross-cutting actor and it only calls CLI commands.

---

## 5. Decision rules & thresholds (tunable)

- **Technological** (stage 1) — the rule the free model applies, in two parts:
  - **Class gate (deterministic, US class schedule):** keep a mark if any US class is in
    `TECH_CLASSES = {19, 21, 23, 26, 34, 44}` (auto-pass) or
    `TECH_BORDERLINE = {13, 31, 35}` (pass to the model). All other classes → skip (no model
    call). This alone drops the food/clothing/tobacco/cosmetic/chemical branding majority.
  - **Goods judgment (free model):** INCLUDE when the goods/services name an **apparatus,
    machine, device, instrument, appliance, mechanism, engine/motor, electrical/electronic
    equipment, or a method/process** (patentable subject matter). EXCLUDE when they are a
    **consumable** (food, drink, drug/cosmetic/chemical *preparation*, fuel), a **material**
    (ore, metal stock, fabric), **content/media** (films, recordings, prints "for sale"),
    **apparel/textile**, or a **simple non-mechanical article** (plain container, jewelry).
    - *positive lexicon (cues, not a whitelist):* machine, apparatus, device, instrument,
      appliance, mechanism, engine, motor, generator, dynamo, pump, valve, meter, gauge,
      regulator, transformer, battery, switch, breaker, scale, projector, camera, typewriter,
      welding, refrigerating, ventilating, tool (powered/precision).
    - *negative lexicon (cues):* canned/food/cereal/syrup/beverage, preparation/compound/
      powder/cream/soap/paint, fabric/garment/coat/hosiery/hat, film/picture/recording/
      publication "for sale", ore/sheet/casting/metal stock.
  - The model returns `technological: yes|no` + a one-line reason; the lexicons steer it but
    the *judgment on the goods text is the rule* (so it handles the US-26 scales-vs-films and
    US-23 pumps-vs-razor-blades cases the class gate cannot). Conservative start; widen the
    class set / loosen the bar later if recall is too low.
- **Good match** (stage 3): `card --infer` score ≥ `GOOD_MATCH_FLOOR` (start ≈ 4/5) with
  honest goods↔subject correspondence; ≥1 good match to proceed.
- **Rich vs sparse** (stage 5): `RICH` when distinct entities ≥ `MIN_ENTITIES` (e.g. 3) **and**
  good matches ≥ `MIN_MATCHES` (e.g. 5) across the subclass(es); else `SMALL_COMPANY` when a
  single owner clears the good-match bar; else **drop**.

All three are config constants surfaced as CLI flags so the loop and a human can tune them;
the consequential branch (stage 5) is always human-approved regardless.

---

## 6. New Markery CLI surface (so the loop can shell out)

| Command | Specialist | Purpose |
|---|---|---|
| `trademark tech-marks --year <Y> [--json]` | TRADEMARK | flag technological design marks (class + goods lexicon) |
| `patent build --cpc <subclass> --year-range …` | PATENT | class-scoped corpus expansion (stage 4) |
| `patent coverage-check --cpc <subclass>` | PATENT | budget the EPO sweep before fetching |
| `match --serials/--entity --auto-fetch` | MATCHMAKER | *exists* — seed + re-match |
| `historian card --infer --json` | HISTORIAN | *exists* — good-match + technological/borderline scoring |
| `project init <slug> --class-hints … / --entity …` | infra/PUBLISHER | scaffold the spawned project with scope |
| `project onboard <slug>` | infra | *exists* — richness counts for stage 5 |

Most stages reuse existing commands; the genuinely new ones are `trademark tech-marks` and a
`--cpc` scope on `patent build`/`coverage-check`. Each new command degrades gracefully and is
unit-testable with mocked HTTP (the `search-tsdr` precedent).

---

## 7. Continuous orchestration in markery-langgraph

A new graph (`spawn_graph.py`), separate from review/discovery:

```
seed_marks      — enumerate technological design marks for a year (trademark tech-marks);
                  skip ones already processed (dedup ledger).
pick_mark       — pop next; terminate when drained.
seed_match      — resolve owner→entity; match --serials --auto-fetch.
score_matches   — historian card --infer on the seed pairs → good? (threshold)
                  no → record_drop ; yes → expand.
expand_subclass — patent coverage-check + build --cpc (budgeted); match --all over the space.
assess_richness — counts → RICH | SMALL_COMPANY | DROP recommendation.
human_gate      — interrupt(): approve branch + name/scope, or reject/defer.
spawn_project   — project init (+ populate hooks), then enqueue a build.
publish         — site build-all; the project becomes a portal card.
record          — append to a spawn ledger (mark, decision, project, timestamps).
```

- **Dedup ledger:** a JSONL of processed marks/owners/subclasses and their outcome, so the
  loop never re-seeds the same mark or re-expands the same subclass; also the audit trail.
- **Budgets:** stage 4 (`patent build --cpc`) is the EPO-quota-heavy step — cap subclasses
  expanded per tick and respect the daily quota via `coverage-check` first.
- **Human gates:** only stage 5/6 (create a project). Everything upstream (triage, seed,
  score, expand) runs autonomously and just logs — those are cheap, reversible, and produce no
  outward artifact.
- **Checkpointer + cadence:** resumable; each tick processes a bounded number of marks so a
  run is short; schedule it like the discovery loop in `HISTORIAN_REVIEW.md`.

---

## 8. The two project types it produces

- **Technology-area project** — `class_hints` = the CPC subclass(es); entities = all owners
  with marks/patents in the space; the essays/site frame a *technology* and the companies
  competing in it. This is the richer, more valuable output.
- **Small company project** — a single entity; the existing match-review-essay shape scoped to
  one firm. The fallback when a subclass turns out thin.

Both are ordinary `match-review-essay` projects (no new project type needed); they differ only
in scope (class-scoped multi-company vs single-company), so the publisher, portal, and all
specialists handle them unchanged.

---

## 9. Risks & discipline

- **Honesty (carried from essays):** technological triage is class/goods-based, not vibes; a
  patent is only matched to a mark when goods↔subject genuinely correspond — no forced
  embodiment claims. A "good match" that fails the correspondence test is dropped.
- **EPO quota** is the real constraint on stage 4; `coverage-check` before every sweep, cap
  subclasses/tick, run over days.
- **No runaway spawning:** project creation is always human-gated; the dedup ledger prevents
  re-processing; thresholds keep the bar high.
- **Idempotency:** every stage checks existing state (entities, patents, candidates, the
  ledger) before acting; safe to re-run.
- **Scope boundaries:** each specialist writes only within its subtree; the loop never edits
  project content directly — it calls the owning specialist's command.

---

## 10. Phased plan

- **P1 — Technological triage.** `trademark tech-marks --year` (class + goods lexicon) + tests;
  run over the 1929/1930 reviews to produce the first candidate-mark list.
- **P2 — Seed + score.** Wire `match --serials --auto-fetch` + `historian card --infer`
  good-match filter; a CLI/loop step that takes a mark → good pairs (or drop), with a ledger.
- **P3 — Subclass expansion.** `patent build --cpc` + `coverage-check --cpc`; re-match across
  the subclass; budgeted.
- **P4 — Richness branch + spawn.** Counts → RICH/SMALL/DROP; `project init` with scope; the
  human gate; populate hooks.
- **P5 — The loop.** `spawn_graph.py` in markery-langgraph end-to-end (seed→…→publish), with
  dedup ledger, budgets, and the single human gate; scheduled.
- **P6 — First spawns.** Run against 1929/1930 technological marks; produce at least one
  technology-area project and one small-company project; `site check` clean across the portal.

Gates: each P closes when its command works with mocked-HTTP tests and degrades without keys;
P5 closes when one end-to-end tick takes a technological design mark through to a human-gated
project spawn and a clean portal build.

---

## 11. Open questions / decisions for the user

1. **Technological definition:** is the int'l-class + goods-lexicon cut right, or do you want
   a HISTORIAN model judgment as the primary gate (slower, but catches odd goods text)?
2. **Thresholds:** starting values for GOOD_MATCH_FLOOR, MIN_ENTITIES, MIN_MATCHES — and should
   "rich vs sparse" be a pure count rule or a HISTORIAN judgment call?
3. **Autonomy boundary:** confirm the only human gate is project creation (stage 5/6), with
   triage/seed/score/expand fully autonomous — or do you also want to approve subclass
   expansions (the EPO-spend step)?
4. **Naming:** who/what names a spawned technology-area project (the subclass title? a HISTORIAN
   suggestion the human edits?).
5. **Source of marks:** only the annual-review years (1929/1930 now), or any design mark in the
   corpus as reviews expand to more years?
