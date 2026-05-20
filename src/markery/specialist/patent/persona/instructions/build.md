# Instruction Card: Patent Build

## When to use

When a project needs patent records for CPC classes or year ranges not yet in `patents.duckdb`. Check the fetch log before starting:

```bash
cat data/patents_fetch_log.json | python -c "
import json, sys
for e in json.load(sys.stdin):
    print(e['cpc_class'], e['year_start'], e['year_end'], e['patents_added'])
"
```

Or check `markery status` for current patent row counts.

## What this produces

New rows in `patents.duckdb` tables: `patents`, `patent_classes`, `patent_inventors`. Figures are not fetched during a build — use `markery patent figures <patent_no>` separately.

Each completed class/window is appended to `data/patents_fetch_log.json`.

## Commands

**Standard build:**
```bash
markery patent build --classes <CPC> [<CPC> ...] --year-start <YEAR> --year-end <YEAR>
```

**Resume after interruption:**
```bash
markery patent build --classes <CPC> [<CPC> ...] --year-start <YEAR> --year-end <YEAR> --resume
```

**Seed only (no API call):**
```bash
markery patent build --seed-only --seed-path projects/<project>/seed_patents.json
```

## Rate limit handling

EPO OPS enforces a daily query quota on the free tier. If the build fails with a 403 error, note which class and window were in progress, then resume the next day:

```bash
markery patent build --classes <remaining classes> --year-start <YEAR> --year-end <YEAR> --resume
```

The `--resume` flag reads `patents_fetch_log.json` and skips any windows already recorded there.

## After the build

Run `markery status` to confirm row counts. Then regenerate candidates:

```bash
markery match <project> --force
```
