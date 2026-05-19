# Specialist Review — Phase 6

Design record for the next phase of specialist development. Covers the historian and publisher specialists in depth, and introduces the librarian specialist concept.

---

## Decisions — Round 1 (2026-05-18)

| Question | Decision |
|---|---|
| Historian mode | Both in parallel — strengthen the Claude persona AND build a thin Python preparation layer |
| Publisher wiki target | Both — wiki-style static site first, Wikipedia publishing designed alongside |
| Library reference retrieval | Mixed — Internet Archive for open-access/pre-1928 works; manual curation for in-copyright |
| Librarian specialist scope | Defer to Phase 7 — prove `references/` format in 6A first |

---

## Recommendation: Python Layer Architecture

**Recommendation: pre-session preparation command, not during-session tool calls.**

The question was whether the thin Python layer should run *during* a Claude session (Claude triggers specialist calls as tools) or *before* a session (a prepare step the researcher runs first).

During-session tool calls — where Claude autonomously invokes `markery patent signals` mid-conversation — require either an MCP server or a formal agent framework. Neither exists in the current architecture. Building that is Phase 7+ work and would be premature before the content and workflow design is proven.

**The immediate path is `markery historian prepare <project>`.** This command runs before a Claude session and produces a refreshed `BRIEF.md` that the historian reads at session start. It:

1. Runs patent signals for all confirmed pairs and any candidates above a threshold
2. Fetches figures for confirmed patents not yet in `patent_figures`
3. Fetches TSDR goods descriptions for confirmed trademarks not yet enriched
4. Counts unreviewed candidates above min-score
5. Writes a structured `BRIEF.md` with all of the above plus current confirmed pairs, content gaps, and project thesis

The Claude session opens with a fully current brief. The historian can then issue instruction cards ("run `markery patent figures US1261167A`") and the researcher executes them in the terminal — or, since the user works in Claude Code, directly in the same session via the Bash tool. This is "during-session" in practice without requiring a formal agent framework.

This is also the right foundation for an agentic future: the `prepare` command's output is exactly what a controller would feed to the historian model as structured context. The format decision (see open questions below) determines whether that transition is easy or hard.

**Implementation: `markery historian prepare <project>`**

```
specialist/historian/prepare.py   — orchestration
specialist/historian/cli.py       — add 'prepare' subcommand
```

Output: `projects/<project>/BRIEF.md` — overwritten on each prepare run, never committed (add to `.gitignore`). The researcher may also keep a hand-maintained `OBJECTIVES.md` alongside it for project thesis and scope constraints that don't change between sessions.

---

## Current Specialist Inventory

| Specialist | What it does today | Gap |
|---|---|---|
| `patent/` | Fetches EPO patents, extracts figures, runs text signals | No agent interface |
| `trademark/` | Builds `trademarks.duckdb` from USPTO bulk data, TSDR fetch | No agent interface; no CLI subcommands |
| `matchmaker/` | Entity registry, scoring, candidate generation | No agent interface |
| `historian/` | Interactive terminal reviewer; Claude persona for essay writing | Persona and code are disconnected; no workflow orchestration; no library reference access |
| `publisher/` | Renders 5-page static site (landing, galleries, entities, essays) | Content structure limited to confirmed pairs; no wiki mode; no external publish targets |

---

## Historian Specialist — Phase 6A

### The gap

The historian currently operates in two disconnected modes:

1. **Python mode** (`markery review`) — terminal-based candidate review; writes to `confirmed.jsonl`
2. **Claude mode** — Claude project with `persona/` context; produces essay markdown

These are not integrated. The Claude persona has no way to call patent signals, request a trademark enrichment, query the matchmaker for related candidates, or consult library references. The historian effectively goes dark between sessions and has no memory of project objectives or prior decisions.

### Workflow design

The historian needs a **project brief** — a structured document that defines the objectives, constraints, and current state of a research project. This is what orients a Claude session to the project and tells it what to produce next.

**`project/BRIEF.md`** (new file per project):

A structured input document the historian reads at session start. Contains:
- Project thesis (what the research is trying to show)
- Entities in scope and their significance
- Confirmed pairs so far and their essays
- What the publisher needs next (content gaps)
- Constraints (scope boundary: dates, geography, technology class)

The brief is hand-maintained by the researcher and updated at the end of each session. It is the historian's primary orientation document — more focused than `RESEARCH-AGENDA.md` (which is a reference) and more specific than `STATUS.md` (which is a metrics snapshot).

### Instructions for other specialists

The historian persona currently has no structured way to direct the other specialists. When it needs more data — a patent signal analysis, a trademark goods description, a candidate list for a new entity — it has to ask the researcher to go run a command.

**Design: specialist instruction cards**

A set of structured prompt templates in `persona/instructions/` that the historian can issue as explicit requests to the researcher or (in an agentic future) directly to the relevant specialist:

```
persona/instructions/
  patent-signals.md     — "run markery patent signals <project> for patent X"
  trademark-enrich.md   — "run markery trademark fetch <serial> for goods/services text"
  candidate-refresh.md  — "run markery match <project> after adding entity Y"
  figure-fetch.md       — "run markery patent figures <patent_no>"
```

Each card specifies: what information is needed, which CLI command produces it, where the output lands, and what format the historian expects back. This makes the historian's requests precise and executable.

In the current human-in-the-loop model, the researcher reads the historian's request, runs the command, and pastes or summarizes the output back. In an agentic future, a controller calls the specialist API directly.

### Content production pipeline

Today the historian produces one content type: match essays (`content/<slug>.md`). The publisher needs more:

**Content types the historian should produce:**

| Content type | File | Publisher uses it for |
|---|---|---|
| Match essay | `content/<slug>.md` | Match essay page |
| Entity summary | `content/entity-<slug>.md` | Entity page narrative |
| Gallery narrative | `content/{trademarks,patents,index}-narrative.md` | Gallery and landing page prose |
| **Thematic essay** (new) | `content/theme-<slug>.md` | A cross-entity narrative page (e.g. "The Card Index in American Business") |
| **Timeline annotation** (new) | `content/timeline.md` | Annotated timeline page showing the full arc of a technology |
| **Source notes** (new) | `content/sources.md` | Consolidated primary and secondary source bibliography |

The thematic essay and timeline annotation are new page types. They require the historian to synthesize across confirmed pairs and entities rather than treating each pair in isolation. These are the content that makes a project intellectually interesting to a general reader — not just "here is SOUNDEX and here is its patent" but "here is how phonetic indexing entered American business practice."

### Library reference retrieval

The historian's five key references (Yates, Cortada, Austrian, Chandler) are cited but not consulted. A historian session that can quote a specific passage from *Control Through Communication* is richer than one that cites it abstractly.

**Proposed: `project/references/` input directory**

```
projects/<name>/references/
  yates-control-through-communication.md    — extracted passages + page refs
  cortada-before-the-computer.md
  austrian-herman-hollerith.md
  ...
```

Each file is a curated excerpt document: relevant passages with page numbers, organized by topic. The historian reads these alongside the DuckDB data and uses them to ground essays in secondary literature.

**Retrieval options (in order of feasibility):**

1. **Internet Archive** (`archive.org/advancedsearch.php`) — several of these works are available as scanned PDFs or ePubs under lending or open access. The IA has a borrowable book API and a full-text search API. *Cortada* and *Austrian* are likely available; *Yates* (1989) is under copyright but may have lending access.

2. **HathiTrust** — large academic library consortium; provides full-text search across scanned works. API access for in-copyright works is restricted but full text is available for pre-1928 material.

3. **Google Books** — snippet and preview access only for in-copyright works; not suitable for passage extraction.

4. **Manual curation** — researcher reads the physical or digital copy and pastes relevant passages into the `references/` file. Lowest automation, highest quality control.

**Recommendation for Phase 6A:** Start with manual curation. Design the `references/` file format so that automated retrieval can be added later without changing how the historian consumes the files. Define the format, populate the information-systems references by hand, and build the Internet Archive retrieval as a separate sub-task once the format is proven.

---

## Publisher Specialist — Phase 6B

### Current content structure

Five page types, all driven from `confirmed.jsonl` and `entities.txt`:

```
index.html          — project landing
trademarks.html     — trademark gallery
patents.html        — patent gallery
entities/<slug>.html — one per entity
matches/<slug>.html  — one per confirmed pair
```

All pages are generated mechanically from database records. There is no page that synthesizes across the dataset — no thematic argument, no timeline, no bibliography.

### Expanded content structure

The publisher should support additional page types sourced from the new content files the historian produces:

| New page type | Source | Purpose |
|---|---|---|
| Thematic essay | `content/theme-<slug>.md` | Cross-entity narrative; appears in landing page nav |
| Timeline | `content/timeline.md` | Visual + annotated timeline of the full patent-trademark arc |
| Sources | `content/sources.md` | Consolidated bibliography; links to external records |

These pages require changes to `build.py` (detect optional content files and render additional pages) and `render.py` (new page templates). The timeline page in particular requires a visual component — the SVG timeline already exists in the trademark and patent galleries and can be adapted to span the full project.

### Wiki mode

Two distinct interpretations, requiring a design decision:

**Option A — Wiki-style static site**

The site is restructured to feel encyclopedic: pages cross-link densely, there is a search index (pre-built JSON, no server required), and the content structure supports stub pages that the historian hasn't yet filled. Each entity, mark, and patent has a canonical page that other pages link to by ID. Navigation is by topic, not by page type.

This is achievable within the current static-site architecture. It requires:
- A `search.json` index built at site-build time (lunr.js or Pagefind for client-side search)
- Cross-link rendering in markdown (historian writes `[[SOUNDEX]]` and the publisher resolves it to the correct page)
- Stub page generation for referenced-but-unwritten content

**Option B — Publish to Wikipedia**

Create or enrich Wikipedia articles for notable confirmed pairs and entities. SOUNDEX already has a Wikipedia page; the Markery research could contribute primary source citations (USPTO serial numbers, EPO patent numbers, specific dates) that are not currently in the article.

Wikipedia publishing requires:
- MediaWiki API authentication (account + bot password)
- Wikitext rendering (different from HTML or Markdown)
- Wikipedia's notability and citation standards (primary sources alone are not sufficient; need secondary sources — which is exactly what the library reference work enables)
- Careful scope control: Markery can contribute citations and dates, not full article rewrites

**Recommendation:** Design for Option A first (wiki-style static site with search and cross-linking) as it is fully within Markery's control and architecture. Option B is a separate publishing target that could be added alongside the static site.

### Publishing targets

| Target | Current | Phase 6B |
|---|---|---|
| GitHub Pages (static HTML) | ✅ Built | Expanded content types |
| Wiki-style static (search, cross-links) | 🔲 | Design and build |
| Wikipedia | 🔲 | Research feasibility; requires library references first |
| MediaWiki (self-hosted) | 🔲 | Not planned |

---

## Librarian Specialist — Future (Phase 7+)

### Concept

A librarian specialist holds a corpus of secondary literature — books, articles, finding aids — that can be consulted across projects. Where the historian is project-scoped, the librarian is repository-scoped: it accumulates knowledge that is useful regardless of which research project is active.

### What it holds

```
library/
  works/
    <author>-<short-title>/
      metadata.json         — author, title, year, ISBN, IA identifier
      excerpts.md           — curated passages with page references
      index.md              — topic index into the excerpts
  index.json                — full library index for search
```

### Retrieval interface

In the simplest form, the librarian is a query over `library/` — the historian asks "what does the library have about tabulating machines?" and gets back relevant excerpts. This can be:

1. **Keyword search** — simple grep over `excerpts.md` files; works immediately, no infrastructure
2. **Semantic search** — embed excerpts into a vector store; query by meaning rather than keyword. Requires an embedding model and a vector database (Chroma, LanceDB, or DuckDB's upcoming vector extension).

**Semantic memory** as the user described it aligns with option 2: the library is not a file system but a queryable semantic store. The librarian specialist would provide a `search_library(query: str) -> list[Excerpt]` function that the historian can call to retrieve contextually relevant passages.

### Dependencies

Before a librarian specialist makes sense:
1. The `references/` format must be proven in a project context (Phase 6A)
2. At least 3–4 works must be in the library with curated excerpts (manual curation phase)
3. The historian must have a demonstrated need for cross-work retrieval (not just within one project's references)

The librarian is not Phase 6 work. It becomes relevant when the reference corpus grows beyond what fits comfortably in a single project's `references/` directory.

---

## Recommendation: OBJECTIVES.md and BRIEF.md Design

### OBJECTIVES.md — hand-maintained, stable across sessions

`OBJECTIVES.md` is what the researcher writes and owns. It does not change between sessions unless the project direction changes. It should carry:

**YAML block (machine-readable):**
```yaml
site_mode: narrative       # or: metrics — controls landing page architecture
wikipedia_targets:
  enrich: []               # existing Wikipedia article titles to enrich
  create: []               # new articles to draft
scope:
  date_range: "1900-1939"
  technology: "pre-computer information systems"
  geography: "United States"
```

**Markdown body (historian-readable):**
- **Thesis** — one paragraph stating the historical argument the project is making
- **Scope boundaries** — what is in and out of scope, and why
- **Target audience** — who the published site is written for *(open question — see Round 3)*
- **Content priorities** — which confirmed pairs most need essays; which entities need depth

### BRIEF.md — auto-generated by `prepare`, never committed

`BRIEF.md` is what the prepare command writes fresh before each session. The historian reads it cold. It should never be committed because it goes stale immediately.

**YAML frontmatter (machine-readable):**
```yaml
project: information-systems
prepared: 2026-05-18T14:32:00
confirmed_count: 8
candidate_count_unreviewed: 47        # above min-score, not yet reviewed
content_gaps:
  - {type: match_essay, slug: handiref, status: missing}
  - {type: entity_summary, slug: boorum-and-pease, status: missing}
signals_available: [US1261167A, US2152606A]   # signals fetched, ready to read
figures_available: [US1261167A, US1527374A]   # figures in patent_figures table
enriched_trademarks: [71246709, 71461278]     # goods/services text fetched
```

**Markdown body (historian-readable sections):**
1. **Project state** — confirmed pairs with one-line descriptions; what has essays vs. what is bare
2. **Content gaps** — what the publisher needs that does not yet exist
3. **Candidate highlights** — top unreviewed candidates above threshold with scores and signals
4. **Available signals** — patent text signals ready to read for confirmed pairs
5. **Session recommendation** — one specific suggested task for this session (derived mechanically from content gaps; the historian may override it)

The "session recommendation" is generated automatically by the prepare command — it picks the highest-priority content gap and states it plainly. This gives the historian a default starting point without requiring the researcher to re-read all the gaps. The historian is free to redirect.

---

## Phase 6 Sequence (updated)

Dependencies flow left to right: BRIEF format must be resolved before `prepare` can be built; content types must be defined before publisher page types; static wiki must work before Wikipedia export is attempted.

**6A-1 — Project orientation documents**

- Define and document `OBJECTIVES.md` format (YAML block + markdown body)
- Write `projects/information-systems/OBJECTIVES.md` by hand
- Add `BRIEF.md` to `.gitignore`; document that it is ephemeral

**6A-2 — Reference file format and initial population**

- Define `projects/<name>/references/<author-shorttitle>.md` format: YAML header (author, title, year, IA identifier), then excerpt sections with page numbers
- Populate information-systems references manually from physical/digital copies (Yates, Cortada, Austrian, Chandler)
- Build `markery librarian fetch <ia-identifier>` for open-access works (pre-1928 or openly licensed); outputs a draft `references/` file the researcher then curates

**6A-3 — `markery historian prepare <project>`**

- Build `specialist/historian/prepare.py` — calls patent signals, trademark enrich, figure fetch, counts candidates
- Add `prepare` subcommand to `specialist/historian/cli.py`
- Output: `projects/<project>/BRIEF.md` (YAML frontmatter + ranked gap list + markdown sections)
- Unit tests for gap ranking logic

**6A-4 — Historian instruction cards**

- Write `persona/instructions/patent-signals.md`, `trademark-enrich.md`, `candidate-refresh.md`, `figure-fetch.md`
- Each card: what information is needed, which command produces it, where the output lands, expected format back

**6A-5 — New historian content schemas**

- Write `persona/content-schemas/thematic-essay.md` — layered audience: narrative lead + technical depth sections
- Write `persona/content-schemas/sources-page.md` — primary sources (USPTO, EPO) + secondary (references/)
- Write `persona/content-schemas/timeline-annotation.md`
- Update `persona/identity.md` to reflect layered audience writing register

**6B-1 — Publisher new page types**

- Implement thematic essay page rendering in `render.py` / `build.py`
- Implement sources page rendering
- `build.py`: read `OBJECTIVES.md` site_mode; switch landing page architecture accordingly
- Unit tests for new render functions

**6B-2 — Cross-link rendering**

- Extend `_render_markdown()` to resolve `[[Slug]]` → `<a href="...">` using a slug→path index built at site-build time
- Slugs resolve to: entity pages, match essay pages, thematic essay pages

**6B-3 — Search index**

- Build `search.json` at site-build time: all pages with title, type, slug, first 200 chars of text
- Integrate Pagefind (static binary, no server required, works on GitHub Pages)
- Add search input to site header

**6B-4 — Wikipedia**

- Add `WIKIPEDIA_USERNAME` and `WIKIPEDIA_BOT_PASSWORD` to `.env` (documented in `SETUP.md`)
- Build `markery wikipedia draft <project> <slug>` — generates wikitext from essay + source notes into `projects/<project>/wikipedia/<slug>.wiki`
- Build `markery wikipedia submit <project> <slug>` — shows diff, prompts confirmation, POSTs to MediaWiki API
- Test case: enrich SOUNDEX article with primary source citations
- Draft case: new article for one confirmed pair (KARDEX recommended — strongest secondary source grounding)

---

## Decisions — Round 2 (2026-05-18)

| Question | Decision |
|---|---|
| BRIEF.md format | YAML frontmatter + markdown body |
| Wikipedia scope | Both in parallel — enrich SOUNDEX (existing article); draft new article for one confirmed pair |
| Site architecture | Configurable per project via `OBJECTIVES.md` |

The configurable site architecture decision means the publisher needs to read a site mode flag from the project before rendering. `OBJECTIVES.md` becomes a structured input, not just a prose document. Its format must be defined before the prepare command or publisher can use it.

---

## Open Questions — Round 2

**Q1 — BRIEF.md format**

The prepare command writes `BRIEF.md` and the historian reads it cold at session start. Three options:

- **Prose markdown** — the prepare command writes human-readable narrative sections: "Current state", "Unreviewed candidates", "Content gaps". Natural for the historian to read; hard for a future agent controller to parse programmatically.

- **YAML frontmatter + markdown body** — machine fields (counts, lists of confirmed pairs, content gap flags) in YAML; narrative sections in markdown. The historian reads the whole document; a future controller reads only the frontmatter. This is the recommended option for forward-compatibility.

- **Pure structured data (JSON/YAML)** — fully machine-parseable; the historian uses it as a reference document rather than reading prose. Loses the narrative orientation that makes a cold session start effective.

**Q2 — Wikipedia scope**

Two distinct activities with different requirements:

- **Enriching existing articles** — SOUNDEX has a Wikipedia page. Markery could add primary source citations: the USPTO serial number, the specific Odell patent number, exact filing dates. This is conservative, citation-only contribution that doesn't require passing notability review.

- **Creating new articles** — Most Markery confirmed pairs (VI-DEX, VARIADEX, KARDEX) have no Wikipedia presence. Creating new articles requires establishing notability through secondary sources — exactly what the reference works provide. A well-sourced KARDEX article grounded in Yates and Cortada would be legitimately publishable.

Which should Phase 6B prioritize, or both?

**Q3 — Thematic essays and site architecture** *(answered: configurable per project via OBJECTIVES.md)*

---

## Decisions — Round 3 (2026-05-18)

| Question | Decision |
|---|---|
| Target audience | Layered — general narrative (essays, landing) accessible to any reader; technical depth (patent gallery, source notes, metadata) for specialists; Wikipedia to encyclopedic standard |
| Wikipedia workflow | Draft + API submission with confirmation (`markery wikipedia submit`) — credentials in `.env` |
| Prepare output depth | Full ranked gap list — all content gaps ranked by type priority, not just the top one |

### Implications

**Layered audience** means the historian must write in two registers:
- Thematic essays and landing narrative: no assumed knowledge, defines terms, explains why the technology mattered
- Match essays and source notes: primary-source grounded, citation-precise, suitable for scholarly reference

The publisher's site mode (`narrative` vs `metrics`) operates at the page-architecture level; the layered audience operates at the content level. Both settings coexist: a `narrative`-mode project still has technical depth pages; a `metrics`-mode project can still carry thematic essays.

**Wikipedia API** requires two new `.env` keys: `WIKIPEDIA_USERNAME` and `WIKIPEDIA_BOT_PASSWORD`. The submit command presents the diff, prompts for confirmation, and POSTs to the MediaWiki API's `edit` action. Edits are attributed to the researcher's Wikipedia account, not a bot.

**Full ranked gap list** in BRIEF.md means the YAML frontmatter carries a `content_gaps` list sorted by priority tier:
```yaml
content_gaps:
  - {type: match_essay,     slug: handiref,         priority: 1}
  - {type: match_essay,     slug: boorum-pease-clip, priority: 1}
  - {type: entity_summary,  slug: boorum-and-pease,  priority: 2}
  - {type: thematic_essay,  slug: card-index,        priority: 3}
  - {type: sources_page,    slug: sources,            priority: 3}
```
Priority tiers: 1 = missing match essays, 2 = missing entity summaries, 3 = enrichment pages (thematic, sources, timeline). The markdown body expands each gap with context.

---

## Phase 6C — Semantic Matchmaker

### Current state and the critical gap

The matchmaker currently uses two structural signals:

| Signal | Range | Source |
|---|---|---|
| `date_score` | −0.4 to +0.5 | Patent grant date vs. trademark filing date |
| `class_score` | 0.0 or 0.3 | CPC class membership in product signal set |
| **Total** | max 0.80 | |

`signals.py` in the patent specialist already computes four semantic fields and writes them to `candidates.jsonl`:

| Field | Type | Meaning |
|---|---|---|
| `title_name_hit` | bool | Mark words appear in patent title |
| `abstract_name_hit` | bool | Mark words appear in patent abstract |
| `goods_title_overlap` | float | Jaccard(G&S tokens, title tokens) |
| `goods_abstract_overlap` | float | Jaccard(G&S tokens, abstract tokens) |

**These are displayed in the reviewer for human judgment but do not affect the `score` field.** The matchmaker computes semantic evidence and then discards it before scoring. This is the primary gap.

A pair like SOUNDEX ↔ US1261167A — where the mark name appears in the patent abstract and the G&S description overlaps the title vocabulary — scores identically to a pair with the same date gap but no textual evidence. Fixing this is Phase 6C.

---

### New scoring architecture

The current flow is:

```
generate_candidates() → candidates.jsonl (score field from date+class only)
enrich_candidates()   → candidates.jsonl (adds signal fields, score unchanged)
```

The new flow separates scoring into two passes:

```
Pass 1: generate_candidates()  → candidates.jsonl  (structural score: date + class)
Pass 2: enrich_candidates()    → adds signal fields
Pass 3: rescore_candidates()   → updates score field using signal fields
```

Pass 3 is new. It reads candidates.jsonl, computes the semantic bonus from existing signal fields, adds it to the structural score, and rewrites the score field. The semantic bonus is pure — it only reads from already-fetched data, no new DB calls.

**CLI:**

```bash
markery match <project>                    # Pass 1 only (current behaviour, unchanged)
markery match <project> --signals          # Pass 1 + 2: generate + enrich
markery match <project> --full             # Pass 1 + 2 + 3: generate + enrich + rescore
markery match rescore <project>            # Pass 3 only: rescore from existing signal fields
```

This preserves backward compatibility: `markery match <project>` continues to work as before. `--full` is the new recommended default for a complete match run.

---

### New scoring components

**Recommendation: additive bonus components with a capped semantic ceiling.**

Semantic signals provide additional evidence on top of structural signals — they should raise confidence in strong pairs and help surface uncertain pairs. They should not manufacture confidence from structural weakness: a pair with no temporal alignment should not score high just because the mark appears in the patent title.

**Proposed cap:** semantic bonus is individually additive but capped at 0.25 total, regardless of how many signals fire. This limits the maximum score to approximately 1.05 (0.80 structural + 0.25 semantic) and prevents the semantic layer from overwhelming the structural foundation.

| Component | Signal source | Value | Notes |
|---|---|---|---|
| `title_hit_score` | `title_name_hit` == True | +0.20 | Strong signal: controlled vocabulary, specific |
| `abstract_hit_score` | `abstract_name_hit` == True | +0.10 | Weaker: abstracts are broader |
| `goods_title_score` | `goods_title_overlap` > 0.05 | +0.10 | G&S and patent title describe the same product domain |
| `goods_abstract_score` | `goods_abstract_overlap` > 0.05 | +0.05 | Supporting evidence only |
| **Semantic bonus** | (sum of above, capped) | **max 0.25** | |
| **New total max** | | **~1.05** | |

**Updated `score.py` signature (backward-compatible):**

```python
def total_score(
    grant_dt: date | None,
    filing_dt: date | None,
    cpc_classes: list[str],
    title_name_hit: bool = False,
    abstract_name_hit: bool = False,
    goods_title_overlap: float = 0.0,
    goods_abstract_overlap: float = 0.0,
) -> float:
    structural = date_score(grant_dt, filing_dt) + class_score(cpc_classes)
    semantic   = min(0.25, semantic_score(
        title_name_hit, abstract_name_hit,
        goods_title_overlap, goods_abstract_overlap,
    ))
    return round(structural + semantic, 4)
```

The existing two-argument call `total_score(grant_dt, filing_dt, cpc_classes)` continues to work and produces the same result as before.

---

### Uncertainty resolution loop

When the structural score alone falls in a **confidence band** [T1, T2] — strong enough to not discard, not strong enough to confidently surface — the matchmaker cannot distinguish a genuine match from a coincidence. Semantic signals are most valuable here.

**Confidence band: [0.40, 0.60]**

- Below 0.40: discard (structural signals weak, unlikely to recover)
- 0.40–0.60: uncertain — semantic signals may resolve
- Above 0.60: surface for review (strong structural case regardless of semantics)

**Resolution request mechanism:**

```
markery match <project> --resolve
```

The `--resolve` flag:

1. Runs Pass 1 (generate)
2. Identifies pairs in the confidence band by structural score
3. Checks which uncertain patents already have abstract text in `patents.duckdb`
4. Checks which uncertain trademarks already have G&S text in `statement`/`mark_case_status`
5. Prints a resolution report:
   ```
   47 pairs in uncertainty band [0.40, 0.60]
   Missing abstracts: 12 patents → run: markery patent signals <project>
   Missing G&S text:  8 trademarks → run: markery trademark enrich <project>
   Resolvable now (data already fetched): 27 pairs → run: markery match rescore <project>
   ```
6. Optionally fetches the missing data automatically if `--auto-fetch` is also set

Without `--auto-fetch`, the researcher reads the report and runs the recommended commands. With `--auto-fetch`, the matchmaker calls the specialist fetch functions inline and then rescores. **This is the "asking specialists" behaviour.**

---

### New data requirements

**Patent abstracts** are already in `patents.duckdb` (`abstract` column in the `patents` table). `signals.py` already reads them. No new fetch required for pairs where abstracts exist.

However, some patents in the database were ingested without abstract text (the EPO OPS bulk fetch sometimes omits it for older records). The patent specialist's `build.py` should be extended to back-fill missing abstracts on re-fetch.

**Goods-and-services text** is in `statement.statement_text` (already read by signals.py) and `mark_case_status.goods_desc`. Both are already fetched when available. Gap: many trademarks have neither, because TSDR does not expose G&S text via the raw image endpoint used for bulk ingestion.

**New: `markery trademark enrich <project>`** — fetches G&S text via the TSDR case file API for confirmed pairs and high-scoring candidates in a project. Stores in `mark_case_status` or a new `trademark_enrichment` table. This is the resolution step the matchmaker requests.

---

### Inventor entity alignment (new signal — open question)

A fourth potential new signal: does the patent's inventor have a known relationship to the entity?

Example: Robert C. Russell is the inventor of US1261167A (SOUNDEX patent). Russell is not in the entity registry — but Rand Kardex Bureau, the trademark owner, was a successor company to the organization Russell worked for. If the entity registry tracked inventor-entity associations, this would be a strong confirming signal.

**Implementation options:**

1. **Manual annotation** — researcher adds known inventor→entity links to `entity_name_variant` with a new `source = 'patent_inventor'` type. Low automation, high precision.
2. **Name match heuristic** — check if any inventor surname appears in the entity's known name variants. Low precision (many false positives on common names) but zero additional data.
3. **Defer** — this signal is valuable for a small number of pairs; the structural + G&S signals handle most uncertainty; treat inventor alignment as future work.

**Recommendation: defer for Phase 6C. Implement manual annotation as Phase 6D** if the resolution loop identifies pairs where inventor context would change the score.

---

### Implementation plan

**Files changed:**

| File | Change |
|---|---|
| `specialist/matchmaker/score.py` | Add `semantic_score()`, extend `total_score()` with signal params |
| `specialist/matchmaker/link.py` | Add `rescore_candidates(path)` function using signal fields |
| `specialist/matchmaker/cli.py` | Add `--signals`, `--full`, `--resolve`, `--auto-fetch` flags; add `rescore` subcommand |
| `specialist/patent/signals.py` | No change (already correct) |
| `specialist/trademark/` | Add `enrich.py` — TSDR G&S fetch for a project's candidates |
| `specialist/trademark/cli.py` | Add `enrich <project>` subcommand |
| `src/markery/cli.py` | Wire `markery trademark enrich` |
| `tests/specialist/matchmaker/test_score.py` | Add semantic_score tests; test total_score with signal params |
| `tests/specialist/matchmaker/test_link.py` | Add rescore_candidates tests |

**New test coverage:**

- `semantic_score()` with all combinations of signal presence
- Semantic bonus cap at 0.25
- `total_score()` backward compatibility (existing tests must still pass unchanged)
- `rescore_candidates()` reads signal fields correctly
- Uncertainty band detection: pairs correctly classified as below/in/above band

---

### Open questions — Round 4

**Q1 — Score integration timing**

The plan above uses a two-pass architecture: generate structural scores first, enrich with signals separately, rescore. An alternative is to fetch and score inline during `generate_candidates()` — every pair is fully scored in one pass.

- **Two-pass (recommended):** Structural scores are immediately available. Signal enrichment is optional and additive. The researcher can inspect structural-only candidates before running signals.
- **Inline:** One command produces fully-scored candidates. Slower (DB queries per pair during generation). No intermediate state to inspect.

Which better fits how you work?

**Q2 — Score ceiling**

The plan caps semantic bonus at 0.25, giving a new max of ~1.05. An alternative is to rescale all components so the ceiling remains exactly 0.80 — pairs that currently score 0.80 would score lower, making room for semantic signals to push strong pairs toward 0.80.

- **Let ceiling rise to ~1.05 (recommended):** Existing score thresholds for review (0.5) are unchanged. A score above 0.80 becomes a new "semantic confirmation" tier.
- **Renormalize to 0.80:** Current scores shift downward. The review threshold must be recalibrated. Cleaner ceiling, breaking change.

**Q3 — Confidence band threshold**

The plan proposes [0.30, 0.60] as the uncertainty band. Does this match your experience reviewing the information-systems candidates? Are there pairs in the 0.30–0.60 range that signals genuinely resolved, or that turned out to be false positives structural signals should have discarded?

**Q4 — `markery trademark enrich` scope**

The TSDR G&S fetch is the most expensive new operation (API calls per trademark, rate-limited). Should `markery trademark enrich <project>` fetch for:
- Confirmed pairs only (small, high-value)
- Confirmed pairs + candidates above min-score (larger, more useful for resolution)
- All candidates in the uncertainty band (targeted, avoids unnecessary fetches)

---

## Decisions — Round 4 (2026-05-18)

| Question | Decision |
|---|---|
| Score integration timing | Two-pass: structural first, enrich+rescore as separate passes |
| Score ceiling | Uncapped additive — total can reach ~1.05; existing thresholds unchanged |
| Confidence band | Tighter: [0.40, 0.60] — drop pairs below 0.40, they aren't worth resolving |
| `markery trademark enrich` scope | Confirmed pairs + uncertainty band [0.40, 0.60] |

### Implications

**Two-pass confirmed** — the three-step flow stands as designed:
```
Pass 1: markery match <project>            → structural score
Pass 2: markery patent signals <project>   → adds signal fields
Pass 3: markery match rescore <project>    → updates score from signal fields
```
`markery match <project> --full` runs all three passes in sequence.

**Uncapped ceiling** — pairs that score above 0.80 after semantic bonus become a "semantic confirmation" tier requiring no reclassification of existing scores. The `min-score` threshold for review (currently 0.50) is unaffected.

**Tighter band [0.40, 0.60]** — pairs scoring below 0.40 on structural signals alone are discarded without resolution. This is a stricter filter than the initial [0.30, 0.60] proposal; it reduces the resolution workload and avoids spending API calls on structurally weak pairs.

**Enrich scope: confirmed + uncertainty band** — `markery trademark enrich <project>` fetches G&S text for:
1. All confirmed pairs (small, guaranteed value — needed for essay context)
2. All candidates in the [0.40, 0.60] band (targeted resolution)

Candidates outside the band (below 0.40 or above 0.60) are not enriched unless explicitly requested. This is the correct balance between API cost and resolution value.
