# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.
Phases 14–15 closed 2026-06-01/2026-05-24. Archived to `archive/ROADMAP-2026-06-03.md`.
Phases 16–18 closed 2026-06-06. Archived to `archive/ROADMAP-2026-06-06.md`.
Phase 19 closed 2026-06-07. Archived to `archive/ROADMAP-2026-06-07.md`.
Phases 20–22 closed 2026-06-14. Archived to `archive/ROADMAP-2026-06-14.md`.
Phase 23 closed 2026-06-18 (P3/D028 deferred to `DEFERRED.md`). Archived to `archive/ROADMAP-2026-06-18.md`.

---

## Phase 24 — Publishing pipeline and content cadence

**Trigger:** Phase 23 complete (P1/P2/P4 passed; P3/D028 deferred). Two free-model research sites now exist — `photographic-equipment` (13 pages) and `precision-tools` (11 pages) — plus the earlier project sites, but they are built **only locally**: there is no deployment path, the site builder's output has known rough edges, and image enhancement / image review run ad hoc. The tool can build, enhance, and draft Wikipedia articles, but nothing is published or maintained on a cadence.

**Scope:** Move Markery from "builds sites locally" to "publishes and maintains them," and make the content itself richer. Six workstreams: improve the site builder's output; **enrich project content with public-domain media** (photos, maps, drawings, video) via the librarian and historian; expand Wikipedia contributions from confirmed pairs; formalize the monthly image-review cadence; improve image-enhancement quality; and stand up real web hosting for the project sites (sequenced last, so it publishes the improved, media-rich output). Each workstream is independent; sequence within the phase can be reordered as priorities shift.

**Goal state:** The site builder produces a polished, accessible, responsive site; project essays and pages are enriched with provenance-tracked **public-domain** media surfaced by the librarian and embedded by the historian/publisher; additional Wikipedia articles are drafted and submitted from confirmed pairs; a documented monthly image-review process runs against project-scope marks; image enhancement produces visibly better mark/figure images than the current pipeline; and project sites are published to a real host at stable URLs via a repeatable `markery`-driven deploy.

---

### P1 — Site builder improvements

1. Audit the current publisher output (`src/markery/specialist/publisher/render/`) across the existing project sites for layout, navigation, accessibility, and responsiveness gaps; record findings in `SITE-REVIEW.md` (REVIEW-file convention). **Done** — see `SITE-REVIEW.md` (16 logged items; the Ink Wash palette and Guild Products footer are already applied).
2. **Publisher-only render/CSS fixes** (no new data dependencies), each with `markery site check` kept green:
   - Stat pills: restyle so they don't read as buttons (SITE-REVIEW #1).
   - Trademark cards: fall back to the word mark — not the serial number — when no image (#2/#14); same for patent number on patent cards.
   - Entity pill links to the entity page (#5).
   - Drop redundant breadcrumbs on top-level Entities/Matches pages (#7).
   - Rename the "Entities" nav item to "Companies" (the *rename* only; the People section is a separate phase) (#8).
   - Fix link/accent contrast to meet WCAG AA on the cream background (#9).
   - Active/current-page indicator in the nav (#10).
   - Make cards clickable as a unit (#11).
   - Full `goods` text via `title`/expand instead of a bare ellipsis (#12).
   - Friendly empty/zero states (#13).
   - Label classification ("Class G01B") and drawing code ("Drawing Code 5T07") on cards (#15).
3. **Patent card illustrative figure** (#3): render the lead figure (historically Figure 1) on patent cards. Render side is publisher; identifying/selecting "Figure 1" may need a PATENT-specialist change if the lead figure isn't already distinguishable in-corpus — route that part to PATENT.
4. **Vertical scrolling filing timeline** (#4): replace the inline horizontal SVG (galleries.py) with a prominent left-rail vertical timeline that advances with scroll alongside the cards.
5. Also fold in the broader audit items from P1's original intent: responsive layout (mobile/tablet), semantic landmarks/alt text/keyboard nav, and metadata/SEO (Open Graph, canonical URLs, sitemap).
6. Add regression tests for new render behavior; archive `SITE-REVIEW.md` on completion.

Note: People-dependent items from SITE-REVIEW (#6 company-formation essay, #8 People nav, #16 inventor/registrant links) are deliberately excluded from P1 and tracked in Phase 25 below.

Results 2026-06-21: Worked the full `SITE-REVIEW.md` audit. Steps 2–6 done across four batches: the publisher-only render/CSS fixes (#1,#2/#14,#5,#7,#8-rename,#9,#10,#12,#13,#15); patent lead-figure rendering (#3, deterministic Figure-1 query + EPO figure fetch) and the vertical scroll timeline (#4); per-record detail pages as the click target (#11) with prominent confirmed-pair links, a sticky nav header, and full grant dates; and step-5 responsive/accessibility (`<main>`, skip link, `:focus-visible`, mobile breakpoints) plus SEO metadata (canonical, meta description, generated sitemap.xml — activated via `--base-url` at deploy). Also fetched media for `precision-tools` (16 TSDR mark images, patent figures) so cards show real imagery. New regression tests added (detail pages, card links, timeline, a11y/SEO); full suite 773 green; `markery site build`/`check` clean (61 pages, 759 links, 0 broken). Deviations: SEO split — robots.txt + schema.org JSON-LD deferred to P7; canonical/sitemap emitted but not baked into the committed artifact pending the P6 URL-scheme decision. `SITE-REVIEW.md` not yet archived (held open while UX feedback continues); P1 gate otherwise met.

### P2 — Public-domain media enrichment (librarian + historian)

1. Survey public-domain media sources and their APIs/licensing — Wikimedia Commons, the Library of Congress, NARA / DPLA, the Internet Archive, and the USPTO patent drawings already in-corpus — covering photos, maps, drawings, and video. Record candidate sources and their license/attribution rules in a review/reference doc. **Only public-domain (or unambiguously free-licensed) media is admitted**; provenance and license must be captured for every item.
2. Extend the **librarian** to discover and acquire such media for a project's entities, marks, and patents (alongside its existing `acquire` / `search-sources` / `discover` flow), storing each item with source URL, license, and attribution metadata under the project.
3. Surface acquired media to the **historian** so essays can reference/embed it, and to the **publisher** so the site renders it with a source caption and attribution. Apply the same fact-discipline as essays — captions state what the media is and where it came from, with no invented provenance.
4. Run enrichment on at least one existing project; confirm media is correctly attributed, the licensing is sound, and `markery site build` / `site check` stay clean with embedded media.

Results 2026-06-22: Built the media-enrichment capability. Step 1 — surveyed six sources (USPTO drawings, Wikimedia Commons, LoC, NARA, DPLA, Internet Archive) with APIs, license-determination rules, and a provenance schema in `MEDIA-SOURCES-REVIEW.md` (PD-by-expiration cutoff: US works published before 1931 as of 2026). License policy decided with the user: admit **PD / CC0 / CC-BY / CC-BY-SA** with a mandatory per-item credit line; reject NC/ND/restricted/unresolved. Step 2 — `markery librarian media-search / media-acquire / media-list` with a Wikimedia Commons adapter (`sources/commons.py`) that resolves rights from `extmetadata` and refuses anything not admitted; items stored under `projects/<name>/library/media/<slug>/` (binary + `metadata.json`) with a `library/media/index.jsonl`. Step 3 — `[[media:slug]]` token renders a sourced, attributed `<figure class="media-figure">` (creator/license + source link), threaded through narratives and essays; build copies media into `site/<project>/media/` and prune covers it. Step 4 — enriched `precision-tools` with a PD combination-square illustration (Wikimedia Commons, Wellman Pattern Supply Co.), embedded via `index-narrative.md`; rebuilt with the caption + attribution + source link rendering; `site check` clean across the root (4797 pages, 62488 links, 0 broken/orphans). New tests for license resolution, storage, and `[[media:]]` rendering; full suite 789 green. Deviation: only **Wikimedia Commons** of the six surveyed sources is implemented (highest coverage); the remaining five (LoC, NARA, DPLA, IA-media) are deferred to **D069**. `MEDIA-SOURCES-REVIEW.md` archived to `archive/MEDIA-SOURCES-REVIEW-2026-06-22.md`.

### P3 — Wikipedia editing expansion — IN PROGRESS

1. Identify confirmed pairs across existing projects suitable for Wikipedia contribution (notability, sourcing); prioritize a working list.
2. Draft and submit articles via `markery wikipedia draft` / `markery wikipedia submit`, honoring Wikipedia sourcing/neutrality norms and the same fact-vs-interpretation discipline used in essays (no unsupported product-patent embodiment claims).
3. Track submissions and outcomes (accepted / declined / pending) in each project's research record.

Progress 2026-06-19: Started a **one-edit-per-day** cadence (kept small so as not to disrupt the rest of the phase). Built a prioritized cross-project working list, `WIKIPEDIA-QUEUE.md`, surveying the 22 confirmed pairs across five projects against the proven "augment an existing notable article with a primary-source citation" pattern (the Soundex precedent). Dropped non-viable targets (Shannon/Yawman & Erbe — no Wikipedia article; Kardex — essay Connection never finalized) and flagged honesty constraints (e.g. Sterilamp's paired patent is a *stroboscopic* lamp, off-topic for the Germicidal-lamp article → trademark-only). **First daily edit submitted and live:** added a primary-source USPTO citation for the "John Deere Moline, Ill." trademark (Serial No. 71055630, filed 1911-04-08, registered 1912-09-10) to the **John Deere** article's logo/trademark paragraph — which previously carried zero USPTO citations — via `markery wikipedia replace` ([rev 1360151379](https://en.wikipedia.org/w/index.php?diff=1360151379), recorded to `projects/animal-marks-1930/wikipedia/submissions.jsonl`, verified live by `check-revision`). **Tooling lesson:** Wikipedia's AbuseFilter #50 ("Shouting") rejects edits whose added text is heavily uppercase — trademark names must be rendered in normal case in prose and edit summaries (per MOS:TM), not the all-caps DB form; the first attempt (all-caps mark) was warned and not saved, the title-case re-submit went through. The P3 gate criterion (≥1 article submitted, status recorded) is met; the daily cadence continues against `WIKIPEDIA-QUEUE.md`.

Tooling 2026-06-19: A review found the first edit leaned heavily on Claude with the free model unused, plus some CLI bypasses (raw `confirmed.jsonl`/essay reads; never running `markery wikipedia draft`). Closed the gaps: (1) added `markery wikipedia candidates <project>` — a deterministic confirmed-pair list (slug, normal-cased mark, patent, essay-present, already-on-Wikipedia) that replaces reading `confirmed.jsonl` by hand; (2) added `markery wikipedia propose-edit <project> <slug> --article <title>` — the **project model drafts the citation sentence** from the human-gated essay, enforcing normal-case mark names (MOS:TM / shouting-filter) and **no patent-embodiment claim** unless the essay's Connection supports goods-correspondence, logging tokens; (3) flipped the P3-relevant project models (`animal-marks-1930` was `claude-haiku-4-5`; `radio-pioneers`, `information-systems` had none) to `openai/gpt-oss-120b:free` so the drafting runs free. **Proof:** `propose-edit` on the John Deere pair (free model, $0) reproduced the correct normal-cased, trademark-only, TSDR-cited sentence — and re-demonstrated the human gate by stating the *filing* date as the registration date (a checkable slip a human corrects). 7 new tests; full suite 753 green. The division now matches the thesis: free model drafts, CLI lists/inspects, human judges.

### P4 — Annual design-mark review

Reconfigured 2026-06-22 (user direction): the design-mark review cadence is now **annual**, starting 1930, rather than monthly. Monthly galleries are retained, grouped under a **year landing page**; each annual landing is a **card on the Markery root portal**.

1. Build an annual review per year at `site/reviews/<year>/`: a year landing page linking the twelve monthly design-mark galleries (mark_draw_cd LIKE '3%', by filing month), rendered in the site chrome (global bar) so it sits under the Markery portal.
2. Surface each annual review as a card on the Markery root portal (year, design-mark count, a representative mark image), linking to the year landing.
3. Build the **1930** and **1929** annual reviews (fetch the design-mark images for both years), and keep `markery site check` green across the root.

Results 2026-06-22: Reconfigured the design-mark review from monthly to **annual**. New `render/reviews.py` renders, per year, a landing page linking twelve monthly galleries of design marks (mark_draw_cd LIKE '3%', by filing month) in the site chrome (`site/reviews/<year>/index.html` + `NN.html`), with mark images written to `reviews/<year>/img/`. `build_all` builds the reviews for `REVIEW_YEARS = [1929, 1930]` and `render_portal` shows a **Design-Mark Reviews** section with a card per year (year, design-mark count, representative image) linking the landing. Fetched the design-mark images for both years via `markery trademark enrich` (360 marks; 1929 and 1930 now at 100% image coverage — 254 and 240). Built: portal + 5 projects + 2 reviews (26 review pages) = **4823 pages**, `site check` clean (63070 links, 0 broken/orphans). 3 new tests; full suite 792 green. Note: the older standalone `projects/monthly-image-review/output/*` monthly galleries are superseded by the in-site annual reviews; the `enhance gallery` tool remains for ad-hoc exploration.

### P5 — Print-ready image files for on-demand printing (Amazon Merch)

Reframed 2026-06-23 (user direction): the goal is for Markery to build a **print-ready image
file** from a public-domain corpus image (a design mark or a patent figure) suitable for
upload to an on-demand printing service like **Amazon Merch on Demand**. Image-enhancement
work (upscale/denoise/deskew) folds in here as the means to reach print resolution.

1. **Define the print spec** (Amazon Merch on Demand as the reference target; other POD
   services are similar and configurable): PNG, **sRGB**, **transparent background**,
   ~**4500×5400 px @ 300 DPI**, **< 25 MB**. Record the spec (and which products/sizes it
   covers) in a reference doc.
2. **Build the asset pipeline from a source image:** clean + **upscale to print resolution**
   (denoise/deskew/contrast so line art is crisp at 300 DPI), **remove the background to
   transparency**, threshold/recolor for a clean print, and place on the target canvas at the
   right size/DPI/color profile. New command, e.g. `markery enhance print <serial|patent_no>
   [--spec merch]`, reusing the existing `enhance` pipeline for the upscaling step. Output is
   written to a **print-images folder under the project** (e.g. `projects/<name>/print/`) — a
   local export for uploading to the POD service, **not** surfaced on the built site.
3. **Source eligibility (legal discipline — two distinct rights):** print only from sources
   that are clear on **both** axes:
   - **Copyright:** PD/CC0 artwork only (pre-1931 by expiration, or CC0). CC-BY/CC-BY-SA are
     *excluded for merch* — POD products carry no attribution surface to satisfy the license.
   - **Trademark:** a historical design mark may have PD *artwork* yet still carry **live
     trademark rights** — selling merch bearing a live mark risks infringement. Restrict
     design-mark sources to **dead/abandoned** marks via `markery trademark mark-status`.
     Patent figures have no trademark issue and are freely printable when PD.
4. **Produce a verified sample sheet** of print-ready files from eligible PD sources (e.g.
   dead design marks from the 1929/1930 reviews and PD patent figures); confirm each meets the
   Merch spec (dimensions, DPI, sRGB, transparency, file size).

### P6 — Web hosting and deployment

1. Select a static host (candidates: **Cloudflare Pages**; Netlify — GitHub Pages dropped 2026-06-21 at the user's direction, deploy workflow removed) and decide the URL scheme (per-project subpath vs. subdomain). Record the decision.
2. Add a repeatable deploy path — a `markery site deploy <project>` command and/or a CI publish workflow — that builds and pushes the site to the host. Handle base-URL/path rewriting so internal links resolve when served under the host's path.
3. Publish at least the two Phase 23 sites — now carrying the P1–P5 improvements and public-domain media — at stable public URLs; verify `site check` against the deployed output (no broken links, correct base URL).

### P7 — Generative-engine optimization (citation in AI search)

**Goal:** make project sites discoverable and *citable* by agentic/AI search (Google AI Overviews, ChatGPT search, Perplexity, Claude web search). These engines retrieve live pages at answer time (RAG) and cite the page carrying a clean, quotable fact — so the work is two jobs: get crawled/retrieved, and be extractable once retrieved. Markery's static-HTML, primary-source-cited, fact-atomic output is already well-suited; this stream closes the output-format gaps. Sequence **before or alongside P6** so deployed sites carry the markup.

1. **Crawl access:** emit a `robots.txt` that permits the AI crawlers we want (`GPTBot`, `ClaudeBot`/`anthropic-ai`, `PerplexityBot`, `Google-Extended`, `CCBot`), plus a `sitemap.xml` and stable canonical URLs (coordinate with the SEO items already in P1).
2. **Structured data:** emit schema.org JSON-LD per page — `Organization` (companies), `Person` (Phase 25 people), `Article`/`CreativeWork` (essays), and patent/trademark records with identifier and date fields — so engines can resolve entities and facts unambiguously.
3. **Extractability:** keep facts as self-contained, dated, identifier-bearing sentences in the HTML text (no JS-painted content); answer-first phrasing and question-shaped headings where natural. (Largely already true; audit and tighten.)
4. **Optional:** emit an `llms.txt` pointing crawlers at key clean-text pages (emerging convention; cheap to add).
5. Keep `markery site check` green; add regression tests for emitted robots/sitemap/JSON-LD.

---

### Phase Gate

P1 PASSED when: the publisher renders a responsive, accessible site with SEO/OG metadata; `markery site check` stays green; render regressions covered by tests; `SITE-REVIEW.md` archived. — PASSED (2026-06-21; archived to `archive/SITE-REVIEW-2026-06-21.md`)

P2 PASSED when: the librarian acquires public-domain media (with source/license/attribution metadata) for a project, the historian/publisher embed it with source captions, and `markery site build` / `site check` stay clean on a media-enriched project. — PASSED (2026-06-22; Wikimedia Commons implemented, other sources deferred to D069)

P3 PASSED when: at least one additional Wikipedia article is drafted and submitted from a confirmed pair via the `markery wikipedia` flow, with submission status recorded. — PASSED (John Deere, rev 1360151379, 2026-06-19). **Closed 2026-06-22:** the daily cadence is paused — the current confirmed pairs are largely exhausted of clean "augment an existing article" targets (Sterilamp/Victor assessed non-viable, see `WIKIPEDIA-QUEUE.md`). Re-open the queue and resume the cadence after more projects add fresh confirmed pairs (more candidate articles).

P4 PASSED when: annual design-mark reviews exist for 1929 and 1930 (year landing + monthly galleries) under `site/reviews/<year>/`, each surfaced as a card on the Markery root portal, with `markery site check` green across the root. — PASSED (2026-06-22)

P5 PASSED when: `markery` produces a print-ready PNG into a project print-images folder (e.g. `projects/<name>/print/`, not surfaced on the site) from a public-domain corpus image that meets the Amazon Merch on Demand spec (PNG, sRGB, transparent background, ~4500×5400 px @ 300 DPI, < 25 MB), built only from copyright-clear **and** trademark-clear sources (PD/CC0 artwork; dead/abandoned marks or patent figures), with a documented sample verified against the spec.

P6 PASSED when: a repeatable `markery`-driven deploy publishes a project site to the chosen host at a stable public URL, with internal links resolving against the deployed base URL.

P7 PASSED when: built sites emit an AI-crawler-permissive `robots.txt`, a `sitemap.xml`, canonical URLs, and valid schema.org JSON-LD for their key entity/essay pages; `markery site check` stays green and the emitted markup is covered by tests.

Phase PASSED when P1–P7 pass. Open deferrals independent of this phase: D007 (`markery patent bulk-import`, PatentsView) and D028 (`search-tsdr` live ODP endpoint, gated on a USPTO ODP/ID.me key).

---

## Phase 25 — People as first-class entities

**Trigger:** Phase 24 P1 site-review surfaced People-dependent work that exceeds the publisher's scope. Items #6 (company-formation essay), #8 (a "People" nav section), and #16 (link inventors/registrants to a person essay) in `SITE-REVIEW.md` all require a person concept the corpus does not yet model. Promote when Phase 24 P1's publisher-only fixes are substantially done.

**Scope:** Introduce *people* (founders, inventors, individual registrants) as a first-class concept spanning shared infrastructure and three specialists. It is rare in this period for an individual to register a trademark, but inventors appear routinely on patents and founders anchor company history. Four workstreams across tiers — they have a hard dependency order: data model → specialist content → publisher rendering.

**Goal state:** People exist in the data model with stable slugs; inventors are surfaced from patent data; the historian writes person essays and company-formation essays; and the publisher renders a "People" section, links inventors/registrants from cards to their person essay, and shows a company-formation essay on each Company page.

---

### P1 — People data model and CLI (Markery infra)

1. Decide how people are represented (a `person` entity type vs. a dedicated people table), with stable slugs and a link index the publisher can resolve — mirroring how companies/entities are addressed today.
2. Add CLI surface for inspection and scaffolding (consistent with `markery project onboard` / entity commands); no hand-editing of person records.

### P2 — Inventors from patents (PATENT specialist)

1. Surface inventor names from in-corpus patent data as people, linkable to the patents they appear on. Identify the rare individual trademark registrant case as well so the publisher can link it (SITE-REVIEW #16).

### P3 — Person and company-formation essays (HISTORIAN specialist)

1. Write short company-formation essays for each company/entity page (SITE-REVIEW #6), under the same fact-vs-interpretation discipline used for existing essays.
2. Write person essays for notable people (founders, key inventors — e.g. Mack, Remington), sourced and provenance-tracked.

### P4 — Publisher rendering of people (PUBLISHER specialist)

1. Add a "People" item to the nav and a People index + person-essay pages (SITE-REVIEW #8).
2. Render the company-formation essay on each Company page (#6).
3. Link inventors on patent cards — and the rare individual registrant on trademark cards — to their person essay (#16). Keep `markery site check` green; add regression tests.

---

### Phase Gate

P1 PASSED when: people are representable in the data model with stable slugs and a resolvable link index, via CLI (no hand-edited records).

P2 PASSED when: inventors are surfaced from patent data as linkable people, and the individual-registrant case is identifiable for trademarks.

P3 PASSED when: company-formation essays exist for the companies in at least one project, and person essays exist for its notable people, all sourced.

P4 PASSED when: the site renders a People section, Company pages show their formation essay, and patent cards (plus any individual-registrant trademark cards) link to person essays, with `site check` green and render regressions tested.

Phase PASSED when P1–P4 pass.

---

## Phase 26 — Markery multi-project portal (site root)

**Trigger:** Per-project sites each build standalone to `projects/<name>/site/` with no shared root. The product is "Markery Research" as a whole — readers should land on a portal that spans all projects, search across all of them, and navigate within a project under a persistent project header.

**Scope (mostly PUBLISHER + a little Markery infra):** Introduce a unified site root and a two-tier page chrome. Decisions taken: **unified root build** (`site/index.html` portal + `site/<project>/` per project; add `markery site build-all`; `site build <project>` builds into the root) and **auto-derived portal metadata with project.json overrides**.

**Goal state:**
- **Root portal** (`site/index.html`): one card per project with an auto-derived scope blurb and a representative trademark image + patent figure; aggregated confirmed-pair **Matches** cards across all projects at the bottom.
- **Two-tier chrome:** a short sticky global bar ("Markery Research" left, site-wide search right); below it a sticky **project sub-header** (project title + section links Trademarks/Patents/Companies/Matches with active state); the timeline/cards scroll beneath both.
- **Global search** over the entire site (all projects), reached from the global bar.
- Each project keeps its nested landing/galleries/detail pages; `markery site check` green across the root.

---

### P1 — Two-tier page chrome
1. Refactor `_page` into a global bar + optional sticky project sub-header; thread project slug/title and root-relative paths through all render callers; adjust sticky offsets so timeline/detail markers clear both bars.

### P2 — Unified root build
1. Build each project into `site/<project>/`; add `markery site build-all` orchestrating per-project builds + the root portal + global search + a root sitemap; keep `site check` working against the root.

### P3 — Root portal landing
1. Render the portal: per-project cards (auto-derived scope blurb + representative mark/figure, with `summary`/`feature_serial`/`feature_patent` project.json overrides) and aggregated cross-project Matches at the bottom.

### P4 — Global search
1. One site-wide search over all projects (pagefind across `site/` + a combined record set), reached from the global bar.

Results 2026-06-21: Built the multi-project portal. `_page` refactored into a short sticky global bar (Markery Research + site-wide search) and an optional sticky project sub-header (project title + section nav, active highlighted), with `<main>` scrolling beneath; root-relative paths thread through all 13 render call sites and timeline/detail sticky markers clear both bars. `markery site build-all` builds every match-review-essay project into `site/<project>/` and renders `site/index.html` (portal: per-project cards with auto-derived OBJECTIVES scope blurb + representative mark/figure, `summary`/`feature_serial`/`feature_patent` overrides, image-existence-guarded) plus aggregated cross-project Matches, a site-wide `search.html` + combined `search.json`, and a root `sitemap.xml` (with `--base-url`). Built artifact: 5 projects, 4797 pages, 62488 links, **0 broken / 0 orphans** via `site check --out site`. 12 new tests (portal + two-tier chrome); full suite 779 green. Deviations: `site build`/`check` default to `proj.site` for direct callers — the unified `site/<project>` path is resolved in the CLI/`build_all` (keeps existing check tests intact); built sites are now gitignored as regenerable artifacts (`/site/`, `projects/*/site/`) and the stale committed per-project builds were untracked; a root-spanning `site check` is run via `--out site` (a dedicated `check-all` could follow).

---

### Phase Gate

P1 PASSED when: project pages render a sticky global bar + sticky project sub-header with the content scrolling beneath, active section highlighted, `site check` green. — PASSED

P2 PASSED when: `markery site build-all` produces `site/index.html` + `site/<project>/...` and `site check` passes across the root. — PASSED

P3 PASSED when: the portal shows every project with a scope blurb + representative mark/figure and the aggregated Matches section, overrides honored. — PASSED

P4 PASSED when: a single search covers all projects from the global bar. — PASSED

Phase PASSED when P1–P4 pass. — PASSED

---
