# Design Decisions

Engineering rationale for the Markery architecture. The research rationale is in `RESEARCH.md`; the scholarly argument for studying this period and subject is there, not here. This document covers the technical choices and the tradeoffs made consciously.

---

## Why DuckDB

DuckDB is a column-oriented analytical database optimized for read-heavy aggregation workloads — exactly the query pattern of historical research. The typical research query is a range scan across filing dates, a GROUP BY on owner name, or a cross-join between two sets of records. DuckDB handles these faster than SQLite and without the operational overhead of Postgres.

The decisive feature for this project is the single-file format. Each database is a single `.duckdb` file committed to the repository. The three database files together are ~25 MB — small enough to commit, portable across machines, and shareable as complete artifacts. No server, no connection pooling, no migration scripts. A researcher cloning the repo immediately has access to the full dataset.

The Python API returns results directly as Python objects or Pandas DataFrames, and DuckDB's `ATTACH` feature enables cross-database queries without copying data. Both are important for a project where data exploration happens in notebooks and ad-hoc scripts as much as in formal pipelines.

**Alternative considered:** SQLite. Row-oriented, slower for analytical aggregations, no `ATTACH` for cross-database joins. Rejected.

---

## Why Three Databases

Each database has an independent source and independent rebuild path:

- `trademarks.duckdb` — built from the USPTO bulk CSV download (a static 2011 snapshot)
- `patents.duckdb` — built by querying the EPO OPS API, class by class, year by year
- `entities.duckdb` — hand-maintained canonical company registry

Separation means a database can be rebuilt, extended, or replaced without touching the others. Adding new CPC classes to `patents.duckdb` does not require dropping or reloading trademark data. Changing the entity registry does not invalidate either primary source.

DuckDB's `ATTACH` makes cross-database joins as syntactically simple as single-database joins — there is no duplication penalty for keeping them separate. The entity registry exists specifically as a cross-reference hub: it holds no primary source data, only the mappings between name variants in the other two databases. Merging it into either primary database would couple two independently-sourced datasets.

**Alternative considered:** One database with all tables. Rejected because a schema change or rebuild in one source would ripple across all data, and the mixed-provenance schema would be harder to reason about.

---

## Why Human Curation, Not Automated Confirmation

The intellectual claim in a confirmed patent-trademark pair — that a specific patent describes the invention underlying a specific product name — is a historical judgment, not an algorithmic one.

A high scoring pair might still be wrong: a company could have filed a trademark for a product line that predated the patent, or scored 0.80 because the dates align without any product correspondence. A low-scoring pair might still be right: the SOUNDEX trademark predates the Odell patent by five years, but the pair is clearly valid.

The error asymmetry is also lopsided. A false positive in `confirmed.jsonl` corrupts the scholarly record; a false negative means a pair is simply unrecognized until someone notices it. Given this, human review before confirmation is not a workflow convenience — it is the appropriate epistemic standard for a research tool making historical claims.

`candidates.jsonl` is generated automatically and is never edited. `confirmed.jsonl` is curated by hand and is what the research essays are built from.

---

## The Scoring Formula

Two additive components, max 0.80:

**Temporal score (max 0.5):** Patent grant date precedes trademark filing date → positive, tapering from 0.5 at zero gap to 0.0 at 20 years. Trademark filed before patent grant → slight negative (max −0.4), which is not disqualifying — brand names often preceded specific patents. The 20-year taper is intentional: a 15-year gap is less compelling evidence than a 2-year gap, but should not score zero.

**Classification score (0.3, binary):** Fires when any of the patent's CPC classes falls in the product signal set (B42F, B42D, B41J, B41L, G06C, G06K, G09F). Binary rather than graded because the CPC classifications for pre-1940 patents were applied retroactively by algorithmic mapping — fine-grained subgroup precision is not reliable enough to justify a graded signal.

The model scores candidate identification, not confirmation. The 0.80 ceiling is intentional: a perfect score would imply a certainty the model cannot deliver.

---

## Tradeoffs Made Consciously

**Image blobs in DuckDB.** Mark images are stored as BLOBs in `mark_images` rather than as files on disk. This keeps the database self-contained and portable, but means the `.duckdb` file grows when images are added and must be committed in full. Acceptable at the current scale (~96 images); would need reconsideration at thousands.

**ATTACH over materialized joins.** Cross-database queries via `ATTACH` require all three database files to be present. For a project where all three are committed to the repository, this is fine. In a distributed or multi-user context it would require rethinking.

**Additive scoring over interaction terms.** The linear additive model is interpretable and easy to explain. It misses interaction effects (a close temporal match plus a matching CPC class should probably score higher than the sum of independent components). Kept simple intentionally — the model's purpose is candidate ranking, not probabilistic confirmation.

---

## Specialist Ownership Pattern

The codebase is organized into five specialists under `src/markery/specialist/`. Each specialist owns exactly one data source and all functionality that reads from or writes to it.

| Specialist | Owns | CLI entry point |
|---|---|---|
| `patent/` | `data/patents.duckdb` | `markery patent` |
| `trademark/` | `data/trademarks.duckdb` | `markery trademark` |
| `matchmaker/` | `data/entities.duckdb` | `markery match / matchmaker` |
| `historian/` | `confirmed.jsonl`, interactive review | `markery review / status` |
| `publisher/` | Site output, image enhancement | `markery site / enhance / publisher` |

A specialist exposes three layers: a **queries module** (pure DB reads, no side effects), a **build/pipeline module** (writes or transforms), and a **CLI module** (entry point). Cross-specialist reads use DuckDB `ATTACH` where a join cannot be expressed through individual specialist APIs without multiple round trips — this is the only permitted cross-specialist coupling.

Each specialist also owns its reference documentation: `EPO.md` lives in `specialist/patent/`, `TSDR.md` lives in `specialist/trademark/`, and the historian Claude persona lives in `specialist/historian/persona/`.

---

## Projects as Independent Research Units

Research projects live under `projects/<name>/` and are entirely independent of each other. A project contains only:
- Configuration (`entities.txt`) — which entity IDs are in scope
- Curated data (`matches/confirmed.jsonl`) — hand-reviewed pairs
- Content (`content/`) — research essays and narrative pages

Everything else — candidates, site output, enhanced images — is generated from these three inputs and is gitignored. Any project can be rebuilt from scratch by running `markery match`, reviewing, and `markery site build`.

Projects do not share confirmed pairs, entities, or content. The same entity (e.g. Remington Rand) can appear in multiple projects with independent confirmation decisions in each.

---

## Agentic Design Intent

The specialist pattern is designed to be forward-compatible with an AI agent layer. Each specialist's queries module is a clean programmatic API: pure functions, typed inputs and outputs, no CLI dependency. A model calling `get_entities()` or `get_confirmed_matches()` gets the same result as the site builder — without going through the CLI.

The historian specialist makes this explicit: `specialist/historian/persona/` contains the Claude persona configuration that turns a model into a research collaborator. The Python code in `specialist/historian/` (the interactive reviewer) and the persona files serve the same function through different interfaces — human terminal and Claude project respectively.

The long-term design intent is that each specialist can be called by a hosted or local model without modification: the queries API is the model's tool interface, the CLI is the human interface, and the two are kept deliberately separate.
