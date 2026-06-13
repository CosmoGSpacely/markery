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

pip install -e "."
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

### Wikipedia API (optional)

Required only if you plan to submit Wikipedia drafts or external links. This is an optional workflow; skip this section if you are only using Markery for local research.

1. Create a Wikipedia account at **https://en.wikipedia.org**
2. Go to **Special:BotPasswords** (`https://en.wikipedia.org/wiki/Special:BotPasswords`)
3. Create a bot password with `Edit existing pages` permission
4. Add to `.env`:

```
WIKIPEDIA_USERNAME=YourUsername@BotName
WIKIPEDIA_PASSWORD=your_bot_password_here
```

Verify:
```bash
markery wikipedia verify-credentials
```

### OpenRouter (optional — model-agnosticism testing)

Markery is provider-agnostic: a model id containing `/` (e.g.
`meta-llama/llama-3.3-70b-instruct:free`) routes to OpenRouter instead of
Anthropic, letting you run specialists on a free or non-Anthropic model. Set a
project's model with `"model": "<slug>"` in its `project.json`, or pass a slug to
`markery model test`.

Key handling uses a **provisioning (management) key** to mint a runtime inference
key automatically:

1. Get a provisioning key at **https://openrouter.ai/settings/provisioning-keys**
2. Add to `.env`:

```
OPENROUTER_PROVISIONING_KEY=sk-or-v1-...
```

3. Mint a runtime key (cached to the gitignored `.openrouter-key`) and verify:

```bash
markery model status        # show key state and the default test model
markery model mint          # mint + cache a runtime key from the provisioning key
markery model test          # one live call (default: openai/gpt-oss-120b:free)
markery model test --model meta-llama/llama-3.3-70b-instruct:free
```

If you already hold a plain inference key (`sk-or-v1-…`), set `OPENROUTER_API_KEY`
instead and skip minting. Free models are rate-limited upstream; `chat()` retries
429/5xx with backoff, and a busy model returns a clear 429 — retry shortly or try
another free slug (`markery model test` lists the default).

---

## 3. Verify the committed databases

```bash
markery --version    # confirms install is working
markery status       # prints row counts for all three databases
```

`markery status` prints row counts for all three databases and a one-line summary for each project. Use it any time to confirm the databases are intact and the venv is correctly set up.

---

## 4. Start a new project (optional)

If you want to create a new research project rather than working with the committed `information-systems` project:

```bash
markery project init <your-project-name>
```

This scaffolds a project directory under `projects/<your-project-name>/` with the correct structure for a match-review-essay project (the default type). Then follow sections 5–8 to populate the databases and run the match pipeline for your project's scope.

If you want to work with the existing `information-systems` project, skip this step.

---

## 5. Set up the entity registry

Entities are defined per project in `projects/<project>/entities.csv` and `projects/<project>/variants.csv`. Load them into `entities.duckdb`:

```bash
markery matchmaker build --data-dir projects/<project>
```

The build is idempotent — re-running adds any new rows and skips existing ones. Confirm:

```bash
markery matchmaker list
```

---

## 6. Build the trademark database

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

## 7. Build the patent database

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

## 7b. Secondary literature (LIBRARIAN) — optional

The LIBRARIAN specialist acquires secondary literature from Internet Archive and Project Gutenberg, extracts relevant passages using Claude, and indexes them for semantic search. This is optional — research projects can run without it, but the library improves historian session quality by providing historical context.

**Dependencies:**

```bash
pip install -e ".[librarian]"
```

This installs `sentence-transformers` (for embedding generation) and `anthropic` (for Claude-assisted passage extraction). Both are optional — `markery librarian search` (keyword) and most librarian commands work without them; `markery librarian extract` and `markery librarian index --embed` require them.

**Acquire and index a work:**

```bash
markery librarian search-sources "topic keywords" --source ia
markery librarian acquire <ia-identifier>
markery librarian extract <slug> --topics "topic1" "topic2"
markery librarian index --embed
markery librarian card "<query>" --mode semantic
```

The shared library lives at `library/` in the repository root and is shared across all projects.

---

## 8. Run the match pipeline

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

## 9. Review and publish

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

The `markery enhance` command has three subcommands — `gallery`, `enhance`, and `batch` — with tiered optional dependencies. Install the tier you need:

**Tier 1 — base install (gallery only)**

No extra dependencies required. `markery enhance gallery` builds a self-contained HTML gallery from mark images stored in the database. The `enhance` and `batch` subcommands are not available at this tier.

```bash
pip install -e "."
markery enhance gallery --where "..." --title "..." --out gallery.html
```

**Tier 2 — enhance group (all subcommands, Lanczos upscaling)**

Installs `opencv-python-headless` and `vtracer`. All three subcommands work. `enhance` and `batch` upscale marks 4× using Pillow LANCZOS resampling and optionally vectorize to SVG. This is the recommended tier for research use — no GPU or large ML dependencies required.

```bash
pip install -e ".[enhance]"
markery enhance enhance <serial_no> --out-dir <dir>
markery enhance batch "<sql_where_clause>" --out-dir <dir>
```

`model_used` in the output will report `lanczos-fallback`.

**Tier 3 — full Real-ESRGAN (highest quality upscaling)**

Manually install `realesrgan` on top of Tier 2. This pulls in PyTorch, basicsr, and related packages (~1–2 GB). On first use, model weights (~64 MB) are downloaded automatically to `src/markery/specialist/publisher/image_enhancement/weights/`. When `realesrgan` is present, `enhance` and `batch` use it automatically; no configuration change needed.

```bash
pip install -e ".[enhance]"
pip install realesrgan
markery enhance enhance <serial_no> --out-dir <dir>
```

`model_used` will report `x4plus-anime`. Suitable for machines with a GPU or where quality is more important than install size. CPU inference works but is slow (~30–120 s per image).

---

## Project layout

```
markery/
├── data/
│   ├── patents.duckdb              Shared patent corpus (EPO OPS)
│   ├── patents_fetch_log.json      Resume state for patent builds
│   ├── trademarks.duckdb           Shared trademark corpus (USPTO)
│   └── entities.duckdb             Canonical entity registry
├── library/
│   ├── works/<slug>/               One directory per acquired work
│   │   ├── metadata.json           Bibliographic data and acquisition source
│   │   ├── raw_text.txt            Full plain text (downloaded)
│   │   └── excerpts.md             Curated passages (### heading per passage)
│   ├── index.jsonl                 Passage index (built by markery librarian index)
│   ├── index.duckdb                Embedding index for semantic search
│   └── wants.jsonl                 ILL queue
├── src/markery/
│   ├── specialist/
│   │   ├── patent/                 Patent specialist + EPO.md
│   │   ├── trademark/              Trademark specialist + TSDR.md
│   │   ├── matchmaker/             Entity registry + candidate generation
│   │   ├── historian/              Review tool + persona/
│   │   ├── publisher/              Site renderer + image enhancement
│   │   └── librarian/              Secondary literature acquisition + indexing
│   ├── common/                     Config, auth, shared utilities
│   └── cli.py                      Unified entry point
├── projects/
│   └── <project>/
│       ├── project.json            Project type and configuration (e.g. focus_serials)
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
