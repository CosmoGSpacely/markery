# Research Session Workflow

Single runnable checklist for a Markery research session. Every command assumes you are at the project root with the virtual environment active.

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
markery status
```

Expected output: row counts for all three databases, project metrics (candidates, confirmed, essays), deferred items list, and next action from `CONTEXT.md`. Any `MISSING` database line is a blocker — rebuild the affected database before proceeding.

---

## 1. Add a new entity (skip if not needed)

Entity data lives in `src/markery/specialist/matchmaker/build.py`. To add a company:

1. Add a row to the `ENTITIES` list — fields: `(entity_id, canonical_name, entity_type, industry, notes)`.
2. Add name variants to the `VARIANTS` list — one row per known spelling from patent assignee fields and trademark owner fields.
3. Run the builder:

```bash
markery matchmaker build
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
markery match <project>
```

Options:

```bash
markery match <project> --entity "Wilson Jones"   # restrict to one entity
markery match --list-entities                               # show registered entities
markery match --all                                         # all entities
```

After the run, check the output count:

```bash
python - <<'EOF'
from pathlib import Path
p = Path("projects/<project>/matches/candidates.jsonl")
print(sum(1 for l in p.read_text().splitlines() if l.strip()), "candidates")
EOF
```

`candidates.jsonl` is overwritten on every run. Never edit it — all curation goes into `confirmed.jsonl`.

---

## 3. Score text signals (optional — recommended before reviewing)

Enriches `candidates.jsonl` with four text-signal fields: `title_name_hit`, `abstract_name_hit`, `goods_title_overlap`, `goods_abstract_overlap`. These are displayed in the reviewer and used to surface the strongest matches.

```bash
markery score-signals <project>
```

Run this after generating candidates and before reviewing. Safe to re-run — it overwrites only the signal fields.

---

## 4. Review candidates

```bash
markery review <project>
```

Options:

```bash
markery review <project> --min-score 0.65    # tighter threshold (default 0.5)
markery review <project> --mark <mark>       # single trademark
```

The reviewer presents each candidate pair sorted by score descending. For each pair:

- Already-confirmed pairs are skipped automatically.
- The display shows: mark, serial, filing date, first use, owner, draw code, goods/services description, patent number, grant date, application date, assignee, inventors, title, CPC classes, date gap, text signals, and overall score.
- If a patent figure exists in `data/patents.duckdb`, it opens automatically via `xdg-open`.

Keys: **Y** = confirm  **N** = skip  **Q** = quit

On **Y**, the reviewer prompts for an optional note, then appends to `confirmed.jsonl` and prints `✓ Written to confirmed.jsonl`.

---

## 5. Confirm a pair manually (if not using the interactive reviewer)

Append directly to `projects/<project>/matches/confirmed.jsonl`:

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

Open a Claude project and add the `src/markery/specialist/historian/persona/` folder plus the three DuckDB files (`data/trademarks.duckdb`, `data/patents.duckdb`, `data/entities.duckdb`).

Prompt pattern:

```
Walk me through the confirmed pair: [MARK] (serial [SN]) ↔ [PATENT].
Draft a research essay for projects/<project>/content/[slug].md.
```

Save the completed essay to `projects/<project>/content/<slug>.md`. Filename matches the mark's common name in lowercase (e.g., `mark-name.md`).

Essay structure: lead with historical context, ground all claims in specific filing records (serial numbers, patent numbers, dates), distinguish what the record shows from what it implies. See existing essays in the project's `content/` for examples.

---

## 7. Fetch patent documents

Download PDF and extract page-1 figure for confirmed pairs:

```bash
markery fetch-patents <project> --confirmed
```

For a specific patent:

```bash
markery fetch-patents --patent US1261167A
```

For high-scoring candidates before review:

```bash
markery fetch-patents <project> --min-score 0.70
```

PDFs land in `projects/<project>/output/` alongside the existing figure PNGs. Figures extracted into `data/patents.duckdb` (`patent_figures` table) and displayed automatically in the reviewer.

---

## 8. Build a gallery

**From DB images (no enhancement needed):** reads raw TSDR images from `mark_images` table.

```bash
markery enhance gallery \
  --where "cf.mark_draw_cd LIKE '3%' AND cf.filing_dt BETWEEN DATE '1930-06-01' AND DATE '1930-06-30'" \
  --out projects/monthly-image-review/output/june1930/gallery.html \
  --title "Design Marks, June 1930" --subtitle "7 marks"
```

**From enhanced PNGs:** after running enhance on selected marks.

```bash
markery enhance gallery projects/<project>/output/<collection> \
  --title "<collection title>"
```

Output is self-contained HTML with base64-embedded images. Not for web publication.

---

## 9. Enhance specific marks (selective — after reviewing the gallery)

Enhancement is manual and compute-intensive. Run only on marks chosen after human review; always confirm serial numbers before proceeding.

Single mark:

```bash
markery enhance enhance <serial_no> --out-dir projects/<project>/output/<collection>
```

Confirmed batch:

```bash
markery enhance batch "cf.serial_no IN ('<sn1>','<sn2>','<sn3>')" \
  --out-dir projects/<project>/output/<collection>
```

Output: 4× upscaled PNG. SVG written alongside for clean word marks and geometric designs. `--force` re-processes existing output.

---

## End of session

Update `CONTEXT.md` → `## Next Action` with the specific next step (mark + serial or task).

Run `markery status` one more time to confirm metrics match expectations before closing.

---

## Quick reference

| Task | Command |
|---|---|
| Session verifier | `markery status` |
| Add entity | edit `src/markery/specialist/matchmaker/build.py` → `markery matchmaker build` |
| Generate candidates | `markery match <project>` |
| Score text signals | `markery score-signals <project>` |
| Review candidates | `markery review <project>` |
| Fetch patent docs | `markery fetch-patents <project> --confirmed` |
| Gallery from DB images | `markery enhance gallery --where "..." --out <path>` |
| Gallery from enhanced PNGs | `markery enhance gallery <dir>` |
| Enhance mark (manual, selective) | `markery enhance enhance <serial> --out-dir <dir>` |
| Historian session | Claude project + `src/markery/specialist/historian/persona/` + 3 DuckDB files |
