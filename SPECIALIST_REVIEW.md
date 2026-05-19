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

## Phase 6 Sequence (updated)

Dependencies flow left to right: BRIEF format must be resolved before `prepare` can be built; content types must be defined before publisher page types; static wiki must work before Wikipedia export is attempted.

**6A — Historian**

1. **BRIEF format decision** *(open question — see below)*
2. **`OBJECTIVES.md` format** — hand-maintained project thesis and scope; define structure; write information-systems version
3. **`references/` format** — define excerpt file structure; populate information-systems references (manual for in-copyright; IA fetch module for open-access)
4. **`markery historian prepare <project>`** — build `prepare.py` + CLI subcommand; output `BRIEF.md`
5. **Historian instruction cards** — `persona/instructions/` for patent-signals, trademark-enrich, candidate-refresh, figure-fetch
6. **New content schemas** — thematic essay, timeline annotation, sources page *(depends on thematic essay decision — see below)*

**6B — Publisher**

7. **New page types** — thematic essay and sources page rendering in `build.py` / `render.py` *(depends on thematic essay decision)*
8. **Cross-link rendering** — `[[Slug]]` → `<a href>` resolution in `_render_markdown()`
9. **Search index** — `search.json` built at site-build time; Pagefind integration
10. **Wikipedia scoping** — assess SOUNDEX article; determine contribution model *(depends on Wikipedia scope decision — see below)*
11. **IA retrieval module** — `markery librarian fetch <ia-identifier>` for open-access works

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

**Q3 — Thematic essays and site architecture**

Thematic essays (e.g. "The Card Index in American Business") are the content that makes the site interesting to a general reader rather than just a research record. Two architectural options:

- **Supplementary** — thematic essays are additional pages alongside the existing structure. The landing page stays stats-focused (entities, marks, patents, confirmed pairs); essays are linked from it as "deeper reading".

- **Primary narrative** — a thematic essay becomes the landing page. The site leads with the intellectual argument, not the database metrics. Stats and galleries are still present but accessed from the essay, not the other way around.

The second option produces a more compelling public site but requires the historian to produce a strong thematic essay before the site is "complete". Which framing fits how you want the site to present itself?
