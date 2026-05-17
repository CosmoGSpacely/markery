# Research Session Workflow

Single runnable checklist for a Markery research session. Every command assumes you are at the project root with the virtual environment active.

This document will move to `docs/workflows/research-session.md` during the Phase 2 reorganization.

---

## 0. Environment check

```bash
source .venv/bin/activate
python --version          # expect 3.11+
```

Verify `.env` is present and has all three keys:

```bash
grep -c '=' .env          # expect 3
```

Required keys: `EPO_CONSUMER_KEY`, `EPO_CONSUMER_SECRET`, `USPTO_API_KEY`.

Verify DuckDB files are present:

```bash
ls -lh data/trademarks.duckdb data/patents.duckdb data/entities.duckdb
```

Run the session-start verifier:

```bash
scripts/check-status
```

Expected output: row counts for all three databases, project metrics (candidates, confirmed, essays), deferred items list, and next action from `CONTEXT.md`. Any `MISSING` database line is a blocker — rebuild the affected database before proceeding.

---

## 1. Add a new entity (skip if not needed)

Entity data lives in `src/markery/db/build_entities_db.py`. To add a company:

1. Add a row to the `ENTITIES` list — fields: `(entity_id, canonical_name, entity_type, industry, notes)`.
2. Add name variants to the `VARIANTS` list — one row per known spelling from patent assignee fields and trademark owner fields.
3. Run the builder:

```bash
python src/markery/db/build_entities_db.py
```

Expected output: counts of entities and variants added. The builder is idempotent — running it again with no changes prints `0 entities added  0 variants added`.

Confirm the entity landed:

```bash
python - <<'EOF'
import duckdb
conn = duckdb.connect("data/entities.duckdb", read_only=True)
print(conn.execute("SELECT entity_id, canonical_name FROM company_entity ORDER BY entity_id").fetchall())
EOF
```

---

## 2. Generate candidates

```bash
scripts/run-match information-systems
```

Options:

```bash
scripts/run-match information-systems --entity "Wilson Jones"   # restrict to one entity
scripts/run-match --list-entities                               # show registered entities
scripts/run-match --all                                         # all entities
```

After the run, check the output count:

```bash
python - <<'EOF'
from pathlib import Path
p = Path("projects/information-systems/matches/candidates.jsonl")
print(sum(1 for l in p.read_text().splitlines() if l.strip()), "candidates")
EOF
```

`candidates.jsonl` is overwritten on every run. Never edit it — all curation goes into `confirmed.jsonl`.

---

## 3. Score text signals (optional — recommended before reviewing)

Enriches `candidates.jsonl` with four text-signal fields: `title_name_hit`, `abstract_name_hit`, `goods_title_overlap`, `goods_abstract_overlap`. These are displayed in the reviewer and used to surface the strongest matches.

```bash
scripts/score-text-signals information-systems
```

Run this after generating candidates and before reviewing. Safe to re-run — it overwrites only the signal fields.

---

## 4. Review candidates

```bash
scripts/review information-systems
```

Options:

```bash
scripts/review information-systems --min-score 0.65    # tighter threshold (default 0.5)
scripts/review information-systems --mark VI-DEX       # single trademark
```

The reviewer presents each candidate pair sorted by score descending. For each pair:

- Already-confirmed pairs are skipped automatically.
- The display shows: mark, serial, filing date, first use, owner, draw code, goods/services description, patent number, grant date, application date, assignee, inventors, title, CPC classes, date gap, text signals, and overall score.
- If a patent figure exists in `patents.duckdb`, it opens automatically via `xdg-open`.

Keys: **Y** = confirm  **N** = skip  **Q** = quit

On **Y**, the reviewer prompts for an optional note, then appends to `confirmed.jsonl` and prints `✓ Written to confirmed.jsonl`.

---

## 5. Confirm a pair manually (if not using the interactive reviewer)

Append directly to `projects/information-systems/matches/confirmed.jsonl`:

```json
{
  "patent_no": "US1261167A",
  "trademark_serial": "71246709",
  "trademark": "SOUNDEX",
  "entity_id": 1,
  "entity": "Remington Rand",
  "type": "product",
  "note": "Russell 1918 phonetic coding patent; mark filed 1927 by Rand Kardex Bureau predecessor."
}
```

Fields: `patent_no`, `trademark_serial`, `trademark`, `entity_id`, `entity`, `type` (`"product"` for product-name marks), `note`.

---

## 6. Write an essay

Open a Claude project and add the `tools/historian/` folder plus the three DuckDB files (`trademarks.duckdb`, `patents.duckdb`, `entities.duckdb`).

Prompt pattern:

```
Walk me through the confirmed pair: [MARK] (serial [SN]) ↔ [PATENT].
Draft a research essay for projects/information-systems/content/[slug].md.
```

Save the completed essay to `projects/information-systems/content/<slug>.md`. Filename matches the mark's common name in lowercase (e.g., `soundex.md`, `kardex.md`, `vi-dex.md`).

Essay structure: lead with historical context, ground all claims in specific filing records (serial numbers, patent numbers, dates), distinguish what the record shows from what it implies. See `soundex.md` and `kardex.md` for existing examples.

---

## 7. Fetch patent documents

Download PDF and extract page-1 figure for confirmed pairs:

```bash
scripts/fetch-patent-docs information-systems --confirmed
```

For a specific patent:

```bash
scripts/fetch-patent-docs --patent US1261167A
```

For high-scoring candidates before review:

```bash
scripts/fetch-patent-docs information-systems --min-score 0.70
```

PDFs land in `projects/information-systems/output/` alongside the existing figure PNGs. Figures extracted into `patents.duckdb` (`patent_figures` table) and displayed automatically in the reviewer.

---

## 8. Enhance mark image

For a single serial:

```bash
scripts/enhance enhance <serial_no> --out-dir projects/information-systems/output/<collection>
```

Example:

```bash
scripts/enhance enhance 71235764 --out-dir projects/information-systems/output/vi-dex
```

For a curated batch (confirm serial list with user first):

```bash
scripts/enhance batch "cf.serial_no IN ('71235764','71237470','71237469')" \
  --out-dir projects/information-systems/output/wilson-jones-marks
```

Output: 4× upscaled PNG (~3200px). SVG is written alongside when the mark is clean enough to vectorize (word marks, simple geometry). `--force` re-processes existing output.

---

## 9. Build gallery

```bash
python -m image_enhancement gallery projects/information-systems/output/<collection> \
  --title "Wilson Jones Filing Products, 1927" \
  --subtitle "3 marks · B42F"
```

Output: `gallery.html` in the collection directory. Self-contained (base64-embedded images) — open in a browser or share as a single file. Not for web publication; see Phase 4 for the publication pipeline.

---

## End of session

Update `CONTEXT.md` → `## Next Action` with the specific next step (mark + serial or task).

Run `scripts/check-status` one more time to confirm metrics match expectations before closing.

---

## Quick reference

| Task | Command |
|---|---|
| Session verifier | `scripts/check-status` |
| Add entity | edit `build_entities_db.py` → `python build_entities_db.py` |
| Generate candidates | `scripts/run-match information-systems` |
| Score text signals | `scripts/score-text-signals information-systems` |
| Review candidates | `scripts/review information-systems` |
| Fetch patent docs | `scripts/fetch-patent-docs information-systems --confirmed` |
| Enhance mark image | `scripts/enhance enhance <serial> --out-dir <dir>` |
| Build gallery | `python -m image_enhancement gallery <dir> --title "<title>"` |
| Historian session | Claude project + `tools/historian/` + 3 DuckDB files |
