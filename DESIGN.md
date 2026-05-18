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
