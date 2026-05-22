# Instruction Card: Patent Fetch (Figures by Project)

## When to use

To bulk-fetch figures for all patents in a project — either all confirmed pairs or all candidates above a score threshold. For a single known patent number use `markery patent figures <patent_no>` instead.

Check what is already stored before running:
```bash
markery status
```

## What this produces

Figure blobs stored in `patent_figures` table in `patents.duckdb`. Each figure is stored once; subsequent calls skip already-stored patents unless `--force` is added.

## Commands

**Fetch figures for all confirmed pairs in a project:**
```bash
markery patent fetch <project> --confirmed
```

**Fetch figures for all candidates above a score threshold:**
```bash
markery patent fetch <project> --min-score 0.6
```

**Fetch a specific list of patents:**
```bash
markery patent fetch <project> --patent US1261167A US1435663A
```

## Rate limit handling

The EPO OPS API enforces a daily quota. If the fetch fails with a 403 error mid-run, note which patents were remaining and re-run the next day with an explicit `--patent` list of the remaining ones.

## After fetching

Figures become available to `markery historian card` and the publisher's HTML output automatically — no additional steps required.
