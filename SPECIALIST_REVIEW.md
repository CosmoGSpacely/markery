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

---

## Phase 6D — Temporal Extension: Out-of-Range Patent and Trademark Fetch

### The gap

Both databases are hard-filtered to 1900–1939 at build time. The filters are enforced by `build.py` parameters (`year_start`, `year_end`, `DATE_START`, `DATE_END`), not schema constraints — the underlying schemas have no date checks. This distinction matters: `insert_patent()` will happily insert a pre-1900 record; `mark_case_status` already accepts any date.

The limitation surfaces in two concrete situations:

1. **Prior art citations** — A confirmed patent like US1261167A (Soundex, 1918) cites earlier patents in its bibliography. Those citations may reference pre-1900 Library Bureau or card-index patents that are directly relevant to the project's historical argument. They exist in EPO OPS (which covers US patents from 1790 to present) but are absent from `patents.duckdb` because the bulk build only reaches back to 1900.

2. **Post-registration commercial longevity** — A trademark filed in 1927 (SOUNDEX, serial 71246709) may remain in active use through the 1940s and 1950s. Later filings by the same entity under the same or related marks show how a product brand persisted or evolved after the 1939 corpus boundary. These marks are in the 2011 USPTO CSV but filtered out by the `DATE_END` constraint.

---

### Decisions — Round 5 (2026-05-18)

| Question | Decision |
|---|---|
| Library Bureau patent origin | Pre-1900, cited in a confirmed patent's bibliography (not found through secondary literature) |
| Forward scope | 1940s–1950s only, trademarks showing continued commercial use |
| Trigger model | Both: explicit targeted fetch by number + citation-chasing discovery |
| Match role | Full participation — out-of-range records scored and surfaced as candidates |

### Implications

**Full participation** means out-of-range records enter the matchmaker's candidate pool alongside in-range records. A pre-1900 Library Bureau patent, once fetched, can produce a confirmed pair. This is the right design: the historical argument benefits from the full innovation chain, not only the 1900–1939 slice. The matchmaker's `date_score()` handles large temporal gaps naturally — a pre-1900 patent matched against a 1927 trademark will score on the same curve as any other pair; the researcher decides in review whether the gap is historically meaningful.

**Citation chasing** is depth-1 by default. Prior art citations of confirmed patents point to direct predecessors; going to depth 2 (citations of citations) expands exponentially and could pull in hundreds of tangentially related patents. Depth-2 is available as an explicit flag, not the default.

**Forward extension is trademark-only in Phase 6D.** Post-1939 patents (continuation work, successor inventions) are a different research question — the focus of the forward window is commercial longevity of already-confirmed marks, not new patent-trademark pairs from the 1940s.

---

### Current architecture (no changes needed at schema level)

| Database | Build constraint | Schema constraint | Out-of-range feasibility |
|---|---|---|---|
| `patents.duckdb` | `year_start=1900, year_end=1939` in `build.py` | None — `insert_patent()` accepts any date | Insert pre-1900 patent via targeted fetch: **already works** |
| `trademarks.duckdb` — `case_file` | `DATE_START`, `DATE_END` in `build.py` CSV load | None — date is just a column | Cannot insert into `case_file` via TSDR alone: **many CSV columns have no TSDR equivalent** |
| `trademarks.duckdb` — `mark_case_status` | None | None | Can store any date: **already works**, but not queried by matchmaker |

The patent path is straightforward: insert a pre-1900 patent into `patents.duckdb` the same way a seed patent is inserted. The trademark path requires a new table because `case_file` was designed for bulk CSV loading and has columns (draw code, mark_id_cd format, etc.) that TSDR case status does not provide.

---

### Patent specialist: backward extension

**New EPOClient method: `fetch_citations(patent_no) -> list[str]`**

EPO OPS provides a citations endpoint that returns a patent's prior-art references:

```
GET /3.2/rest-services/published-data/publication/epodoc/US{num}/citations
Accept: application/json
```

The response contains a `references-cited` block with `citation` entries. Each citation has a `patcit` (patent citation) node with a `document-id` carrying `@country`, `@doc-number`, `@kind`, and `@date`. The method filters for `@country == "US"`, constructs `US{doc_number}{kind}` strings, and returns the list. Non-patent citations (literature, `nplcit` nodes) are ignored.

Pagination: the citations endpoint is not paginated — it returns all citations in one response. For patents with many citations this is a single request.

**New CLI: `markery patent fetch <patent_no>`**

```bash
markery patent fetch US495147A
```

Wraps the existing `fetch_biblio(patent_no)` and `insert_patent(conn, record)` calls. No year check — the date filter is the responsibility of the `build` command, not the `fetch` command. Output:

```
US495147A  ✓ added to patents.duckdb  (grant_dt: 1893-04-04, assignee: LIBRARY BUREAU [US])
US789654A  — already present
```

Idempotent: `insert_patent()` already checks existence and returns `False` without inserting if the patent is already present.

**New CLI: `markery patent citations <project> [--auto-fetch] [--depth 1]`**

```bash
markery patent citations information-systems
markery patent citations information-systems --auto-fetch
markery patent citations information-systems --depth 2
```

Algorithm:
1. Read all confirmed patent numbers from `projects/<project>/matches/confirmed.jsonl`
2. For each, call `fetch_citations(patent_no)` → list of cited US patent numbers
3. Check which cited patents are already in `patents.duckdb`
4. Print resolution report:

```
Confirmed patent US1261167A (SOUNDEX, 1918) — 4 citations
  US495147A  (1893-04)  LIBRARY BUREAU [US]     — NOT IN CORPUS → candidate
  US523014A  (1894-07)  HALL THOMAS S [US]      — NOT IN CORPUS → candidate
  US1183571A (1916-05)  already in corpus
  US1219636A (1917-03)  already in corpus

Confirmed patent US1435663A (SOUNDEX, 1922) — 2 citations
  US1261167A (1918-04)  already in corpus
  US495147A  (1893-04)  already in corpus (fetched above)

Out-of-range candidates: 2 new patents
  Run: markery patent fetch US495147A US523014A
  Or:  markery patent citations information-systems --auto-fetch
```

With `--auto-fetch`: fetches and inserts all out-of-range citations immediately after the report.

With `--depth 2`: repeats the citation fetch for each newly discovered out-of-range patent (one additional level). Depth-2 should warn about scale ("N additional patents found at depth 2; confirm before fetching").

**Files changed — patent specialist:**

| File | Change |
|---|---|
| `specialist/patent/epo_client.py` | Add `fetch_citations(patent_no) -> list[str]` method |
| `specialist/patent/build.py` | Add `fetch_one(patent_no, conn, client) -> bool` function wrapping `fetch_biblio` + `insert_patent` |
| `specialist/patent/cli.py` | Add `fetch <patent_no>` subcommand; add `citations <project>` subcommand |
| `specialist/patent/EPO.md` | Document the citations endpoint (URL, response structure, parsing notes) |
| `src/markery/cli.py` | Wire `markery patent fetch` and `markery patent citations` |
| `tests/specialist/patent/test_epo_client.py` | Add `fetch_citations` unit test (mock response) |
| `tests/specialist/patent/test_build.py` | Add `fetch_one` unit test |

---

### Trademark specialist: forward extension

**New schema: `extended_marks` in `trademarks.duckdb`**

`extended_marks` stores out-of-range trademarks fetched via TSDR. It holds the subset of `case_file` columns the matchmaker needs, plus an `entity_id` column that bypasses the need for the `owner → entity_name_variant` join used for in-range marks.

```sql
CREATE TABLE IF NOT EXISTS extended_marks (
    serial_no         VARCHAR PRIMARY KEY,
    mark_text         VARCHAR,
    filing_dt         DATE,
    registration_no   VARCHAR,
    registration_dt   DATE,
    status_cd         VARCHAR,
    goods_desc        VARCHAR,
    intl_class        VARCHAR,
    first_use_dt      VARCHAR,
    first_use_comm_dt VARCHAR,
    entity_id         INTEGER,       -- FK to entities.duckdb company_entity
    source            VARCHAR DEFAULT 'tsdr_extended',
    fetched_dt        DATE
);
```

The `entity_id` column is the critical addition. `case_file` has no entity column — the matchmaker discovers the entity relationship through `owner → entity_name_variant`. For `extended_marks`, the researcher supplies the entity association at fetch time (or the `entity-forward` command infers it from the CSV owner name match). This makes the matchmaker's `extended_marks` query simpler and faster.

The DDL belongs in `trademark/build.py` (the `_ENRICHMENT_DDL` block) so it is created alongside `mark_images` and `mark_case_status` on every `open_db()` call. This means `extended_marks` exists (empty) in any trademarks.duckdb created or opened after Phase 6D ships, with no migration required.

**New CLI: `markery trademark fetch <serial_no> [--entity-id <id>]`**

```bash
markery trademark fetch 71550000 --entity-id 1
```

1. Calls `client.fetch_case_status(serial_no)` (existing method in `tsdr_client.py`)
2. Also calls `client.fetch_mark_image(serial_no)` and stores into `mark_images`
3. Upserts into `mark_case_status` (existing enrichment table)
4. Upserts into `extended_marks` with the supplied `entity_id`
5. Output: one-line summary per serial

If `--entity-id` is omitted, the record is inserted into `mark_case_status` only (not `extended_marks`) and therefore does not participate in matching. The researcher must supply an entity association for the mark to become matchable.

**New CLI: `markery trademark entity-forward <project> [--window 1940-1959] [--csv csv/]`**

```bash
markery trademark entity-forward information-systems --window 1940-1959 --csv csv/
```

Discovers post-1939 trademarks filed by confirmed entities, using the full 2011 USPTO CSV (which contains post-1939 marks filtered out by the build command):

1. Loads entity IDs from `projects/<project>/matches/confirmed.jsonl` (unique entity_ids from confirmed pairs)
2. Loads all name variants for those entities from `entities.duckdb`
3. Runs a DuckDB query against the raw `owner.csv` and `case_file.csv` files (via `read_csv_auto()`, not `trademarks.duckdb`) filtering to the forward window:

```sql
SELECT cf.serial_no, cf.filing_dt, cf.mark_id_char, o.own_name
FROM read_csv_auto('csv/case_file.csv', ...) cf
JOIN read_csv_auto('csv/owner.csv', ...) o USING (serial_no)
WHERE o.own_name IN ('REMINGTON RAND INC', 'REMINGTON RAND INC.', ...)
  AND cf.filing_dt >= '1940-01-01'
  AND cf.filing_dt <= '1959-12-31'
ORDER BY cf.filing_dt
```

4. Prints a candidate list for the researcher to review:

```
Entity: Remington Rand (entity_id 1)
  71520000  SOUNDEX         1941-03-12  REMINGTON RAND INC
  71531000  VARIADEX        1942-07-08  REMINGTON RAND INC
  71588000  KARDEX VISIBLE  1948-01-15  REMINGTON RAND INC.
  ...
  12 candidates in window 1940–1959

To fetch: markery trademark fetch <serial_no> --entity-id 1
```

The researcher reviews the list and selects marks to fetch. No automatic fetch — the forward window can produce many marks, and the researcher should judge which are relevant to the project's thesis (commercial longevity of a specific product line, not every Remington Rand mark from the era).

**Files changed — trademark specialist:**

| File | Change |
|---|---|
| `specialist/trademark/build.py` | Add `extended_marks` DDL to `_ENRICHMENT_DDL`; add to `open_db()` |
| `specialist/trademark/enrich.py` | Add `store_extended_mark(serial_no, parsed, entity_id, conn)` function; update `store_case_status()` to also write `extended_marks` when `entity_id` is supplied |
| `specialist/trademark/cli.py` | Add `fetch <serial_no>` subcommand; add `entity-forward <project>` subcommand |
| `src/markery/cli.py` | Wire `markery trademark fetch` and `markery trademark entity-forward` |
| `tests/specialist/trademark/test_enrich.py` | Add `store_extended_mark` unit test |

---

### Matchmaker: include extended_marks in candidate generation

`link.py` generates candidates by joining `patents` with `case_file` via entity name variants. To include `extended_marks`, a second query path is added: one that joins `patents` with `extended_marks` directly via the stored `entity_id` (bypassing the `owner → entity_name_variant` join, since extended marks already carry the entity association).

```python
def generate_candidates(project, conn_tm, conn_pt, conn_ent, ...) -> int:
    # Existing path: patents × case_file via entity name variants
    n1 = _generate_from_case_file(...)
    # New path: patents × extended_marks via entity_id
    n2 = _generate_from_extended_marks(...)
    return n1 + n2
```

Deduplication: `candidates.jsonl` deduplicates by `(patent_no, trademark_serial)`. The same pair cannot be generated from both paths because `extended_marks` serial numbers are distinct from `case_file` serial numbers (they are out-of-range marks not loaded by the build).

The new `_generate_from_extended_marks()` function is a simplified version of the existing generator: it queries `extended_marks` filtered by `entity_id IN (...)` and joins against `patents` by assignee entity_id. This is simpler than the current case_file path because the entity relationship is pre-stored.

**Files changed — matchmaker:**

| File | Change |
|---|---|
| `specialist/matchmaker/link.py` | Add `_generate_from_extended_marks()` function; call it in `generate_candidates()` |
| `tests/specialist/matchmaker/test_link.py` | Add test: extended_marks candidates are generated when table is populated |

---

### Full CLI surface — Phase 6D additions

```bash
# Patent: targeted fetch
markery patent fetch US495147A

# Patent: citation discovery
markery patent citations information-systems
markery patent citations information-systems --auto-fetch
markery patent citations information-systems --depth 2

# Trademark: targeted fetch (requires --entity-id for match participation)
markery trademark fetch 71550000 --entity-id 1

# Trademark: forward entity scan
markery trademark entity-forward information-systems
markery trademark entity-forward information-systems --window 1940-1959 --csv csv/
```

---

### What the Library Bureau workflow looks like end-to-end

1. `markery patent citations information-systems` — discovers that US1261167A cites US495147A (1893, Library Bureau) and US523014A (1894) as prior art
2. Researcher reviews the report — both citations are relevant (Library Bureau was a direct predecessor in card-index technology)
3. `markery patent fetch US495147A US523014A` — inserts both patents into `patents.duckdb`
4. Optionally add Library Bureau as an entity in `entities.duckdb` (`markery matchmaker build`)
5. `markery match information-systems` — Library Bureau patents now appear as candidates against Library Bureau trademarks (ARMORCLAD, AUTOMATIC, LB — all in the existing 1900–1939 corpus, 17 patents already present)
6. Review and confirm matching pairs; write essays grounding the pre-1900 patents in the project's argument about the card-index technology lineage

---

## Gap Analysis — Agent-to-Agent Communication

A survey of the specialist codebase against the agentic design intent stated in `DESIGN.md`:

> "The long-term design intent is that each specialist can be called by a hosted or local model without modification: the queries API is the model's tool interface, the CLI is the human interface, and the two are kept deliberately separate."

Six gaps stand between the current state and that intent.

---

### G1 — Interface contract exists but Python implementations do not

`specialist/historian/persona/interface.md` already defines a clean abstract tool interface — `trademarks.for_entity()`, `patents.for_entity()`, `entities.get()`, `matches.for_project()` — with DuckDB SQL implementations for each. This is the right design. The gap is that these implementations exist only as documentation examples, not as callable Python functions.

`DESIGN.md` states: "Each specialist exposes three layers: a **queries module** (pure DB reads, no side effects)..." Only the matchmaker approximates this (`link.py`, `entities.py`, `score.py`). Patent and trademark have no `queries.py`. Publisher has no `queries.py`.

**Missing modules:**

| Module | Functions needed |
|---|---|
| `specialist/patent/queries.py` | `get_patent(conn, patent_no)`, `get_patents_for_entity(conn, entity_id)`, `get_cpc_classes(conn, patent_no)`, `has_abstract(conn, patent_no)`, `has_figure(conn, patent_no)`, `get_missing_signals(conn, patent_nos)` |
| `specialist/trademark/queries.py` | `get_mark(conn, serial_no)`, `get_marks_for_entity(conn, entity_id)`, `has_image(conn, serial_no)`, `has_case_status(conn, serial_no)`, `get_goods_desc(conn, serial_no)`, `get_missing_enrichment(conn, serial_nos)` |
| `specialist/publisher/queries.py` | `get_content_gaps(project)`, `get_rendered_pages(project)`, `content_gap_priority(gap)` |

Until these exist, any model calling the interface must inline SQL — coupling the caller to the DB schema and making the abstraction in `interface.md` nominal rather than real.

**Consequence for Phase 6A:** `markery historian prepare` will need to detect content gaps (what's missing from the site). Without `publisher/queries.py`, it either duplicates publisher logic or triggers a full site build to interrogate the output. Neither is correct.

---

### G2 — The historian interface is read-only; operation requests have no protocol

The current interface in `interface.md` supports data retrieval only. The historian can ask "what patents exist for entity X?" but cannot request "run signals on patent Y" or "fetch the figure for patent Z."

Phase 6A's instruction cards are the human-readable version of operation requests — templates the historian fills in and the researcher executes manually. But for agentic operation, the historian needs to emit structured requests that a Python controller can execute without human relay. No such schema exists.

**The gap:** a request schema and a request executor.

**Proposed request schema** (Phase 7 prerequisite to design now):

```json
{
  "action": "patent_signals",
  "target": {"patent_no": "US1261167A"},
  "project": "information-systems",
  "reason": "Abstract needed to compute abstract_name_hit for SOUNDEX pair"
}
```

Actions: `patent_signals`, `patent_figure`, `trademark_enrich`, `trademark_image`, `candidate_refresh`, `patent_citations`. Each maps to a specific specialist function. The controller validates the request, calls the function, returns a structured result.

The request executor lives in a new `specialist/orchestrator.py` — the only module permitted to import from multiple specialists for write/operation calls. This also resolves the cross-specialist call policy question from Phase 6C's `--auto-fetch` design (G5 below).

**Consequence for Phase 6C:** `markery match <project> --auto-fetch` currently has no defined mechanism for how the matchmaker triggers patent signals and trademark enrichment. The request schema gives it one.

---

### G3 — No negative feedback channel from reviewer to matchmaker

The interactive reviewer (`review.py`) captures Y/N decisions. Y writes to `confirmed.jsonl`. N is silently discarded. The matchmaker regenerates every candidate on every run — including all pairs the researcher has explicitly rejected.

**Effect:** a researcher who has reviewed 500 candidates and rejected 480 gets all 480 rejections again on the next `markery match` run. The workflow degrades in usability the more it is used. This is the most practically painful gap in the current system.

**Fix:**

1. `projects/<project>/matches/rejected.jsonl` — populated by the reviewer on N, with the same schema as `confirmed.jsonl` plus a `rejection_note` field
2. `common/config.py` `Project` class gets a `rejected` path property
3. `matchmaker/link.py` `generate_candidates()` reads `rejected.jsonl` at the start and filters those pairs out of output
4. `review.py` prompts for an optional rejection note (same as the confirmation note) before writing to `rejected.jsonl`

Downstream: rejected pairs form a negative training signal for Phase 7 scoring refinement. A structural-only score of 0.65 that was rejected by the researcher is more informative than a 0.65 that was never reviewed.

---

### G4 — Workflow state is held entirely in candidates.jsonl, which is overwritten on each run

`candidates.jsonl` is the sole durable artifact of the match pipeline. Running `markery match <project>` overwrites it completely — losing all signal enrichment and rescoring written by previous passes.

Phase 6C's three-pass flow (generate → enrich → rescore) assumes that all three passes run in a single session. If the session ends after Pass 2 (signal enrichment), Pass 3 can be run separately only if `candidates.jsonl` still exists with the enriched signal fields. But if the researcher runs `markery match <project>` again (even to check on fresh data), the enrichment is lost.

**Fix: `projects/<project>/matches/pipeline_state.json`**

A small JSON file written by each pass:

```json
{
  "generated_at":  "2026-05-18T14:00:00",
  "enriched_at":   "2026-05-18T14:05:00",
  "rescored_at":   null,
  "candidate_count": 512,
  "enriched_count":  512,
  "score_p50":       0.42,
  "score_p90":       0.71
}
```

Behavior: `markery match <project>` checks `pipeline_state.json`. If `generated_at` is recent and the researcher did not pass `--force`, it warns: "candidates.jsonl was generated today; use --force to regenerate." This prevents accidental overwrites that discard enrichment work.

`markery match rescore <project>` (Phase 6C) checks whether `enriched_at` is set before rescoring — refusing to rescore unenriched candidates.

`markery status` includes the pipeline state in project metrics.

---

### G5 — No cross-specialist call policy for operations

`DESIGN.md` permits DuckDB `ATTACH` for cross-specialist reads: "Cross-specialist ATTACH is used to join entities, patents, and trademarks in a single query — permitted per Q19." This covers all read operations cleanly.

Phase 6C's `--auto-fetch` requires the matchmaker to invoke patent signals and trademark enrichment — write/operation calls that `ATTACH` does not cover. No policy governs this. Can `matchmaker/link.py` import from `specialist.patent.signals`? The design intent says specialists own their domain; importing across specialist boundaries creates coupling.

**The gap:** the policy covers reads (DuckDB ATTACH) but not operations (Python function calls across specialists).

**Resolution:** the orchestrator pattern from G2 resolves this. `specialist/orchestrator.py` is the only module permitted to import from multiple specialists for operation calls. The matchmaker's `--auto-fetch` invokes the orchestrator, not the patent or trademark specialist directly. The orchestrator:

- Receives a list of operation requests (from the matchmaker's uncertainty band report)
- Calls the appropriate specialist functions in order
- Returns a structured result to the matchmaker for rescoring

This keeps specialist boundaries clean. The matchmaker imports only from `orchestrator`; `orchestrator` imports from all specialists.

---

### G6 — Historian persona files don't describe the Phase 6A session protocol

`specialist/historian/persona/` contains five files: `identity.md`, `rules.md`, `interface.md`, `examples.md`, and a `reference/` directory. Together they define who the historian is, what it knows, and how it queries data.

None of the persona files describe how the historian should use `BRIEF.md` (planned in Phase 6A), how it should handle session startup, or how it should structure operation requests to other specialists (the schema from G2). These will need to be written alongside 6A implementation — not after.

**Needed additions to persona:**

1. `persona/session-protocol.md` — how to open a session: read `BRIEF.md` first, confirm the highest-priority gap with the researcher, state scope boundaries before proceeding. How to close a session: identify any unresolved requests, state what should be run before the next session.

2. `interface.md` extension — add an **Operations** section alongside the current **Queries** section. Operations are requests the historian can emit but not execute: `patents.run_signals(patent_no)`, `trademark.enrich(serial_no)`, etc. Each operation has a structured format (the schema from G2) and a human-readable equivalent (the instruction card from Phase 6A-4).

3. `rules.md` addition — a rule for when to emit operation requests vs. when to proceed without additional data: "If a confirmed pair lacks signal fields and the essay would be strengthened by them, emit a `patent_signals` request. Do not block essay writing on unfetched data — write with what is available and note what is missing."

---

### Priority and dependencies

The gaps above are independent in cause but dependent in fix order:

```
G1 (queries.py modules)
  └── G6 (persona session protocol) — can be written in parallel, but needs G1 for implementation
  └── Phase 6A prepare command — needs publisher/queries.py

G2 (request schema + orchestrator)
  └── G5 (cross-specialist call policy) — orchestrator resolves this
  └── Phase 6C --auto-fetch — needs orchestrator to be clean

G3 (rejected.jsonl) — independent; fix is small and high-value
G4 (pipeline_state.json) — independent; fix is small and prevents data loss
```

**Implementation sequence (decided 2026-05-18):**

| Order | Gap | When | Rationale |
|---|---|---|---|
| 1 | G3 — rejected.jsonl | Now, before any phase | Highest practical impact, smallest change; workflow degrades without it |
| 1 | G4 — pipeline_state.json | Now, before any phase | Prevents enrichment loss during Phase 6C development |
| 2 | G1 — queries.py modules | Before Phase 6A | Prerequisite for prepare command (publisher/queries.py) and for G6 |
| 3 | G6 — persona session protocol | During Phase 6A | Persona updates written alongside the prepare command; G1 gives the Operations section real implementations to reference |
| 4 | G2 — request schema + orchestrator | Between 6A and 6C | Prerequisite for Phase 6C `--auto-fetch`; 6A context informs what operations are needed |
| 5 | G5 — cross-specialist call policy | During Phase 6C | G5 is resolved *by* the G2 orchestrator; lands when `--auto-fetch` is implemented |

G5 is not a separate implementation item — the orchestrator from G2 *is* the policy resolution. Documenting G5 as "during Phase 6C" means: when the orchestrator is built, add a one-paragraph note to `DESIGN.md` formalising the rule ("operation calls across specialists route through `specialist/orchestrator.py`").

---

## Implementation — G3: rejected.jsonl (2026-05-19)

**Commit:** 125a284

G3 adds a negative feedback channel from the reviewer to the matchmaker. Previously, N-key decisions were silently discarded; every `markery match` run regenerated all rejected pairs alongside new ones.

### Files changed

| File | Change |
|---|---|
| `src/markery/common/config.py` | Add `rejected` property to `Project` dataclass |
| `src/markery/specialist/matchmaker/link.py` | Add `read_rejected()` function |
| `src/markery/specialist/historian/review.py` | Add `load_rejected()`, `write_rejected()`; update `main()` |
| `tests/specialist/matchmaker/test_link.py` | 3 new tests for `read_rejected` |
| `tests/specialist/historian/test_review.py` | 4 new tests for `load_rejected` / `write_rejected` |

### `common/config.py` — new `Project` property

```python
@property
def rejected(self) -> Path:
    return self.root / "matches" / "rejected.jsonl"
```

### `matchmaker/link.py` — new `read_rejected()`

```python
def read_rejected(path: Path) -> set[tuple]:
    """Load rejected.jsonl as a set of (patent_no, trademark_serial) tuples."""
    if not path.exists():
        return set()
    pairs: set[tuple] = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        pairs.add((row["patent_no"], str(row["trademark_serial"])))
    return pairs
```

`str()` normalization on `trademark_serial` is required: the field is stored as an integer in some JSONL files (the candidate generator writes it as int) and as a string in others. The reviewer's filter key uses `str(c["trademark_serial"])` to match.

`read_rejected()` lives in `link.py` (not `review.py`) because it is the matchmaker's consumer of the file — it reads the set to filter candidates before writing `candidates.jsonl`. This keeps the write path (`review.py`) separate from the read path (`link.py`).

### `matchmaker/cli.py` — candidate filtering

In `_run_project()`:

```python
rejected_keys = read_rejected(proj.rejected)
candidates = [
    c for c in candidates
    if (c["patent_no"], str(c["trademark_serial"])) not in rejected_keys
]
```

Run before `write_candidates()`. Rejected pairs are excluded from `candidates.jsonl` on every subsequent generation pass without any further action from the researcher.

### `historian/review.py` — two new functions

```python
def load_rejected(path: Path) -> set[tuple]:
    if not path.exists():
        return set()
    return {
        (json.loads(l)["patent_no"], json.loads(l)["trademark_serial"])
        for l in path.read_text().splitlines()
        if l.strip()
    }

def write_rejected(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

`load_rejected()` in `review.py` uses `trademark_serial` without `str()` normalization — it matches against the reviewer's own in-memory key format, which is consistent within a session. The string normalization is only needed in `link.py` where the keys may come from different JSONL sources.

In `main()`, the queue filter adds `key not in already_rejected`, and the N branch calls:

```python
write_rejected(rejected_path, {
    "patent_no":         cand["patent_no"],
    "trademark_serial":  cand["trademark_serial"],
    "trademark":         cand["trademark"],
    "entity_id":         cand["entity_id"],
    "entity":            cand["entity"],
    "rejection_note":    "",
})
```

Session summary says "rejected" (not "skipped") and counts `rejected_n` separately from `skipped_n`.

### Key design decisions

**No rejection note prompt.** Unlike confirmation (which prompts for a note before writing), the N key writes immediately with `rejection_note: ""`. Prompting for a note on every N keypress would add a mandatory Enter for each of potentially hundreds of rejections in a session. The empty field is preserved in the schema for future annotation if needed.

**`rejection_note: ""`** is included in the written record deliberately — it reserves the field in the JSONL schema so downstream tooling (Phase 7 scoring refinement) can parse it without schema changes.

---

## Implementation — G4: pipeline_state.json (2026-05-19)

**Commit:** 3ac91cf

G4 protects enriched candidate data from accidental overwrite. Before this change, running `markery match` again after a signal enrichment pass silently destroyed all enrichment work by regenerating `candidates.jsonl` from scratch.

### Files changed

| File | Change |
|---|---|
| `src/markery/common/config.py` | Add `pipeline_state` property to `Project` dataclass |
| `src/markery/specialist/matchmaker/pipeline.py` | New file — state tracking functions |
| `src/markery/specialist/matchmaker/cli.py` | Guard + `--force` flag; call `mark_generated()` |
| `src/markery/specialist/patent/cli.py` | Call `mark_enriched()` after `cmd_signals()` |
| `src/markery/specialist/historian/status.py` | Show pipeline state in project summary |
| `tests/specialist/matchmaker/test_pipeline.py` | New file — 10 tests |

### `common/config.py` — new `Project` property

```python
@property
def pipeline_state(self) -> Path:
    return self.root / "matches" / "pipeline_state.json"
```

### `matchmaker/pipeline.py` — new module

Six public functions:

```python
def read_state(path: Path) -> dict
    # Returns {} if file is missing or malformed JSON.

def mark_generated(path: Path, candidate_count: int, scores: list[float]) -> None
    # Writes generated_at (now), clears enriched_at and rescored_at,
    # sets candidate_count, score_p50, score_p90. Clears enriched_count.

def mark_enriched(path: Path, enriched_count: int) -> None
    # Merges into existing state: sets enriched_at (now), enriched_count,
    # clears rescored_at. Preserves generated_at and score percentiles.

def mark_rescored(path: Path) -> None
    # Merges into existing state: sets rescored_at (now).

def is_enriched(path: Path) -> bool
    # True if enriched_at is set in the current state.

def _percentile(values: list[float], p: float) -> float | None
    # Simple sorted-index percentile. Returns None for empty list.
    # No numpy/statistics dependency — sufficient precision for score distributions.
```

**State JSON structure:**

```json
{
  "generated_at":  "2026-05-19T14:00:00",
  "enriched_at":   "2026-05-19T14:05:00",
  "rescored_at":   null,
  "candidate_count": 512,
  "enriched_count":  512,
  "score_p50":       0.42,
  "score_p90":       0.71
}
```

### Cascading state resets

`mark_generated()` clears both `enriched_at` and `rescored_at`. `mark_enriched()` clears `rescored_at`. This means each pass invalidates downstream passes automatically — the state always reflects the most recent complete pass chain, not a mix of timestamps from different runs. The rule is: if you re-run a pass, all later passes are stale.

### `matchmaker/cli.py` — guard and `--force`

In `_run_project()`:

```python
if not force and is_enriched(proj.pipeline_state):
    print(
        f"WARNING: candidates.jsonl has enriched signal fields "
        f"(enriched_at set). Regenerating will lose enrichment work. "
        f"Use --force to regenerate anyway."
    )
    return
```

After writing candidates:

```python
mark_generated(
    proj.pipeline_state,
    candidate_count=len(candidates),
    scores=[c["score"] for c in candidates],
)
```

`--force` flag added to `match_main()` parser. The guard checks `is_enriched()` specifically — not just `is_generated()` — because regenerating un-enriched candidates is harmless; the expensive work to protect is signal enrichment.

### `patent/cli.py` — mark enriched after signals

After `cmd_signals()` completes its enrichment loop:

```python
from markery.specialist.matchmaker.pipeline import mark_enriched
mark_enriched(project.pipeline_state, enriched_count=n)
```

`n` is the count of candidates that received signal enrichment. This updates `pipeline_state.json` without touching `candidates.jsonl`.

### `historian/status.py` — pipeline state in project summary

```python
if pipeline_path.exists():
    ps = json.loads(pipeline_path.read_text())
    gen = (ps.get("generated_at") or "")[:10]
    enr = ps.get("enriched_at")
    enr_str = f"  enriched {enr[:10]}" if enr else ""
    pipeline_str = f"  (generated {gen}{enr_str})"

print(f"    candidates: {candidates:,}{pipeline_str}")
```

`markery status` output now shows both the candidate count and the pipeline timestamps inline, e.g. `candidates: 512  (generated 2026-05-19  enriched 2026-05-19)`.

### Test coverage

`tests/specialist/matchmaker/test_pipeline.py` — 10 tests:

- `test_read_state_missing_file` — returns `{}`
- `test_read_state_malformed_json` — returns `{}`
- `test_mark_generated_writes_fields` — verifies all fields written correctly
- `test_mark_generated_clears_enriched` — enriched_at reset on re-generate
- `test_mark_enriched_sets_timestamp` — enriched_at set; rescored_at still null
- `test_mark_enriched_clears_rescored` — rescored_at cleared by re-enrichment
- `test_mark_rescored_sets_timestamp`
- `test_is_enriched_false_when_missing`
- `test_percentile_empty_scores` — both percentiles return None
- `test_state_file_is_valid_json` — verifiable JSON with expected shape after multiple passes

---

## Implementation — G1: queries.py modules (2026-05-19)

**Commit:** 1f44ce5

G1 creates the callable Python query layer that `interface.md`'s abstract tool interface requires. Without these modules, any model using the historian interface would need to inline SQL — coupling the caller to the DB schema.

### Files created / modified

| File | Change |
|---|---|
| `src/markery/specialist/patent/queries.py` | New — 6 functions, conn-as-parameter |
| `src/markery/specialist/trademark/queries.py` | New — 6 functions, conn-as-parameter |
| `src/markery/specialist/publisher/queries.py` | Modified — added `get_content_gaps()` and `get_rendered_pages()` |
| `tests/specialist/patent/test_queries.py` | New — 18 tests |
| `tests/specialist/trademark/test_queries.py` | New — 21 tests |
| `tests/specialist/publisher/test_queries.py` | Modified — 11 new tests added |

### `patent/queries.py` — 6 functions

```python
def connect() -> duckdb.DuckDBPyConnection
    # Opens a read-only connection to patents.duckdb.

def get_patent(conn, patent_no: str) -> dict | None
    # Returns {patent_no, title, app_dt, grant_dt, abstract, assignee_name,
    #          cpc_classes: list[str], inventors: list[str]} or None.

def has_abstract(conn, patent_no: str) -> bool
    # True if abstract is non-null and non-empty.

def has_figure(conn, patent_no: str) -> bool
    # True if a non-null figure_data BLOB exists in patent_figures.

def get_cpc_classes(conn, patent_no: str) -> list[str]
    # Returns distinct 4-char CPC class codes. Empty list if not found.

def get_missing_signals(conn, patent_nos: list[str]) -> list[str]
    # Returns patent_nos from the list whose abstract is NULL or empty.
    # Order from input list is preserved.
```

All functions take `conn` as their first argument. The caller controls connection lifetime and tests inject in-memory connections via `open_db(":memory:")` from `patent/build.py`.

### `trademark/queries.py` — 6 functions

```python
def connect() -> duckdb.DuckDBPyConnection
    # Opens a read-only connection to trademarks.duckdb.

def get_mark(conn, serial_no: str) -> dict | None
    # Returns {serial_no, mark_name, filing_dt, draw_cd, registration_no,
    #          status_cd} or None. serial_no is always returned as str.

def has_image(conn, serial_no: str) -> bool
    # True if a non-null image_data BLOB exists in mark_images.

def has_case_status(conn, serial_no: str) -> bool
    # True if any row exists in mark_case_status for this serial.

def get_goods_desc(conn, serial_no: str) -> str | None
    # Checks statement.statement_text first; falls back to
    # mark_case_status.goods_desc. Returns None if neither has text.

def get_missing_enrichment(conn, serial_nos: list[str]) -> list[str]
    # Returns serial_nos not covered by either statement or mark_case_status.
    # A serial covered by either table is excluded from the result.
    # Input list order is preserved.
```

`get_goods_desc()` checks `statement` first because it is populated during the bulk CSV build and is the authoritative source for in-range marks. `mark_case_status.goods_desc` is the TSDR-enriched fallback, written by `enrich.py`. The priority reflects data provenance: bulk CSV data predates TSDR enrichment.

`get_missing_enrichment()` computes the union of covered serials across both tables before filtering. This correctly handles the case where a serial has `statement` text but no `mark_case_status` row (or vice versa).

### `publisher/queries.py` — two new functions

**Discovery:** the publisher already had substantial coverage when examined for G1 implementation: `get_entities()`, `get_trademarks_for_project()`, `get_patents_for_project()`, `get_confirmed_matches()`, and `get_entity_stats()` were all present. Only `get_content_gaps()` and `get_rendered_pages()` were genuinely absent. The G1 inventory in the gap analysis overestimated what was missing here.

```python
def get_content_gaps(project: str) -> list[dict]
    # Returns gaps sorted by (priority, slug).
    # Priority 1: match essays missing from content/<slug>.md (one per confirmed pair slug, deduplicated)
    # Priority 2: entity summaries missing from content/entity-<slug>.md
    # Priority 3: sources.md and timeline.md if absent
    #
    # Each gap dict: {type, slug, priority, label, path}
    # Calls get_confirmed_matches() and get_entities() internally.

def get_rendered_pages(project: str) -> list[str]
    # Returns sorted relative paths of all .html files under site/.
    # Returns [] if site/ does not exist.
```

`get_content_gaps()` priority tiers match the `content_gaps` YAML schema defined in Round 3 — `BRIEF.md` will consume this function's output directly. The deduplication of match essay slugs prevents a trademark that appears in multiple confirmed pairs from generating multiple essay gap entries.

### conn-as-parameter design rationale

The patent and trademark query modules use conn-as-parameter consistently. This was chosen over the publisher's internal-connection pattern because:

1. **Testability** — tests inject `open_db(":memory:")` without touching any file. No patching of `DB["patents"]` or `DB["trademarks"]` is needed.
2. **Lifetime control** — callers that need to run multiple queries over a batch can open one connection and pass it to each function, avoiding repeated connect/close overhead.
3. **Alignment with `interface.md`** — the abstract tool interface in the historian persona specifies connection-taking functions (`trademarks.for_entity(conn, entity_id)`). The conn-as-parameter pattern makes the Python implementation match the interface's intent.

Publisher queries retain the internal-connection pattern because they open three databases via ATTACH — a connection that the caller cannot easily construct — and because the publisher's callers (the site builder and `BRIEF.md` generation) are one-shot batch operations where lifetime control is less important.

### Test coverage summary

`tests/specialist/patent/test_queries.py` — 18 tests covering: None on missing patent, dict on found, CPC classes and inventors populated, `has_abstract` true/false/null/empty, `has_figure` with and without BLOB, `get_cpc_classes` distinct deduplication, `get_missing_signals` all combinations (all absent, all present, mixed, unknown IDs).

`tests/specialist/trademark/test_queries.py` — 21 tests covering: `get_mark` None and dict, serial_no string type guarantee, `has_image` with null BLOB vs real BLOB vs no row, `has_case_status` true/false, `get_goods_desc` statement priority over case_status, null-statement fallback, `get_missing_enrichment` covered-by-statement, covered-by-case-status, covered-by-both, all-missing, input order preserved.

`tests/specialist/publisher/test_queries.py` — 11 new tests covering: `get_rendered_pages` with no site, sorted paths, non-HTML ignored; `get_content_gaps` all priority levels present/absent, existing files excluded, sort order verified, slug deduplication. Publisher tests mock `get_confirmed_matches()` and `get_entities()` via `unittest.mock.patch` — no real DB connection required.

156 tests pass after G1 implementation (full suite).

---

## Implementation — G6: Historian session protocol (2026-05-19)

**Commit:** 966d0bd  (bundled with Phase 6A)

G6 closes the gap between the historian persona files and the Phase 6A session workflow. Before this change, nothing in `persona/` described how a session should start, how BRIEF.md should be used, or how the historian should emit structured operation requests.

### Files changed

| File | Change |
|---|---|
| `persona/session-protocol.md` | New — session open/close protocol |
| `persona/interface.md` | Modified — added Operations section |
| `persona/rules.md` | Modified — added Operation Requests rule block |

### `persona/session-protocol.md` — new file

Defines five steps for opening a session: (1) read BRIEF.md and verify its `prepared:` timestamp, (2) read OBJECTIVES.md for project thesis and scope, (3) confirm the session task with the researcher, (4) check `signals_available` before beginning, (5) start content production from the highest-priority gap.

Closing protocol: state what was produced, list any unresolved operation requests with the commands needed to resolve them before the next session, and avoid summarizing content the researcher already knows.

Session startup checklist table (five rows: read BRIEF.md, read OBJECTIVES.md, confirm task, check signals, begin writing) gives a scannable orientation format for session open.

The key behavioral guarantee: if BRIEF.md does not exist or is stale, the historian asks the researcher to run `markery historian prepare <project>` before proceeding rather than working from a cold state.

### `persona/interface.md` — Operations section

Added between the Markery Implementation section and the Portability Note. The Operations section defines:

**Request schema:**
```json
{
  "action": "<operation_name>",
  "target": { "<field>": "<value>" },
  "project": "<project_name>",
  "reason": "<why this data is needed>"
}
```

**Six supported operations** with CLI equivalents:

| Action | CLI equivalent | What it produces |
|---|---|---|
| `patent_signals` | `markery patent signals <project>` | Abstract text and signal fields |
| `patent_figure` | `markery patent figures <patent_no>` | Figure BLOB in `patent_figures` |
| `trademark_enrich` | `markery trademark enrich <project>` | Goods/services text from TSDR |
| `trademark_image` | `markery trademark enrich <serial_no>` | Mark image BLOB |
| `candidate_refresh` | `markery match <project>` | Fresh candidate list |
| `patent_citations` | `markery patent citations <project>` | Prior-art citation list |

Two worked examples (fetch abstract for a patent, fetch figure for KARDEX) show how the schema is used in context.

The section closes with guidance on when to emit an operation request: when confirmed pair lacks abstract text, when a figure in `figures_available` hasn't been described, when G&S text is absent, or when the candidate list appears stale. The "do not block" rule — write with available data, note what is missing — is restated here in the interface context.

**Design note:** The Operations section is forward-compatible. In the current human-in-the-loop workflow, the historian states the request in natural language (via instruction cards) and the researcher runs it. The structured JSON schema is the agentic future path — when a controller exists, it reads the schema directly. Both paths coexist because the instruction cards reference the same action names.

### `persona/rules.md` — Operation Requests block

Inserted before the Never section. Three rules:

1. **Emit operation requests when data would strengthen the analysis — never block writing on them.** With a worked example of how to note a missing abstract in an essay without halting the session.

2. **Emit operation requests proactively at session start.** If BRIEF.md shows missing abstracts or G&S text for confirmed pairs, name them before writing essays for those pairs so the researcher can run fetches while the session opens.

3. **Do not emit operation requests for data already available.** If a patent appears in `signals_available`, the abstract is in the database. Emitting a redundant request wastes researcher time.

---

## Implementation — Phase 6A: Project orientation and historian prepare (2026-05-19)

**Commit:** 966d0bd

Phase 6A establishes the project document structure (OBJECTIVES.md, references/, BRIEF.md) and implements `markery historian prepare` — the prepare command that generates a fresh BRIEF.md before each historian session.

### 6A-1 — OBJECTIVES.md

**Format defined** (YAML frontmatter + markdown body):

```yaml
---
site_mode: narrative          # or: metrics
wikipedia_targets:
  enrich: [SOUNDEX]
  create: [KARDEX]
scope:
  date_range: "1900-1939"
  technology: "..."
  geography: "United States (primary)"
  cpc_classes: [B42F, B42D, ...]
---
```

Markdown body sections: **Thesis**, **Scope Boundaries**, **Target Audience**, **Content Priorities**.

**`projects/information-systems/OBJECTIVES.md` written.** Key content:

- *Thesis:* American office-systems manufacturers of 1900–1939 systematically bridged invention and product by filing trademarks for the branded names under which their patented indexing and filing systems were sold. The filing record — not trade press or corporate archives — is the primary evidence, because it survived where physical records have not.
- *Scope:* 1900–1939 USPTO dataset; B42F, B42D, B41J, B41L, G06C, G06K, G09F CPC classes; entities: Remington Rand, Wilson Jones, Yawman & Erbe, Boorum & Pease. Pre-1900 via citation chaining (Phase 6D), post-1939 commercial continuity (Phase 6D).
- *Hollerith boundary:* Tabulating machines are adjacent, not central — different CPC classes. Austrian's biography is reference context, not a source for confirmed pairs.
- *Target audience:* Layered — general reader for landing/thematic content; specialist for match essays and source notes; Wikipedia standard for any contributed articles.
- *Wikipedia targets:* enrich SOUNDEX article (primary-source citations), draft KARDEX article (secondary-source grounded).
- *Content priorities:* HANDIREF essay (missing companion to REDIREF); entity summary for Library Bureau (precursor entity, citation-chain candidate); deepen SOUNDEX and KARDEX essays.

**`common/config.py`** — three new `Project` properties:

```python
@property
def objectives(self) -> Path:
    return self.root / "OBJECTIVES.md"

@property
def brief(self) -> Path:
    return self.root / "BRIEF.md"

@property
def references(self) -> Path:
    return self.root / "references"
```

**`.gitignore`** — added `projects/*/BRIEF.md`. BRIEF.md is ephemeral (regenerated by `prepare` before each session) and must never be committed, as a stale brief is worse than no brief.

---

### 6A-2 — References format and information-systems skeletons

**`projects/<project>/references/README.md`** defines the file format:

```markdown
---
author: Last, First
title: Full Title
year: 1989
ia_identifier: <IA item slug>
ia_access: borrow | open | restricted
---

## Overview

## Relevant passages

### [Topic]
> "Direct quotation." (p. 42)
Context note.
```

Files are named `<author-surname>-<short-title>.md`. Passages are organized by topic (not page order) because the historian searches by subject, not by chapter. The `ia_identifier` field enables future automated retrieval from the Internet Archive.

**Three skeleton files written** for information-systems:

| File | Author | IA access |
|---|---|---|
| `yates-control-through-communication.md` | Yates, JoAnne (1989) | borrow |
| `cortada-before-the-computer.md` | Cortada, James W. (1993) | borrow |
| `austrian-herman-hollerith.md` | Austrian, Geoffrey D. (1982) | borrow |

Each file has an Overview section (one paragraph on the book's argument and its relevance to this project) and placeholder `### [Topic]` sections with comments indicating what passages should be added. The researcher fills in the actual passages from the physical or IA-borrowed copy; the structure is pre-built.

---

### 6A-3 — `markery historian prepare <project>`

**New file: `specialist/historian/prepare.py`**

Five public functions, separated by concern so each is independently testable:

```python
def gather_confirmed(proj: Project) -> list[dict]
    # Read confirmed.jsonl; add essay_path by computing slug and checking content/

def gather_patent_state(conn, patent_nos: list[str]) -> dict[str, dict]
    # Per-patent: {abstract: bool, figure: bool}
    # Uses has_abstract() and has_figure() from patent/queries.py

def gather_trademark_state(conn, serial_nos: list[str]) -> dict[str, bool]
    # Per-trademark: goods description available?
    # Uses get_goods_desc() from trademark/queries.py

def count_unreviewed(proj: Project, min_score: float = 0.5) -> int
    # Candidates above threshold not in confirmed or rejected (file-based)

def top_candidates(proj: Project, min_score: float = 0.5, n: int = 5) -> list[dict]
    # Top N unreviewed candidates by score descending

def render_brief(project, confirmed, gaps, patent_state, tm_state,
                 unreviewed_count, top_cands, prepared_at) -> str
    # Pure function: builds full BRIEF.md string from gathered data

def prepare(project: str, min_score: float = 0.5) -> None
    # Orchestrates: gathers data, calls render_brief, writes proj.brief
```

**`prepare()` connection handling:** opens patent and trademark connections (read-only, via `patent/queries.connect()` and `trademark/queries.connect()`), gathers state, closes both before calling publisher queries. The `finally` block ensures connections close even if an error occurs mid-gather.

**Essay path computation** in `prepare()` (not in `gather_confirmed`): after loading from JSONL, each confirmed pair gets `essay_path` set from the slug derived by `.lower().replace(" ", "-")`. This matches the slug convention used by `publisher/queries.get_confirmed_matches()` and `get_content_gaps()`.

**BRIEF.md format** — YAML frontmatter followed by five markdown sections:

```yaml
---
project: information-systems
prepared: 2026-05-19T11:21:45
confirmed_count: 8
candidate_count_unreviewed: 1903
content_gaps:
  - {type: sources_page, slug: sources, priority: 3}
signals_available:
  [US1261167A, US1435663A]
figures_available:
  []
enriched_trademarks:
  ["71246709", "71255821", ...]
---
```

Sections: **Project State** (confirmed pairs with ✓ essay / **no essay** tags), **Content Gaps** (ranked by priority), **Candidate Highlights** (table of top unreviewed by score), **Available Signals** (patents with abstract, patents with figure), **Session Recommendation** (first gap stated as a plain task).

**Session recommendation logic:** picks the first gap from the sorted gap list and produces a prescriptive one-line task. If no gaps exist, recommends a thematic essay or sources page. This gives the historian a default starting point without requiring the researcher to re-read the full gap list.

**`specialist/historian/cli.py`** — replaced the placeholder stub with real argparse:

```
markery historian prepare <project> [--min-score SCORE]
```

**`src/markery/cli.py`** — added `historian` to `_SUBCOMMANDS` and `cmd_historian()`.

### Live output (information-systems, 2026-05-19)

```
BRIEF.md written → projects/information-systems/BRIEF.md
  8 confirmed pairs  ·  1903 unreviewed candidates
  2 content gap(s)  ·  signals: 2/7 patents
```

Content gaps: `sources_page` and `timeline_page` (P3 only — all match essays and entity summaries already exist). `signals_available`: US1261167A, US1435663A (the two SOUNDEX patents have abstracts in the DB). All 7 confirmed trademarks have goods descriptions (`enriched_trademarks` fully populated).

### 6A-4 — Specialist instruction cards

**`persona/instructions/`** — new directory with four files:

| Card | When to use | CLI it requests |
|---|---|---|
| `patent-signals.md` | Missing abstract text for confirmed pairs | `markery patent signals <project>` |
| `trademark-enrich.md` | Missing G&S description for confirmed marks | `markery trademark enrich <project>` |
| `figure-fetch.md` | Figure not yet described in essay | `markery patent figures <patent_no>` |
| `candidate-refresh.md` | Candidate list stale after entity changes | `markery match <project>` |

Each card specifies: when to use (including when NOT to use — check BRIEF.md first), what the command produces, where the output lands, the human-readable request to make to the researcher, the structured JSON request (for agentic use), and expected output. The `candidate-refresh.md` card includes the important warning about `--force` when enrichment has already been run.

### 6A-5 — New content schemas and identity.md update

**Three new content schema files:**

`persona/content-schemas/thematic-essay.md` — cross-entity narrative synthesizing multiple confirmed pairs. Key design: explicit layered audience handling within one document. Two registers are specified per section: *accessible* (general reader, no assumed knowledge, magazine register) and *technical depth* (specialist, citation-precise, academic register). The opening argument and context sections use accessible register; the evidence section uses technical depth. Length target 800–1,500 words.

`persona/content-schemas/sources-page.md` — consolidated project bibliography. Four sections: (1) USPTO trademark filings (confirmed serials with TSDR links), (2) US patents (confirmed numbers with Google Patents links), (3) secondary literature (Chicago author-date from `references/` files), (4) archival sources if applicable. Closes with a method note paragraph documenting the cross-reference research technique. Format: bulleted lists throughout, no narrative except the method note.

`persona/content-schemas/timeline-annotation.md` — annotated chronological entries for the full arc. Format: `### [Year]` headings, bold event description, 1–3 sentence context per entry. Preamble (100–150 words) and closing note (50–100 words) as unmarked prose. Site builder reads `###` heading format to detect entry boundaries. Length: 15–30 entries for a project with 8 confirmed pairs.

**`persona/identity.md`** — added **Writing Register — Layered Audience** section between Areas of Strength and Explicit Limits. Defines three registers with explicit format guidance:

- *General reader* — landing, thematic essay leads, entity summary leads: magazine register, define terms on first use, open with historical situation not record identifiers
- *Specialist reader* — match essays, source notes, patent/trademark sections: evidence-forward, explicit serial and publication number citations, gaps acknowledged
- *Wikipedia standard* — any Wikipedia-bound content: neutral POV, secondary-source grounded, no original research

The registers coexist: a thematic essay opens in general-reader, transitions to specialist for evidence, closes in general-reader. Active register per section is defined in each content schema.

### Test coverage

`tests/specialist/historian/test_prepare.py` — 20 tests:

- `gather_patent_state`: abstract true/false/null, figure true/false, empty list
- `gather_trademark_state`: goods desc present/absent, empty list
- `count_unreviewed`: basic count, excludes confirmed, excludes below min_score, excludes rejected, empty candidates
- `top_candidates`: sorted by score descending, returns at most N
- `render_brief`: YAML frontmatter present, signals in YAML, content gaps listed, session recommendation present, no-gaps message, candidate highlights table

176 tests pass after Phase 6A + G6 implementation (full suite).

---

## Phase 6B Implementation — 2026-05-19

**Commit:** 11fc37b — "Implement Phase 6B: new page types, cross-links, search, Wikipedia tooling"

### Files modified

| File | Change |
|---|---|
| `src/markery/specialist/publisher/render.py` | New page renderers, cross-link support, search form, CSS additions |
| `src/markery/specialist/publisher/build.py` | Full rewrite: theme detection, link index, search.json, pagefind |
| `src/markery/specialist/wikipedia/__init__.py` | New module |
| `src/markery/specialist/wikipedia/wikitext.py` | Markdown → MediaWiki wikitext converter |
| `src/markery/specialist/wikipedia/api.py` | MediaWiki API client |
| `src/markery/specialist/wikipedia/cli.py` | `markery wikipedia draft / submit` CLI |
| `src/markery/cli.py` | `wikipedia` subcommand wired up |
| `tests/specialist/publisher/test_render_6b.py` | 29 new tests |
| `tests/specialist/wikipedia/test_wikitext.py` | 15 new tests |

### 6B-1 — New page types

Three optional page types, each sourced from a content file the historian writes:

| Source file | Output page | Render function |
|---|---|---|
| `content/theme-<slug>.md` | `themes/<slug>.html` | `render_thematic_essay()` |
| `content/sources.md` | `sources.html` | `render_sources_page()` |
| `content/timeline.md` | `timeline.html` | `render_timeline_page()` |

All three render placeholder text when the source file does not exist, so `build_site()` can call them unconditionally without failing on incomplete projects.

**`render_timeline_page()`** generates two SVG timelines (patent grants + trademark filings) from the existing database records, then renders the historian's `timeline.md` annotations (which use `### YYYY` headings) below them using the standard `_render_markdown()` pipeline.

**`render_thematic_essay()`** extracts the essay title from the first `# Heading` line in the content file (falls back to the slug). Strips YAML frontmatter before rendering.

**OBJECTIVES.md integration:** `_parse_site_mode(proj)` reads `site_mode:` from the YAML frontmatter of `OBJECTIVES.md` using a regex (no PyYAML dependency). Returns `"narrative"` if missing. Consumed by `build_site()` but the landing page architecture switch between `narrative` and `metrics` modes is deferred to Phase 6C when the content is available to warrant it.

### 6B-2 — Cross-link rendering

`_render_markdown()` gains two new optional parameters:

```python
def _render_markdown(
    text: str,
    link_index: dict[str, str] | None = None,
    depth: int = 0,
) -> str:
```

**Implementation:** Before per-line processing, `[[Slug]]` occurrences are stashed (like fenced code blocks) into a shared `stash` dict, keyed with `\x00LINK{n}\x00` sentinels. The stash values are pre-built `<a href="...">` tags with the correct `../` prefix for the page's depth. After `_esc()` runs on each content line (which leaves the `\x00` sentinel intact), the stash values are restored by a dict scan. This keeps `[[Slug]]` out of code blocks (which are stashed first) and avoids double-escaping.

**`build_link_index(entities, matches, theme_slugs) -> dict[str, str]`** builds the slug→root-relative-URL mapping used for resolution:
- Entity slugs → `entities/<slug>.html`
- Match slugs → `matches/<slug>.html`
- Theme slugs → `themes/<slug>.html`

All existing render functions (`render_landing`, `render_trademark_gallery`, `render_patent_gallery`, `render_entity_page`, `render_match_essay`) gain optional `link_index` and `extra_nav` parameters, threaded through from `build_site()`. Backward-compatible: existing call sites with no link_index behave identically.

Unknown slugs resolve to plain text (link removed, display text kept), not broken `<a>` tags.

### 6B-3 — Search index + search page

**`search.json`** is written to the site output directory at the end of every build. Format:

```json
[
  {"title": "...", "type": "match_essay", "url": "matches/soundex.html", "excerpt": "..."},
  ...
]
```

`_text_excerpt(path, max_chars=200)` strips frontmatter, headings, bold, inline code, fenced blocks, and `[[cross-links]]` from the markdown source, then normalizes whitespace before truncating.

**`render_search_page()`** produces `search.html` with a self-contained client-side JavaScript search engine (~40 lines) that:
1. Fetches `search.json` lazily on first query
2. Filters records by substring match across title + excerpt
3. Renders clickable results with type badges and excerpts

**`_run_pagefind(out_dir)`** is called at the end of `build_site()`. If the `pagefind` binary is in PATH, it runs `pagefind --site <out_dir>` to build a full-text index. If not installed, it skips silently. The search page works either way: `search.json` provides the baseline, Pagefind provides enhanced search if available.

**Header search form:** `_page()` now emits a `<form class="site-search">` in the site header that submits `?q=` to `search.html`. Styled with CSS to sit right-aligned in the dark header bar.

**Extra nav links** are built by `_build_extra_nav()` in `build_site()` and passed to all render functions. Entries added for each thematic essay by title, plus Timeline, Sources, and Search when those pages exist.

### 6B-4 — Wikipedia tooling

**`specialist/wikipedia/wikitext.py`** — `markdown_to_wikitext(text)` converts the historian's markdown to MediaWiki syntax:

| Markdown | Wikitext |
|---|---|
| `## Heading` | `== Heading ==` |
| `### Sub` | `=== Sub ===` |
| `**bold**` | `'''bold'''` |
| `*italic*` / `_italic_` | `''italic''` |
| `[text](url)` | `[url text]` |
| `` `code` `` | `<code>code</code>` |
| ```` ```lang\n...\n``` ```` | `<syntaxhighlight lang="lang">` |
| `[[cross-link]]` | `[[cross-link]]` (left as wikilink for researcher review) |

`build_draft_wikitext()` wraps `markdown_to_wikitext()` and appends a `== Sources ==` section with `<references />`, structured primary source entries (USPTO serial number, patent number), and Wikipedia category tags.

**`specialist/wikipedia/api.py`** — `WikipediaClient`:
- Credentials from `WIKIPEDIA_USERNAME` and `WIKIPEDIA_BOT_PASSWORD` env vars
- Bot password authentication (`lgtoken` → login flow)
- `get_page(title)` — fetches current wikitext via `revisions` API; returns `None` for missing pages
- `edit_page(title, wikitext, summary)` — full-page replacement with CSRF token
- `append_section(title, section_title, content, summary)` — adds a new section (for citation-only enrichments)

**`markery wikipedia draft <project> <slug>`** — generates wikitext from the match essay and saves to `projects/<project>/wikipedia/<slug>.wiki`. Requires the match essay to exist.

**`markery wikipedia submit <project> <slug>`** — shows a `unified_diff` of the draft vs. current Wikipedia content (or vs. empty for new articles), then prompts `[y/N]` before POSTing. Uses `page_title` from CLI `--title` flag, falling back to `match["wikipedia_title"]` or the trademark name.

### Design decisions

**No PyYAML dependency:** `_parse_site_mode()` uses `re.search(r'^site_mode:\s*(\w+)', ...)` rather than parsing the full YAML frontmatter. This avoids adding a dependency for a one-field read. The OBJECTIVES.md frontmatter has a richer structure, but only `site_mode` is consumed programmatically by the publisher.

**Pagefind as optional post-processing:** The site build always produces `search.json` (the primary search mechanism). Pagefind adds full-text search if the binary is installed. This means the build works in CI without Pagefind installed, and researchers can add Pagefind to the workflow incrementally.

**Wikipedia `[[cross-links]]` preserved as wikilinks:** The historian writes `[[SOUNDEX]]` as cross-links within the Markery site. In wikitext, `[[SOUNDEX]]` is a Wikipedia internal link to the SOUNDEX article. This is intentional: the historian's cross-links become Wikipedia internal links in the draft, which the researcher reviews and adjusts before submitting.

### Test coverage

`tests/specialist/publisher/test_render_6b.py` — 29 tests:
- `_strip_frontmatter`: removes YAML block, noop without markers, noop single dash
- `_render_markdown` cross-links: resolves known slug, depth-0/depth-1 prefix, unknown slug → plain text, no index → no links, inline placement, does not affect code blocks
- `_parse_site_mode`: reads from OBJECTIVES.md, default narrative when missing
- `build_link_index`: entities, matches, themes, combined, match without slug
- `_text_excerpt`: strips markdown, strips frontmatter, missing file, truncation
- `render_thematic_essay`: creates file, placeholder when source missing
- `render_sources_page`: creates file, placeholder when source missing
- `render_timeline_page`: creates file with year entries rendered, placeholder when source missing
- `render_search_page`: creates file, search.json fetch in JS, query input present

`tests/specialist/wikipedia/test_wikitext.py` — 15 tests:
- `markdown_to_wikitext`: all heading levels, bold, italic (asterisks + underscores), markdown links, inline code, fenced blocks, cross-link preservation, frontmatter stripping, plain paragraph
- `build_draft_wikitext`: sources section present, categories present, essay body converted

220 tests pass after Phase 6B implementation (full suite).

---

## Phase 6C Implementation — 2026-05-19

**Commit:** 81713c3 — "Implement Phase 6C: semantic matchmaker scoring and resolution loop"

All Phase 6C code is in the **matchmaker specialist** (`specialist/matchmaker/`), as directed.

### Files modified

| File | Change |
|---|---|
| `src/markery/specialist/matchmaker/score.py` | `semantic_score()`, extended `total_score()`, `SEMANTIC_CAP` |
| `src/markery/specialist/matchmaker/link.py` | `rescore_candidates()`, `resolve_report()`, `_parse_date()`, `UNCERTAINTY_BAND` |
| `src/markery/specialist/matchmaker/cli.py` | `rescore` subcommand, `--signals`, `--full`, `--resolve`, `--auto-fetch` flags |
| `tests/specialist/matchmaker/test_score_6c.py` | 18 new tests |
| `tests/specialist/matchmaker/test_link_6c.py` | 9 new tests |

### 6C-1 — `semantic_score()` in score.py

Pure function, no external dependencies. Four additive components:

| Component | Condition | Value |
|---|---|---|
| `title_hit_score` | `title_name_hit == True` | +0.20 |
| `abstract_hit_score` | `abstract_name_hit == True` | +0.10 |
| `goods_title_score` | `goods_title_overlap > 0.05` | +0.10 |
| `goods_abstract_score` | `goods_abstract_overlap > 0.05` | +0.05 |

`SEMANTIC_CAP = 0.25` is defined as a module-level constant so tests can reference it directly and the cap value is single-sourced.

`total_score()` gains four keyword arguments (all defaulting to zero/False) and applies the cap internally:

```python
def total_score(
    grant_dt, filing_dt, cpc_classes,
    title_name_hit=False, abstract_name_hit=False,
    goods_title_overlap=0.0, goods_abstract_overlap=0.0,
) -> float:
    structural = date_score(grant_dt, filing_dt) + class_score(cpc_classes)
    semantic   = min(SEMANTIC_CAP, semantic_score(...))
    return round(structural + semantic, 4)
```

Calling `total_score(grant_dt, filing_dt, cpc_classes)` without signal args is identical to the pre-6C behaviour — existing callers unaffected.

**Design decision:** `semantic_score()` returns the raw (uncapped) bonus; `total_score()` applies the cap. This makes the raw signal contribution testable independently of the cap.

### 6C-2 — `rescore_candidates(path)` in link.py

Pass 3. Reads `candidates.jsonl`, recomputes every candidate's `score` field as `structural + min(SEMANTIC_CAP, semantic_bonus)`, writes in-place. Uses `_parse_date()` to convert ISO date strings back to `datetime.date` objects for scoring.

Candidates without signal fields (no `title_name_hit`, etc.) are rescored with zero semantic bonus — identical to their original structural score. This means `rescore_candidates` is safe to run on a candidates file that has not been enriched.

**`_parse_date(s: str | None) -> date | None`** — shared helper for both `rescore_candidates` and `resolve_report`. Handles `None`, empty string, and malformed dates without raising.

**`UNCERTAINTY_BAND: tuple[float, float] = (0.40, 0.60)`** — module-level constant for the structural confidence band.

### 6C-3 — `resolve_report(project)` in link.py

Reads `candidates.jsonl`, computes structural score for each candidate, identifies those in `UNCERTAINTY_BAND`. Queries both specialist databases **via their published query APIs** (not cross-specialist ATTACH):

- `patent.queries.has_abstract(conn, patent_no)` — checks `patents.duckdb`
- `trademark.queries.get_goods_desc(conn, serial_no)` — checks `trademarks.duckdb`

Returns:
```python
{
    "band_count":        int,     # pairs in [0.40, 0.60] structural band
    "missing_abstracts": list[str],  # patent_nos without abstract text
    "missing_goods":     list[str],  # serial_nos without G&S text
    "resolvable":        int,    # pairs where BOTH are present — can rescore now
}
```

### 6C-4 — CLI additions in cli.py

**`markery match rescore <project>`** — Pass 3 only. Dispatched before the main argparse parser by checking `sys.argv[1] == "rescore"`. This avoids argparse collision with the existing `project` positional argument (which would otherwise consume `"rescore"` as a project name).

**New flags on `markery match <project>`:**

| Flag | Behaviour |
|---|---|
| `--signals` | Pass 1 + 2: generate + enrich with text signals |
| `--full` | Pass 1 + 2 + 3: generate + enrich + rescore |
| `--resolve` | After Pass 1, print uncertainty band report |
| `--auto-fetch` | With `--resolve`: enrich + rescore resolvable pairs automatically |

**`--auto-fetch` scope:** Runs the signal enrichment pass (reads from existing DB data, no external API calls) and then rescores. Pairs that need external data fetch (missing patent abstracts from EPO, missing G&S from TSDR) are identified in the report but not auto-fetched — the researcher runs the specialist fetch commands for those. This keeps `--auto-fetch` atomic and safe (no live API calls from matchmaker).

**Resolution report output:**
```
47 pair(s) in uncertainty band [0.40, 0.60]
  Missing abstracts : 12 patent(s)
    → run: markery patent signals <project>
  Missing G&S text  : 8 trademark(s)
    → run: markery trademark enrich-project <project> --source candidates --min-score 0.40
  Resolvable now    : 27 pair(s)
    → run: markery match rescore <project>
```

### Placement decision

All 6C code is in `specialist/matchmaker/`. The `resolve_report()` function reads from patent and trademark databases but does so via their published query module APIs (`patent.queries.has_abstract`, `trademark.queries.get_goods_desc`) — this is read-only specialist API usage, not a cross-specialist ATTACH query. The actual fetch logic (EPO API, TSDR API) remains in the patent and trademark specialists.

### Test coverage

`tests/specialist/matchmaker/test_score_6c.py` — 18 tests:
- `semantic_score`: zero when no signals, each component individually, below-threshold does not fire, at-threshold for goods overlap does not fire, all signals sum correctly
- `SEMANTIC_CAP` value is 0.25
- `total_score`: backward compatibility (no-signal call unchanged), max without signals = 0.80, title_hit bonus exactly +0.20, all-signals cap enforced, None dates still allow semantic bonus, result rounded to 4 decimal places

`tests/specialist/matchmaker/test_link_6c.py` — 9 tests:
- `_parse_date`: valid ISO, None, empty string, invalid string
- `UNCERTAINTY_BAND` values (0.40, 0.60)
- `rescore_candidates`: score updated, title_hit adds +0.20 delta, semantic cap enforced, no-signal-fields uses structural only, missing file, other fields preserved, multi-row

247 tests pass after Phase 6C implementation (full suite).
