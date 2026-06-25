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
- **License/usage:** LoC states the digitized content is **public domain / no known
  restrictions**, and pre-1931 dates put it firmly in PD by expiration. **Admit as PD media
  + citable text** (same status as our other PD media — fully embeddable).

- **Retrieval mechanics (how the bytes come down):**
  1. **Search.** `GET https://chroniclingamerica.loc.gov/search/pages/results/?andtext=
     <query>&date1=1900&date2=1930&dateFilterType=yearRange&format=json&rows=20`. Each item
     in `.items[]` gives the page identity: `lccn`, `date` (YYYYMMDD), `edition`, `sequence`,
     a `title` (paper name), and `ocr_eng` (the page's OCR text — already in the search
     payload, so relevance scoring needs no extra call).
  2. **Resolve the page base URL** from those fields:
     `https://chroniclingamerica.loc.gov/lccn/<lccn>/<YYYY-MM-DD>/ed-<edition>/seq-<sequence>/`.
  3. **Fetch the assets** off that base:
     - full page image — append `.jp2` (archival) or, simpler for the web, the JPEG via the
       built-in deliverable (`…/seq-<n>.jp2` → convert) or the IIIF endpoint
       `…/image_<region>_<size>.jpg`;
     - OCR text — append `/ocr.txt`;
     - **word-coordinate boxes** — `/coordinates/` (JSON mapping OCR words → pixel boxes).
  4. **Crop to a clipping (optional but preferred).** Use the coordinate boxes for the
     matched query terms to compute a bounding region and crop the page image to just the
     relevant article/ad — a real "clipping" rather than a whole broadsheet. Store both the
     crop and a link to the full page. (Pillow for the crop; fall back to the full page if
     coordinates are unavailable.)
  5. **Store.** Write the clipping (and/or full page) to `projects/<name>/library/media/`
     with `kind="clipping"`, `license="PD"`, `source_url` = the page URL, `attribution_text`
     = "<Paper>, <date>, p.<seq> — Chronicling America (Library of Congress)", plus the OCR
     excerpt saved alongside for quoting.
- **Maps to:** (1) a **clipping** in `library/media`, embeddable via `[[media:slug]]`;
  (2) a **citation + OCR excerpt** the historian quotes in an essay. New CLI:
  `markery librarian newspapers search <query> [--year-max 1930]` and
  `… newspapers acquire <lccn>/<date>/<ed>/<seq> --project <p> [--crop]`.
- **Discipline:** quote OCR faithfully; cite paper/date/page; no invented attribution.
- **Caveat:** OCR is noisy — store raw OCR + the image; cap the date at the rolling PD
  cutoff (<1931); JP2 may need conversion to JPEG/PNG for the site (note the dependency).

### 4c. eBay listings — for-sale artifact leads (images shown as listing cards, not PD media)
- **Provides:** signals that period artifacts exist and what they look like / sell for —
  original advertising, signs, catalogs, letterheads, packaging, ephemera tied to a
  mark/company. The **images are the point** here: a photo of an actual 1925 Starrett
  catalog is a genuine research signal even though it isn't ours to relicense.

- **Retrieval mechanics (how the images come down):**
  1. **Auth.** eBay OAuth2 *application* token from the dev app key/secret
     (`POST https://api.ebay.com/identity/v1/oauth2/token`, client-credentials grant,
     scope `buy.browse`). Cache the token; refresh on expiry.
  2. **Search.** `GET https://api.ebay.com/buy/browse/v1/item_summary/search?q=<query>
     &filter=...&limit=20` with the bearer token. Each `.itemSummaries[]` carries
     `title`, `price`, `itemWebUrl` (the live listing), `itemLocation`, `seller`, and
     **`image.imageUrl`** + `thumbnailImages[]` (eBay-hosted image URLs).
  3. **Detail (optional).** `GET …/buy/browse/v1/item/<itemId>` returns `additionalImages[]`
     for the full image set.
  4. **What we store:** the **image URL(s)** plus listing metadata — not, by default, a
     copied binary. eBay's API terms allow *displaying* item images **in the context of the
     listing** (linking back to the item for sale); they do **not** allow repurposing them as
     our own content. So we **hotlink** the eBay-hosted thumbnail and link the card to
     `itemWebUrl`. (If a local snapshot is needed for the leads log, store it private to the
     repo's working data with a `© seller / via eBay` note and a retrieved-at date — never
     promoted into `library/media`.)
- **Display model — separate from PD media:** eBay items render as **"For-sale artifact"
  lead cards** in a clearly-labeled research-leads surface (e.g. a per-entity "Related
  artifacts offered for sale" strip, or the discovery log), each card = hotlinked eBay
  thumbnail + title + price + **"View listing on eBay →"** linking to `itemWebUrl`, with a
  "© seller, via eBay" credit. They are **not** `[[media:slug]]` encyclopedic media, are
  **not** cited as evidence in essays, and carry `rel="nofollow noopener"`. This keeps the
  images visible (what you asked for) without relicensing them or asserting provenance.
- **Maps to:** the **discovery log** (`library/leads.jsonl`: title, price, image_url,
  item_web_url, seller, location, retrieved_at) and the for-sale lead cards; where the
  historian judges an item worth owning, a `wants.jsonl` entry. **No auto-purchase** —
  acquisition is always a human gate; Markery never transacts.
- **Discipline:** a listing is a lead, not a fact; don't assert provenance from a listing
  alone; keep eBay images visibly in the "for sale" frame, never mixed into the PD media.
- **Caveat:** app key + rate limits; **use the API, never scrape**; hotlinked images and the
  listings themselves are ephemeral (snapshot metadata + retrieved-at; expect dead links over
  time).

- **Sold-price history (completed listings) — automatable vs. human-only.** The Browse API
  above covers *active* listings only. For *sold/completed* prices (what a period artifact
  actually fetches), the candidate sources split sharply by whether the unattended loop can
  use them within terms of service:
  - **eBay Marketplace Insights API** — the **only ToS-compliant automated** route to
    sold-listing data (last-90-day sales: price, condition, date). Requires a *restricted*
    application grant from eBay (business justification). **This is the source the loop uses
    if we get the grant.** Without it, the loop does *not* fetch sold prices automatically.
  - **Terapeak** (eBay's own, in Seller Hub) — rich completed-listing analytics (avg price,
    sell-through), but access is the **logged-in web UI**, not a general public API (the
    legacy Terapeak API was folded into Marketplace Insights). Programmatic scraping of the
    Seller Hub violates eBay ToS → **human-only tool**, not for the loop.
  - **eBay Advanced Search → Completed/Sold listings** — the built-in web UI for sold items.
    No official API for it; scraping eBay search result pages violates eBay ToS →
    **human-only**.
  - **WatchCount.com** — third-party index of eBay sold/popular items. No public API;
    scraping carries its own ToS exposure → **human-only**.
  - **SoldListings.com** — third-party historic sold-listing archive. No API → **human-only**.
- **How the human-only tools fit the loop (handoff, not scraping):** when the loop surfaces a
  for-sale or wanted artifact, it **deep-links the price-research query** on each tool so a
  person can check sold prices in one click, and records the figure they report back into the
  lead. The loop generates URLs like:
  - eBay completed/sold: `https://www.ebay.com/sch/i.html?_nkw=<query>&LH_Complete=1&LH_Sold=1`
  - WatchCount: `https://www.watchcount.com/sold/<query>` (sold filter)
  - Terapeak: link to Seller-Hub Product Research (user must be logged in)
  - SoldListings: `https://www.soldlistings.com/?q=<query>`

  These belong in the lead card / discovery log as **"check sold prices →" links**, never as
  an automated fetch. If Marketplace Insights is later granted, the loop fills the sold-price
  field directly and the handoff links become a fallback.

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

- **Licensing is the central risk.** Only 4a/4b/4d yield embeddable/quotable **PD** content.
  **eBay (4c) images are shown only as hotlinked "for-sale" lead cards that link back to the
  listing** (allowed in-context use), never copied into `library/media`, never `[[media:]]`
  encyclopedic content, never cited as evidence — a hard rule, enforced in code (the eBay
  adapter has no `acquire`-to-PD-media path; it emits lead records with image URLs only).
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
- **P5 — eBay leads. DEFERRED → D074** (out of scope; market-signal leads, not library
  acquisition). §4c kept as reference.
- **P6 — The loop.** `discovery_graph.py` in markery-langgraph: seed → discover → score →
  route → acquire/gate/log, with dedup, budgets, and human gates. Runs as a **persistent
  service the user toggles** (`markery historian discovery {on|off|status|tick}` + a state
  flag), not a fixed cron.
- **P7 — Toggle + docs.** The on/off persistence + status; document the local
  ILL-submission path contract; first full sweep over the published projects.

Gates: each P closes when its CLI command works with mocked-HTTP tests and degrades
gracefully without keys; P6 closes when an end-to-end loop tick discovers, acquires a free
item, queues a want, logs a lead, and human-gates a purchase/ILL on a real project with
`markery site check` still clean.

---

## 9. Open questions / decisions — RESOLVED 2026-06-24

1. **eBay scope:** **DEFERRED → D074.** eBay is market-signal leads, not library
   acquisition; it's out of scope for the loop's "grow the rights-cleared library"
   core. The full §4c design stays as reference for when D074 reopens; P5 drops out
   of this phase.
2. **OCLC WorldCat:** **pursue institutional access if obtainable** (an external,
   user-side action). Build the book pipeline **key-gated with keyless fallbacks
   first** (Open Library + HathiTrust + IA), degrading gracefully when no OCLC key
   is present — same pattern as EPO/TSDR. WorldCat access is not a blocker to
   starting (it's P4, after the free-acquisition core).
3. **ILL:** **human-gated, and make a real request if possible.** Markery manages
   `wants.jsonl` and *prepares* the ILL request; on human approval it submits via a
   local institution-specific path **if one is available** (OCLC WorldShare / ILLiad
   / RapidILL / ReShare — see `memory/reference_ill_automation.md`), otherwise it
   emits the request for manual submission. Never auto-submits. (Institutional ILL
   access is the same external, user-side dependency as WorldCat.)
4. **Autonomy boundary: confirmed — auto-acquire-free / gate-everything-else.** The
   loop auto-acquires free/PD items into the library; everything with cost or
   commitment (ILL requests, any purchase) and ambiguous-license media interrupts
   for a human.
5. **Where the loop runs: a persistent service the user toggles on/off** (not a
   fixed cron). Proposed mechanism: a state flag (e.g. `library/discovery_state.json`,
   `{enabled, last_tick, ...}`) + `markery historian discovery {on|off|status|tick}`;
   while enabled the markery-langgraph `discovery_graph` runs ticks (a long-running
   loop with sleeps, or a scheduler firing `tick`, which no-ops when disabled).
   *Still open (minor):* whether annual design-mark **review** projects are in
   discovery scope, or essay projects only first.
