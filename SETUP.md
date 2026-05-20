# Setup Guide

Complete instructions for setting up Markery on a new machine.

---

## Prerequisites

- **Python 3.11 or later** (`python --version`)
- **Git**
- API credentials for the data sources you plan to use (see below)
- ~50 MB disk space for the committed databases; ~4 GB additional if rebuilding the trademark bulk tables from the USPTO CSV download

The three `.duckdb` files are committed to the repository and ready to use. You do not need to rebuild them to start working. Rebuilding from scratch requires the relevant credentials and, for the trademark bulk route, the raw USPTO CSV files (not committed).

---

## 1. Clone and create environment

```bash
git clone <repository-url>
cd markery

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

All `markery` commands below assume the venv is active.

---

## 2. API credentials

Create a `.env` file in the project root (gitignored):

```bash
touch .env
```

### EPO Open Patent Services

Required for fetching patent records from the EPO OPS API.

1. Register at **https://developers.epo.org** — free, requires email verification
2. Create an application to receive a Consumer Key and Consumer Secret
3. Add to `.env`:

```
EPO_CONSUMER_KEY=your_key_here
EPO_CONSUMER_SECRET=your_secret_here
```

Verify:
```bash
markery patent verify-credentials
```

### USPTO TSDR API

Required for fetching individual trademark records and mark images.

1. Register at **https://account.uspto.gov/api-manager/**
2. Create an API key
3. Add to `.env`:

```
USPTO_API_KEY=your_key_here
```

Verify:
```bash
markery trademark verify-credentials
```

---

## 3. Verify the committed databases

```bash
markery status
```

This prints row counts for all three databases and a one-line summary for each project. Use it any time to confirm the databases are intact and the venv is correctly set up.

---

## 4. Set up the entity registry

Entities are defined per project in `projects/<project>/entities.csv` and `projects/<project>/variants.csv`. Load them into `entities.duckdb`:

```bash
markery matchmaker build --data-dir projects/<project>
```

The build is idempotent — re-running adds any new rows and skips existing ones. Confirm:

```bash
markery matchmaker list
```

---

## 5. Build the trademark database

Two routes depending on what you have available.

### Route A: Bulk CSV (full USPTO dataset)

The 2011 USPTO Trademark Case Files Dataset provides ~5 million case files with companion tables (owner, classification, statement, and others). This route populates the full bulk schema and is required for candidate generation via the matchmaker.

**When to use:** Starting a new project where you need to discover which marks belong to your entities across the full USPTO corpus, or when your project's date window falls within the 2011 bulk snapshot.

Download the dataset from:

> https://www.uspto.gov/ip-policy/economic-research/research-datasets/trademark-case-files-dataset

Extract to `csv/`, then:

```bash
markery trademark build --csv-dir csv/
```

Supply `--date-start` and `--date-end` to load only a date window:

```bash
markery trademark build --csv-dir csv/ --date-start 1900-01-01 --date-end 1939-12-31
```

The full dataset takes 2–5 minutes depending on disk speed. The filtered build is faster. Row counts in `case_file` will reflect the window you chose.

### Route B: TSDR API (targeted fetch)

Fetches specific marks by serial number from the USPTO TSDR API into `extended_marks`. Does not populate the bulk tables (`case_file`, `owner`, etc.).

**When to use:** You already know which marks you need; your marks are post-2011 and not in the bulk dataset; or you are building a project from confirmed pairs rather than from candidate discovery.

Fetch a specific mark:

```bash
markery trademark fetch <serial_no>
```

Enrich all marks in a project's confirmed or candidates file:

```bash
markery trademark enrich-project <project> --source confirmed
markery trademark enrich-project <project> --source candidates --min-score 0.50
```

With this route, `extended_marks` is the primary trademark table. Candidate generation via the matchmaker requires the bulk tables; if using Route B, candidates must be supplied by other means (manual curation, seed records).

---

## 6. Build the patent database

### Route A: EPO OPS API (current)

Fetches patent records by CPC class and year range from the EPO OPS API. This is the primary and currently supported fetch mechanism.

```bash
markery patent build --classes B42F B42D --year-start 1900 --year-end 1939
```

Use `--resume` to continue a fetch interrupted by rate limits or quota:

```bash
markery patent build --classes B42F B42D --year-start 1900 --year-end 1939 --resume
```

Resume state is tracked in `data/patents_fetch_log.json` alongside the database. Each completed class/window is recorded; `--resume` skips already-completed entries.

To add seed patents without triggering an API fetch (useful for patents identified by manual research):

```bash
markery patent build --seed-only --seed-path projects/<project>/seed_patents.json
```

Fetch a single patent by number on demand:

```bash
markery patent pull <patent_no>
```

### Route B: Bulk CSV import (planned, not yet implemented)

A future route will support bulk import from sources such as PatentsView or Google Patents Public Data, allowing `patents.duckdb` to be populated without EPO OPS API calls. This is useful for large class sweeps, offline environments, or projects covering CPC classes that EPO OPS rate limits make impractical to fetch incrementally. Implementation is pending.

---

## 7. Run the match pipeline

Generate patent-trademark candidate pairs for a project:

```bash
markery match <project>
```

This reads the project's `entities.txt` (the entity IDs in scope), queries all three databases via DuckDB ATTACH, scores every patent-trademark pair, and writes `projects/<project>/matches/candidates.jsonl`.

To also enrich with text signals in one step:

```bash
markery match <project> --full
```

Check pipeline state at any time:

```bash
markery match status <project>
```

---

## 8. Review and publish

Interactive candidate review:

```bash
markery review <project>
```

Keys: `Y` confirm · `N` skip · `Q` quit. Confirmed pairs are written to `confirmed.jsonl`.

Build the static site:

```bash
markery site build <project>
```

---

## Image enhancement

Mark image enhancement uses Real-ESRGAN. Model weights (~17 MB) are downloaded automatically on first use to `src/markery/specialist/publisher/image_enhancement/weights/`.

Enhancement is selective and manually confirmed — not a batch operation on all candidates. See `markery enhance --help` for options.

---

## Project layout

```
markery/
├── data/
│   ├── patents.duckdb              Shared patent corpus (EPO OPS)
│   ├── patents_fetch_log.json      Resume state for patent builds
│   ├── trademarks.duckdb           Shared trademark corpus (USPTO)
│   └── entities.duckdb             Canonical entity registry
├── src/markery/
│   ├── specialist/
│   │   ├── patent/                 Patent specialist + EPO.md
│   │   ├── trademark/              Trademark specialist + TSDR.md
│   │   ├── matchmaker/             Entity registry + candidate generation
│   │   ├── historian/              Review tool + persona/
│   │   └── publisher/              Site renderer + image enhancement
│   ├── common/                     Config, auth, shared utilities
│   └── cli.py                      Unified entry point
├── projects/
│   └── <project>/
│       ├── entities.csv            Entity definitions (loaded into entities.duckdb)
│       ├── variants.csv            Name variant definitions
│       ├── seed_patents.json       Manually-identified seed patent records
│       ├── entities.txt            Entity IDs in scope for this project
│       ├── matches/
│       │   ├── candidates.jsonl    Generated — never edited
│       │   └── confirmed.jsonl     Hand-curated — authoritative
│       └── content/                Research essays and narrative pages
└── .env                            API credentials (gitignored)
```
