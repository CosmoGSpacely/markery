# Markery — Project Constitution

This document defines what Markery is, how it works, and the structure of work within it.

---

## What Markery Is

**Markery is a tool that builds research projects using an agentic design pattern.** It is not a standalone application — it is a command-line toolkit that agents and humans invoke together. Work proceeds through a defined sequence of specialist operations, each callable independently, with the agent deciding what to run and when.

**Markery agents curate general-purpose patent and trademark databases that grow as projects need them.** The core databases (`patents.duckdb`, `trademarks.duckdb`, `entities.duckdb`) are not project-specific. They are shared infrastructure: a USPTO trademark bulk load, EPO patent records fetched by CPC class and year range, and a registry of named entities. Each project defines its own scope — which classes, which date windows, which entities — and the databases expand to cover that scope. Nothing project-specific is baked into the databases or the tool's source code.

**Markery projects are self-contained bodies of work that humans and agents build in collaboration.** A project defines a research question, a set of entities to track, and a scope over the shared databases. Within that scope, the agent generates candidate patent-trademark pairs, and the human reviews and confirms them. The confirmed pairs become the factual record that the project's published content rests on. Projects live under `projects/<name>/` and are entirely independent of each other.

**Markery agents organize the data and prepare results for publishing.** Once pairs are confirmed, the agent drafts research essays from a historian persona, resolves figure references, and renders the content as a static site. The human edits and approves. The agent builds and the historian writes; the human decides what is true and what ships.

---

## Specialist Agents

Markery is structured as five specialist agents. Each owns a bounded domain: its own database, its own external API credentials, and a defined set of operations. Cross-specialist calls route through `orchestrator.py`. No specialist imports directly from another.

---

### PATENT

**Owns:** `patents.duckdb` — bibliographic records, CPC classifications, inventors, figures.

**Role:** Acquires and maintains the patent corpus. Fetches patent records from the EPO OPS API by CPC class and year range, inserting into a shared database that grows as projects define new scope. Can also fetch individual patents by number, pull backward citation chains, and retrieve drawing figures as stored BLOBs. Resume state is tracked in `patents_fetch_log.json` alongside the database.

**Invoked:** At project setup (bulk class fetch), when a specific patent needs to be added on demand, and when figures are needed for review or publication.

**Credentials:** EPO OPS OAuth2 (`EPO_CONSUMER_KEY`, `EPO_CONSUMER_SECRET`).

---

### TRADEMARK

**Owns:** `trademarks.duckdb` — USPTO bulk tables (`case_file`, `owner`, `statement`, `classification`, and companions) plus TSDR enrichment tables (`mark_images`, `extended_marks`).

**Role:** Loads and maintains the trademark corpus. The bulk build imports the 2011 USPTO Trademark Case Files Dataset filtered to a caller-supplied date window; no default scope is assumed. The TSDR enrichment layer adds live API data: mark images, status, goods descriptions, and first-use dates. Enrichment is per-mark and on-demand; it extends the bulk record, not replaces it.

**Invoked:** Once at project setup (bulk build), then incrementally as the matchmaker or historian identifies marks that need enrichment.

**Credentials:** USPTO API key (`USPTO_API_KEY`).

---

### MATCHMAKER

**Owns:** `entities.duckdb` — `company_entity` (canonical names) and `entity_name_variant` (how each entity appears in patent assignee fields and trademark owner fields).

**Role:** Links entities to their patents and trademarks, generates scored candidate pairs, and writes `candidates.jsonl`. Scores each pair on three dimensions: date gap (trademark filed after patent grant), CPC class relevance, and semantic overlap between goods descriptions and patent text. Applies a hard exclusion for marks that are themselves company names. The entity registry is populated from per-project CSV files; the database is shared but each project scopes its queries through an `entities.txt` file.

**Invoked:** After both patent and trademark databases cover the project's scope. Reads all three databases simultaneously via DuckDB ATTACH.

**Credentials:** None.

---

### HISTORIAN

**Owns:** No database. Reads `candidates.jsonl`, writes `confirmed.jsonl` and `rejected.jsonl`.

**Role:** The human-facing review agent. Presents each candidate pair interactively (trademark details, patent details, date gap, score breakdown) and records the human's Y/N decision. Confirmed pairs become the authoritative factual record for the project. Also carries a defined scholar persona used for drafting research essays: the historian writes from a primary-source perspective, interprets confirmed pairs in their industrial and commercial context, and produces structured content files consumed by the publisher.

**Invoked:** During the review session (interactive), and when content drafts are needed.

**Credentials:** Anthropic API (for essay drafting).

---

### PUBLISHER

**Owns:** `site/` under each project — a rendered static site, gitignored and regenerable.

**Role:** Transforms confirmed pairs and historian essays into a publishable site. Resolves figure references (`[[figure:patent_no]]`) to stored BLOBs or on-disk PNGs, enhances trademark images, pulls Wikipedia summaries for entity pages, and renders Markdown content to HTML. The build is deterministic from the project's content files and confirmed data; running it again produces the same output.

**Invoked:** When the project's content is ready to publish or preview.

**Credentials:** None for rendering; Wikipedia API is unauthenticated.

---

## Two-Track Model

All work in this repository is either **tool work** (building and improving Markery) or **project work** (conducting research using Markery). Root documents describe the tool only. Each research project is self-contained in its own folder under `projects/`.

---

## Tool Work Lifecycle

```
DEFERRED.md  →  ROADMAP.md  →  STATUS.md  →  archive/
```

- **`DEFERRED.md`** — items that are known, intentional, and not currently active. Each has a reopen trigger. When a trigger fires, promote the item to `ROADMAP.md`.
- **`ROADMAP.md`** — active and upcoming tool development, organized into phases with explicit gates.
- **`STATUS.md`** — current state: infrastructure ledger and one-line status per active project. Updated at the end of each session.
- **`archive/`** — completed roadmaps and design records, datestamped. Never edited after archiving.

---

## Project Work Lifecycle

Each project under `projects/<name>/` is independent and defines its own workflow in its `README.md`. Projects vary in structure depending on what they are doing.

**Common to all projects:**

| Path | Purpose |
|---|---|
| `README.md` | Project overview and workflow description |
| `STATUS.md` | Project-local metrics and next action |
| `output/` | Enhanced images, PDFs — gitignored, regenerable |

**Match-review-essay projects** (e.g. `information-systems`) also have:

| Path | Purpose |
|---|---|
| `RESEARCH-AGENDA.md` | Candidate subjects, methodology, key references |
| `RESEARCH.md` | Scholarly framework |
| `entities.txt` | Entity IDs scoped to this project |
| `matches/candidates.jsonl` | Generated — never edited |
| `matches/confirmed.jsonl` | Hand-curated confirmed pairs |
| `content/` | Research essays and narrative pages |
| `site/` | Built static site — gitignored, regenerable |

**Gallery/exploration projects** (e.g. `monthly-image-review`) have a lighter structure — typically just `README.md`, `STATUS.md`, and `output/` galleries. They surface leads that may feed into match-review projects or stand alone as visual surveys.

A project's `README.md` is the authority on its workflow. `research-session.md` at root documents the match-review-essay workflow specifically.

Project-local `STATUS.md` carries the metrics and next action for that project. The root `STATUS.md` carries only a one-line summary per project.

---

## Root File Responsibilities

| File | What it contains |
|---|---|
| `CONTEXT.md` | This document — what Markery is and structural rules |
| `ROADMAP.md` | Active and upcoming tool development phases |
| `STATUS.md` | Tool infrastructure ledger + project summary table |
| `DEFERRED.md` | Deferred tool work with reopen triggers |
| `DESIGN.md` | Engineering rationale and architecture decisions |
| `SETUP.md` | New-machine setup instructions |
| `research-session.md` | Runnable operations checklist (project-agnostic) |
| `README.md` | Repository overview for new contributors |

---

## Specialist Reference Docs

Each specialist owns its API reference alongside its code:

| Doc | Owned by |
|---|---|
| `src/markery/specialist/patent/EPO.md` | Patent specialist — EPO OPS API reference |
| `src/markery/specialist/trademark/TSDR.md` | Trademark specialist — USPTO TSDR API reference |
| `src/markery/specialist/historian/persona/` | Historian specialist — Claude persona and content schemas |
