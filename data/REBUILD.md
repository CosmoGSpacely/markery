# Rebuilding the corpus (data/)

As of Phase 28 P3 (2026-06-24) the corpus DBs and record-image assets are
**rebuildable artifacts**, not committed to git:

- `data/trademarks.duckdb`, `data/patents.duckdb`, `data/entities.duckdb` — gitignored
- `data/assets/` (externalized mark drawings + patent figures) — gitignored
- `data/patents_fetch_log.json` — **committed** (the patent coverage manifest)

Record images live as files under `data/assets/{marks,patents}/`, referenced by a
`file` + `sha256` column on `mark_images` / `patent_figures` (no more BLOBs). Any
pre-Phase-28 DB self-migrates (externalizes its BLOBs, adds provenance columns) on
the next **writable** open.

## Fastest: restore from the archived snapshot

A full copy of the DBs as of the externalization was archived outside the repo:

```
/home/wccogswell/markery-corpus-archive-2026-06-24/   # trademarks, patents, entities, fetch_log
```

That snapshot predates the blob→file migration (it still holds image BLOBs); just
copy the `.duckdb` files back into `data/` and open any specialist command once
(e.g. `markery trademark status`) — the writable open externalizes the images into
`data/assets/` automatically.

```
cp /home/wccogswell/markery-corpus-archive-2026-06-24/*.duckdb data/
markery trademark status   # triggers the externalization migration
markery patent coverage    # sanity check
```

## From source (no snapshot)

The source inputs are large and external (not in the repo):

1. **Trademarks** — USPTO bulk CSV (case_file + companion tables) in `csv/`:
   `markery trademark build [--date-start 1900-01-01 --date-end 1939-12-31]`.
   Mark images are fetched on demand: `markery trademark enrich <serial>` (TSDR).
2. **Patents** — EPO OPS (needs `.env` EPO credentials), driven by CPC class/year:
   `markery patent build …` (resume state in `patents_fetch_log.json`).
   Figures: `markery patent figures <patent_no>`.
3. **Entities** — auto-register from the corpus (Phase 28 P2):
   `markery matchmaker register "<Company>" --confirm` and
   `markery matchmaker register-people --confirm`; or `matchmaker build` from
   hand-written `entities.csv` / `variants.csv`.

## Verifying

`markery trademark coverage` and `markery patent coverage` print the local
manifest (record counts, ranges, live/dead, provenance, fetch windows).
