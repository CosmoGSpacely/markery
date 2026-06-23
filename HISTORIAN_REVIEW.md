# Continuous Historian Discovery Loop — Plan

A plan to make **markery-langgraph** run the historian/librarian on a continuous loop
that discovers literature and media relevant to the projects published on the Markery
site, acquires what is admissible, and queues the rest (ILL, purchase leads) for human
decision. Extends the public-domain media sources already deferred in **D069** with three
new source classes: **eBay listings**, **pre-1931 newspapers**, and **WorldCat/ILL for
pre-1931 books**.

Status: planning. No code yet. Archived to `archive/` on completion.

---

## 1. Goal

For every subject in the published projects — each company (entity), its trademarks and
patents, and (Phase 25) its people — continuously:

1. **Discover** relevant literature and media across a fixed set of sources.
2. **Judge relevance + admissibility** (historian model + license rules).
3. **Acquire** what is free/public-domain (media → `library/media`, text → `library/works`).
4. **Queue** what needs a human decision: ILL/book requests (`library/wants.jsonl`) and
   purchase leads (eBay), never auto-buying or auto-submitting an ILL.
5. **Log** everything as provenance-tracked research leads the historian can cite/embed.

The loop runs unattended on a cadence, is idempotent (dedups against what's already in the
library), respects per-source rate limits and budgets, and surfaces only genuine decisions
to a human.

---

## 2. Current state (what we build on)

- **markery-langgraph** already shells out to the `markery` CLI (never imports it), with a
  `MemorySaver` checkpointer, a `human_gate` via LangGraph `interrupt()`, and a
  `check_contract()` gate before any CLI call (see its `CLAUDE.md`). Today it runs the
  *candidate review* cycle; this plan adds a second graph: the *discovery loop*.
- **Librarian** (`markery librarian …`): `search-sources` (IA/Gutenberg), `discover`
  (Wikipedia citations → acquirable sources), `acquire` (text → `library/works/<slug>`),
  `wants` / `wants-update` (the ILL/wants queue at `library/wants.jsonl`, schema carries
  `isbn` + `source_article`), and **`media-search` / `media-acquire`** (Wikimedia Commons,
  P2) writing provenance-tracked items to `projects/<name>/library/media/`.
- **Historian** (`markery historian …`): `card --infer --json` (relevance/recommendation
  scoring, the proven free-model + human-gate pattern), `draft`, `digest`, `validate`.
- **D069** (deferred): the remaining public-domain media sources — Library of Congress,
  NARA, DPLA, Internet Archive media — each a new adapter following `sources/commons.py`.
- **ILL reference** (`memory/reference_ill_automation.md`): OCLC WorldShare / ILLiad /
  RapidILL / ReShare have APIs, but patron-facing submission is institution-specific and
  must live in a **local script outside the repo**; `wants.jsonl` already holds the fields
  ILL needs.

**Design rule carried throughout:** the loop only ever calls the `markery` CLI (the
langgraph contract). So most of this plan is *new Markery CLI surface* that the loop then
orchestrates and human-gates.

---

## 3. Architecture — the discovery loop

A new LangGraph graph in `markery-langgraph` (e.g. `discovery_graph.py`), separate from the
review graph. Subjects come from the project's published state (entities, marks, patents,
people), enumerated via existing CLI (`markery project onboard` / `historian digest`).

```
seed_subjects   — enumerate (project × subject) work items from project state.
pick_subject    — pop next subject; skip if recently swept (cadence/dedup).
discover        — for each enabled source, run `markery librarian <source> search` → candidates.
score_relevance — historian judges each candidate (relevance 1–5 + kind: media/text/lead/book).
route           — admissible-free → acquire; needs-decision → human_gate; irrelevant → drop.
acquire         — media → librarian media-acquire; text → librarian acquire.
human_gate      — interrupt() for: ILL/book request, eBay purchase lead, license edge cases.
record_lead     — append to the project discovery log (provenance + decision).
sleep/next      — back off per source rate limits; loop to pick_subject; idle when drained.
```

- **Idempotency / dedup:** before discover, load what's already in `library/media/index.jsonl`,
  `library/works/`, `wants.jsonl`, and the discovery log; skip known items (by source id /
  URL / ISBN / hash). A per-subject "last swept" timestamp drives the cadence.
- **Cadence:** run as a scheduled job (cron / a long-running loop with sleeps). Each tick
  sweeps a bounded number of subjects/sources so a run is short and resumable via the
  checkpointer.
- **Budgets & rate limits:** free sources first; cap calls per source per tick; honor each
  API's quota. eBay/OCLC keys gate those sources (skip gracefully if absent — same pattern
  as `search-tsdr`).
- **Human gates (never autonomous for irreversible/outward/$$ actions):** ILL submission,
  any eBay purchase, and ambiguous-license media all interrupt for a human; everything
  free + clearly-licensed + clearly-relevant is acquired automatically and just logged.
- **Division of labor:** librarian *acquires*, historian *judges and later embeds*; the loop
  *orchestrates and gates*. Matches the existing thesis (free model drafts/judges, CLI does
  deterministic work, human decides the consequential calls).

---

## 4. Sources

Each source: what it provides · access · license/usage posture · how it maps into Markery ·
discipline · caveats.

### 4a. Public-domain media — D069 (LoC, NARA, DPLA, Internet Archive media)
- **Provides:** period photos, maps, drawings, film of companies/people/products.
- **Access:** per `archive/MEDIA-SOURCES-REVIEW-2026-06-22.md` (LoC `?fo=json`; NARA
  catalog API; DPLA `api.dp.la` + rightsstatements.org; IA `archive.org/metadata`).
- **Posture:** admit PD/CC0/CC-BY/CC-BY-SA (the P2 policy); capture license + attribution.
- **Maps to:** `library/media` via new `librarian media-acquire --source <loc|nara|dpla|ia>`
  adapters (the D069 work), embeddable with `[[media:slug]]`.
- **Caveat:** "no known restrictions" is a flag, not a license — require a positive PD basis.

### 4b. Pre-1931 newspapers — Chronicling America (Library of Congress)
- **Provides:** OCR full text **and** page images of historic US newspapers; ideal for
  contemporaneous coverage of a company/mark/product (ads, notices, articles).
- **Access:** Chronicling America API — `https://chroniclingamerica.loc.gov/search/pages/
  results/?andtext=<query>&date1=1900&date2=1930&format=json`; each hit has OCR text + a
  page image (JP2/PDF) + a stable citation URL.
- **License/usage:** LoC states the digitized content is **public domain / no known
  restrictions**, and pre-1931 dates put it firmly in PD by expiration. **Admit as PD media
  + citable text.**
- **Maps to:** two outputs — (1) a **newspaper clipping** as `library/media` (kind=`clipping`,
  the page image cropped/linked, with the citation as attribution) embeddable via
  `[[media:slug]]`; (2) a **citation/excerpt** the historian can quote in an essay (with the
  paper name, date, page). New CLI: `markery librarian newspapers search <query> [--year-max
  1930]` and `… newspapers acquire <loc-page-id> --project <p>`.
- **Discipline:** quote OCR faithfully; cite paper/date/page; no invented attribution.
- **Caveat:** OCR is noisy — store raw OCR + the image; cap date at the rolling PD cutoff
  (currently <1931).

### 4c. eBay listings — research/provenance **leads only** (never site media)
- **Provides:** signals that period artifacts exist and what they look/sell for — original
  advertising, signs, catalogs, letterheads, packaging, ephemera tied to a mark/company.
- **Access:** eBay **Browse API** (`buy.browse` — active listings by keyword; OAuth app
  token) for current items; sold/historical needs the restricted Marketplace Insights API
  (apply, or omit). Requires an eBay developer app key.
- **License/usage — important:** eBay listing **images and text are copyrighted** (seller /
  eBay) and are **not** admissible as site media. eBay is a **discovery and provenance
  signal only**: "an original 1925 STARRETT catalog is offered for sale" → a research lead,
  optionally a `wants`/acquisition candidate, never an embedded image.
- **Maps to:** the **discovery log / research leads** (title, price, URL, seller location,
  date if datable) and, where the historian judges it worth owning for research, a
  `wants.jsonl` entry. **No auto-purchase** — purchase is always a human gate, and Markery
  does not transact.
- **Discipline:** treat as a lead, not a fact; never copy eBay images into the site; never
  assert provenance from a listing alone.
- **Caveat:** key + rate limits; ToS forbids scraping (use the API); listings are
  ephemeral — snapshot the lead with a retrieved-at date.

### 4d. Pre-1931 books — WorldCat discovery → digitized full text → ILL
- **Provides:** trade catalogs, company histories, industry directories, biographies.
- **Access / flow (three tiers, cheapest first):**
  1. **Find the book.** WorldCat Search API (OCLC key) — or, keyless fallbacks, Open Library
     (`openlibrary.org/search.json`) and HathiTrust bib API — to identify relevant pre-1931
     titles (by/about the entity) with OCLC number + ISBN.
  2. **Prefer digitized full text (free, PD).** Pre-1931 ⇒ PD by expiration ⇒ usually already
     scanned on **Internet Archive** or **HathiTrust**. Resolve the title to an IA identifier
     / HathiTrust id and `markery librarian acquire` the full text directly — no ILL needed.
  3. **ILL only if not digitized.** If no free scan exists, add to `library/wants.jsonl`
     (already carries `isbn`/`source_article`); **ILL submission stays a local,
     institution-specific script outside the repo** (per the ILL reference) and is a human
     gate, not an autonomous action.
- **License/usage:** pre-1931 books are PD → full text is admissible (`library/works`) and
  quotable. Cap the publication-year filter at the rolling PD cutoff (<1931 as of 2026).
- **Maps to:** `library/works` (digitized) or `wants.jsonl` (ILL); new CLI:
  `markery librarian worldcat search <query> [--year-max 1930]` that emits candidates and,
  on accept, either hands off to `acquire` (if a free scan is found) or `wants`.
- **Caveat:** OCLC key/membership; dedup by OCLC#/ISBN; don't ILL something already PD-online.

---

## 5. New Markery CLI surface (so the loop can shell out)

The loop is thin; the capability lives in Markery commands:

| Command | Purpose | Notes |
|---|---|---|
| `librarian media-acquire --source {loc,nara,dpla,ia}` | D069 PD-media adapters | follow `commons.py`; same license policy |
| `librarian newspapers search/acquire` | Chronicling America (4b) | PD; clipping media + citation/excerpt |
| `librarian ebay search` | eBay Browse leads (4c) | leads only → discovery log / wants; key-gated, graceful skip |
| `librarian worldcat search` | book discovery (4d) | → digitized `acquire` or `wants`; keyless fallbacks |
| `historian relevance <project> --subject … --candidates -` | score discovered items | reuse the `card --infer --json` free-model + human-gate pattern for media/lit |
| `librarian leads <project>` / `leads-add` | the per-project discovery log | provenance + decision trail |

All key-gated commands degrade gracefully with an actionable message when the key is absent
(the `search-tsdr` precedent), so the loop keeps running on the free sources.

---

## 6. Outputs & provenance

- **Media:** `projects/<name>/library/media/` (Commons + D069 + newspaper clippings),
  embeddable via `[[media:slug]]`, rendered with caption + attribution + source link (P2/P3).
- **Text:** `library/works/<slug>` (digitized PD books, OCR), indexed/searchable, surfaced to
  historian sessions via `librarian card`.
- **Wants/ILL:** `library/wants.jsonl` (books needing ILL or purchase consideration).
- **Discovery log:** a new per-project `library/leads.jsonl` — every candidate the loop saw,
  its source, relevance score, decision (acquired / wanted / lead / dropped), and timestamps.
  This is the historian's research surface and the loop's dedup memory.

Same fact-discipline as essays: captions/citations state *what it is and where it came
from*; eBay is a lead, never evidence; nothing invented.

---

## 7. Risks & constraints

- **Licensing is the central risk.** Only 4a/4b/4d yield embeddable/quotable content (PD/free).
  **eBay (4c) is leads-only** — a hard rule, enforced in code (the eBay adapter has no
  `acquire`-to-media path).
- **API keys / quotas:** eBay (app key + OAuth), OCLC WorldCat (membership). Skip gracefully
  without them; the free spine (Commons, LoC/Chronicling America, IA/HathiTrust, Open Library)
  works keyless.
- **ToS:** use official APIs, never scrape (eBay, OCLC, newspapers).
- **Continuous-run safety:** idempotent + dedup’d; bounded per-tick work; rate-limit backoff;
  **no autonomous purchases or ILL submissions** (human gate); cost caps; the checkpointer
  makes runs resumable and observable.
- **OCR/relevance noise:** store raw + image; the historian relevance gate filters; low-score
  items are logged, not acquired.

---

## 8. Phased plan

- **P1 — D069 media adapters.** LoC, NARA, DPLA, IA-media `media-acquire` sources. Unblocks
  the media half of the loop. (Closes D069.)
- **P2 — Chronicling America (newspapers).** `librarian newspapers search/acquire`; clipping
  media + citation output; PD/date-capped.
- **P3 — Discovery log + relevance.** `library/leads.jsonl` + `librarian leads*`; `historian
  relevance` scoring (reuse `card --infer` contract).
- **P4 — WorldCat/book pipeline.** `librarian worldcat search` → digitized `acquire` (IA/
  HathiTrust) → else `wants`; keyless fallbacks first, OCLC key optional.
- **P5 — eBay leads.** `librarian ebay search` (Browse API, key-gated) → leads/wants only.
- **P6 — The loop.** `discovery_graph.py` in markery-langgraph: seed → discover → score →
  route → acquire/gate/log, with cadence, dedup, budgets, and human gates. Run scheduled.
- **P7 — Cadence + docs.** Document the run cadence and the local ILL-submission script
  contract (outside the repo); first full sweep over the published projects.

Gates: each P closes when its CLI command works with mocked-HTTP tests and degrades
gracefully without keys; P6 closes when an end-to-end loop tick discovers, acquires a free
item, queues a want, logs a lead, and human-gates a purchase/ILL on a real project with
`markery site check` still clean.

---

## 9. Open questions / decisions for the user

1. **eBay scope:** active listings only (Browse API), or pursue sold-price history
   (Marketplace Insights — restricted application)? Recommend active-only first.
2. **OCLC WorldCat key:** do we have/want institutional access, or rely on keyless Open
   Library + HathiTrust + IA for book discovery initially?
3. **ILL submission:** confirm it stays a local institution-specific script (per the ILL
   reference) — Markery only manages `wants.jsonl`, never POSTs to a library.
4. **Cadence + autonomy:** how often should the loop sweep, and is the auto-acquire-free /
   gate-everything-else boundary correct (e.g. should *all* media admission be human-gated
   at first, loosening as it proves out)?
5. **Where the loop runs:** scheduled cron vs. a persistent service; and whether discovery
   for the annual design-mark reviews (not just the essay projects) is in scope.
