# enhance-marks — Image Enhancement Workflow

Enhance trademark mark images for a selected set of serial numbers, then write an HTML gallery to the output folder.

**This workflow is for use after human review and selection.** Do not run batch enhancement automatically on query results. The enhancement pipeline is compute-intensive and the output is meant to reflect a deliberate curatorial choice — marks that were reviewed, found interesting, and selected for closer study. Always confirm the list of serial numbers with the user before running.

---

## Steps

### 1. Identify the project and collection

Output goes to `projects/<project>/output/<collection>/`. Current projects: `information-systems`, `monthly-image-review`.

### 2. Confirm the serial numbers with the user

If the user described marks by date range, company, or search term rather than serial numbers directly, query the database to surface candidates — then **show the results and ask the user which ones to enhance** before running anything.

```bash
.venv/bin/python - << 'EOF'
import duckdb
conn = duckdb.connect("trademarks.duckdb")
rows = conn.execute("""
    SELECT serial_no::VARCHAR, mark_id_char, filing_dt, mark_draw_cd
    FROM case_file
    WHERE <your WHERE clause here>
    ORDER BY serial_no
""").fetchall()
for r in rows:
    print(r)
EOF
```

Do not proceed to enhancement until the user has reviewed the list and confirmed which serial numbers to include.

### 3. Run the enhancer on the confirmed selection

Pass the confirmed serial numbers as a SQL WHERE clause:

```bash
.venv/bin/python -m image_tools batch \
  "cf.serial_no IN ('71300354','71301023')" \
  --out-dir projects/<project>/output/<collection>
```

Or for a date/type query scoped to a pre-confirmed set:

```bash
.venv/bin/python -m image_tools batch \
  "cf.filing_dt BETWEEN DATE '1930-05-01' AND DATE '1930-05-31' AND cf.mark_draw_cd LIKE '3%'" \
  --out-dir projects/monthly-image-review/output/enhanced-may1930-designs
```

### 4. Build the gallery

```bash
.venv/bin/python -m image_tools gallery projects/<project>/output/<collection> \
  --title "<descriptive title>" \
  --subtitle "<count> marks • <source description>"
```

### 5. Report results

How many marks were enhanced, how many have SVG output, where the gallery file lives, and any failures.

---

## Notes

- Model weights (~17 MB for `x4plus-anime`) are downloaded automatically on first use to `image_tools/weights/`.
- SVG output is written alongside the PNG when the mark is clean enough to vectorize (word marks, geometric designs). Illustration marks — figures, animals, landscapes — get PNG only. The gallery labels SVG-capable marks with `[SVG]`.
- Use `--force` to re-process marks that already have output files.
- The gallery is self-contained HTML with base64-embedded images — open directly in a browser or share as a single file.
