# Setup Guide

Complete instructions for setting up Markery from scratch on a new machine.

---

## Prerequisites

- **Python 3.11 or later** (`python --version`)
- **Git**
- Two API credentials (both free — see below)
- ~500 MB disk space for the databases and model weights

The three `.duckdb` files are committed to the repository. You do not need to rebuild them to start working — they already contain data. Rebuilding from scratch requires the EPO OPS credentials and, for trademarks, the raw USPTO CSV files (which are not committed).

---

## 1. Clone and create environment

```bash
git clone git@github.com:CosmoGSpacely/markery.git
cd markery

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## 2. API credentials

Create a `.env` file in the project root (it is gitignored):

```bash
touch .env
```

### EPO Open Patent Services

Used by `build_patents_db.py` and `test_epo_ops.py`.

1. Register at **https://developers.epo.org** — free, requires email verification
2. Create an application to get a Consumer Key and Consumer Secret
3. Add to `.env`:

```
EPO_CONSUMER_KEY=your_key_here
EPO_CONSUMER_SECRET=your_secret_here
```

Verify credentials:
```bash
.venv/bin/python test_epo_ops.py
```

Expected output: token obtained, a known patent retrieved, a CQL search returning results.

### USPTO TSDR API

Used by `tsdr_client.py` for fetching mark images and case status.

1. Register at **https://account.uspto.gov/api-manager/**
2. Create an API key
3. Add to `.env`:

```
USPTO_API_KEY=your_key_here
```

---

## 3. Verify the databases

The committed databases are ready to use. Confirm they're working:

```bash
.venv/bin/python -c "
import duckdb

p = duckdb.connect('patents.duckdb', read_only=True)
print('patents:', p.execute('SELECT COUNT(*) FROM patents').fetchone()[0])

t = duckdb.connect('trademarks.duckdb', read_only=True)
print('trademarks:', t.execute('SELECT COUNT(*) FROM case_file').fetchone()[0])

e = duckdb.connect('entities.duckdb', read_only=True)
print('entities:', e.execute('SELECT COUNT(*) FROM company_entity').fetchone()[0])
"
```

Expected: ~11,284 patents, ~25,473 trademarks, 4 entities.

---

## 4. Run the match pipeline

Generate patent-trademark candidate pairs for the information-systems project:

```bash
.venv/bin/python -m match information-systems
```

Output is written to `projects/information-systems/matches/candidates.jsonl`.

---

## Rebuilding from scratch

### entities.duckdb

Safe to rebuild at any time — idempotent:

```bash
rm entities.duckdb
.venv/bin/python build_entities_db.py
```

### patents.duckdb

Requires EPO OPS credentials. The full B42F + B42D fetch takes approximately 20–30 minutes and makes several hundred API calls.

```bash
rm patents.duckdb
.venv/bin/python build_patents_db.py --seed-only       # create schema, load 2 seed patents
.venv/bin/python build_patents_db.py --classes B42F B42D   # full fetch

# Or fetch a single year to test:
.venv/bin/python build_patents_db.py --classes B42F --year-start 1918 --year-end 1918
```

Use `--resume` to continue a partial build without re-fetching already-completed windows.

### trademarks.duckdb

Requires the USPTO Trademark Case Files Dataset CSV files in `csv/`. The CSVs are not committed (combined ~4 GB). Download from:

> https://www.uspto.gov/ip-policy/economic-research/research-datasets/trademark-case-files-dataset

Extract to `csv/`, then:

```bash
rm trademarks.duckdb
.venv/bin/python build_trademarks_db.py
```

The rebuild takes 2–5 minutes depending on disk speed. The resulting database is ~150 MB.

---

## Image enhancement

Mark image enhancement uses Real-ESRGAN. Model weights (~17 MB) are downloaded automatically on first use to `image_tools/weights/`.

Before running enhancement, review `image_tools/ENHANCE.md`. Enhancement is a selective, manually-confirmed step — not a batch operation on query results.

---

## Project layout summary

```
markery/
├── patents.duckdb              US patents 1900–1939 (B42F + B42D)
├── trademarks.duckdb           USPTO trademark applications 1900–1939
├── entities.duckdb             Canonical company registry
├── build_patents_db.py         Rebuild patents.duckdb from EPO OPS
├── build_trademarks_db.py      Rebuild trademarks.duckdb from CSV
├── build_entities_db.py        Rebuild entities.duckdb (idempotent)
├── match/                      Patent-trademark candidate pipeline
├── image_tools/                Mark image enhancement pipeline
├── projects/
│   └── information-systems/    Active research project
│       ├── entities.txt        Companies in scope
│       ├── matches/            candidates.jsonl + confirmed.jsonl
│       └── content/            Research essays per entry
└── .env                        API credentials (gitignored)
```
