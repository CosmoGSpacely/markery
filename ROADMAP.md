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

1. Audit the current publisher output (`src/markery/specialist/publisher/render/`) across the existing project sites for layout, navigation, accessibility, and responsiveness gaps; record findings in a `SITE-REVIEW.md` (REVIEW-file convention).
2. Improve templates and CSS: responsive layout (mobile/tablet), accessibility (semantic landmarks, alt text, contrast, keyboard nav), and metadata/SEO (Open Graph, canonical URLs, sitemap). Keep `markery site check` green throughout.
3. Add regression tests for any new render behavior; archive `SITE-REVIEW.md` on completion.

### P2 — Public-domain media enrichment (librarian + historian)

1. Survey public-domain media sources and their APIs/licensing — Wikimedia Commons, the Library of Congress, NARA / DPLA, the Internet Archive, and the USPTO patent drawings already in-corpus — covering photos, maps, drawings, and video. Record candidate sources and their license/attribution rules in a review/reference doc. **Only public-domain (or unambiguously free-licensed) media is admitted**; provenance and license must be captured for every item.
2. Extend the **librarian** to discover and acquire such media for a project's entities, marks, and patents (alongside its existing `acquire` / `search-sources` / `discover` flow), storing each item with source URL, license, and attribution metadata under the project.
3. Surface acquired media to the **historian** so essays can reference/embed it, and to the **publisher** so the site renders it with a source caption and attribution. Apply the same fact-discipline as essays — captions state what the media is and where it came from, with no invented provenance.
4. Run enrichment on at least one existing project; confirm media is correctly attributed, the licensing is sound, and `markery site build` / `site check` stay clean with embedded media.

### P3 — Wikipedia editing expansion — IN PROGRESS

1. Identify confirmed pairs across existing projects suitable for Wikipedia contribution (notability, sourcing); prioritize a working list.
2. Draft and submit articles via `markery wikipedia draft` / `markery wikipedia submit`, honoring Wikipedia sourcing/neutrality norms and the same fact-vs-interpretation discipline used in essays (no unsupported product-patent embodiment claims).
3. Track submissions and outcomes (accepted / declined / pending) in each project's research record.

Progress 2026-06-19: Started a **one-edit-per-day** cadence (kept small so as not to disrupt the rest of the phase). Built a prioritized cross-project working list, `WIKIPEDIA-QUEUE.md`, surveying the 22 confirmed pairs across five projects against the proven "augment an existing notable article with a primary-source citation" pattern (the Soundex precedent). Dropped non-viable targets (Shannon/Yawman & Erbe — no Wikipedia article; Kardex — essay Connection never finalized) and flagged honesty constraints (e.g. Sterilamp's paired patent is a *stroboscopic* lamp, off-topic for the Germicidal-lamp article → trademark-only). **First daily edit submitted and live:** added a primary-source USPTO citation for the "John Deere Moline, Ill." trademark (Serial No. 71055630, filed 1911-04-08, registered 1912-09-10) to the **John Deere** article's logo/trademark paragraph — which previously carried zero USPTO citations — via `markery wikipedia replace` ([rev 1360151379](https://en.wikipedia.org/w/index.php?diff=1360151379), recorded to `projects/animal-marks-1930/wikipedia/submissions.jsonl`, verified live by `check-revision`). **Tooling lesson:** Wikipedia's AbuseFilter #50 ("Shouting") rejects edits whose added text is heavily uppercase — trademark names must be rendered in normal case in prose and edit summaries (per MOS:TM), not the all-caps DB form; the first attempt (all-caps mark) was warned and not saved, the title-case re-submit went through. The P3 gate criterion (≥1 article submitted, status recorded) is met; the daily cadence continues against `WIKIPEDIA-QUEUE.md`.

Tooling 2026-06-19: A review found the first edit leaned heavily on Claude with the free model unused, plus some CLI bypasses (raw `confirmed.jsonl`/essay reads; never running `markery wikipedia draft`). Closed the gaps: (1) added `markery wikipedia candidates <project>` — a deterministic confirmed-pair list (slug, normal-cased mark, patent, essay-present, already-on-Wikipedia) that replaces reading `confirmed.jsonl` by hand; (2) added `markery wikipedia propose-edit <project> <slug> --article <title>` — the **project model drafts the citation sentence** from the human-gated essay, enforcing normal-case mark names (MOS:TM / shouting-filter) and **no patent-embodiment claim** unless the essay's Connection supports goods-correspondence, logging tokens; (3) flipped the P3-relevant project models (`animal-marks-1930` was `claude-haiku-4-5`; `radio-pioneers`, `information-systems` had none) to `openai/gpt-oss-120b:free` so the drafting runs free. **Proof:** `propose-edit` on the John Deere pair (free model, $0) reproduced the correct normal-cased, trademark-only, TSDR-cited sentence — and re-demonstrated the human gate by stating the *filing* date as the registration date (a checkable slip a human corrects). 7 new tests; full suite 753 green. The division now matches the thesis: free model drafts, CLI lists/inspects, human judges.

### P4 — Monthly image-review cadence

1. Define a repeatable monthly image-review process over project-scope marks — what to check (live/dead and public-domain status via `markery trademark mark-status`; image presence/quality via `markery enhance gallery`), and how results are recorded.
2. Add or extend tooling to make the review one command where possible (e.g., a gallery/status report that flags marks needing a fresh image pull or re-enrichment).
3. Run the first cycle against the current projects and document the cadence (CLAUDE.md or a dedicated doc) so it recurs.

### P5 — Better image enhancement

1. Review the current enhancement pipeline (`src/markery/specialist/.../enhance`) and baseline its output quality on a sample of mark images and patent figures.
2. Improve enhancement (e.g., upscaling, denoise, deskew/contrast for scanned figures); keep the `markery enhance` (`enhance` | `batch` | `gallery`) interface stable.
3. Re-enhance a sample, compare against baseline, and confirm the site picks up the improved images via `markery enhance gallery` / `site build`.

### P6 — Web hosting and deployment

1. Select a static host (candidates: **GitHub Pages** — repos already live under `CosmoGSpacely` on GitHub; Cloudflare Pages; Netlify) and decide the URL scheme (per-project subpath vs. subdomain). Record the decision.
2. Add a repeatable deploy path — a `markery site deploy <project>` command and/or a CI publish workflow — that builds and pushes the site to the host. Handle base-URL/path rewriting so internal links resolve when served under the host's path.
3. Publish at least the two Phase 23 sites — now carrying the P1–P5 improvements and public-domain media — at stable public URLs; verify `site check` against the deployed output (no broken links, correct base URL).

---

### Phase Gate

P1 PASSED when: the publisher renders a responsive, accessible site with SEO/OG metadata; `markery site check` stays green; render regressions covered by tests; `SITE-REVIEW.md` archived.

P2 PASSED when: the librarian acquires public-domain media (with source/license/attribution metadata) for a project, the historian/publisher embed it with source captions, and `markery site build` / `site check` stay clean on a media-enriched project.

P3 PASSED when: at least one additional Wikipedia article is drafted and submitted from a confirmed pair via the `markery wikipedia` flow, with submission status recorded. — PASSED (John Deere, rev 1360151379, 2026-06-19; daily cadence continues via `WIKIPEDIA-QUEUE.md`)

P4 PASSED when: a documented monthly image-review process exists, is runnable (ideally one command), and has completed its first cycle against current projects.

P5 PASSED when: the enhancement pipeline produces measurably/visibly better images than the current baseline on a documented sample, with the `markery enhance` interface unchanged and the improved images surfaced in a built site.

P6 PASSED when: a repeatable `markery`-driven deploy publishes a project site to the chosen host at a stable public URL, with internal links resolving against the deployed base URL.

Phase PASSED when P1–P6 pass. Open deferrals independent of this phase: D007 (`markery patent bulk-import`, PatentsView) and D028 (`search-tsdr` live ODP endpoint, gated on a USPTO ODP/ID.me key).

---
