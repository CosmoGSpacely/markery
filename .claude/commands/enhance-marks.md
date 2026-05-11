Enhance trademark mark images for a set of serial numbers, then write an HTML gallery to the output folder.

## Steps

1. Determine the output collection name from the request (e.g. `enhanced_may1930_designs`). Output goes to `output/<collection>/`.

2. If the user gave a date range, company, or search term rather than serial numbers directly, query `trademarks.duckdb` first to get the serial numbers:

```bash
.venv/bin/python - << 'EOF'
import duckdb
conn = duckdb.connect("trademarks.duckdb")
rows = conn.execute("""
    SELECT serial_no::VARCHAR, mark_id_char, filing_dt
    FROM case_file
    WHERE <your WHERE clause here>
    ORDER BY serial_no
""").fetchall()
for r in rows:
    print(r)
EOF
```

3. Run the batch enhancer. The `where` argument is a SQL WHERE clause against `case_file` (aliased `cf`):

```bash
.venv/bin/python -m image_tools batch \
  "cf.serial_no IN ('71300354','71301023')" \
  --out-dir output/<collection>
```

Or for a date/type query:

```bash
.venv/bin/python -m image_tools batch \
  "cf.filing_dt BETWEEN DATE '1930-05-01' AND DATE '1930-05-31' AND cf.mark_draw_cd LIKE '3%'" \
  --out-dir output/enhanced_may1930_designs
```

4. Build the gallery:

```bash
.venv/bin/python -m image_tools gallery output/<collection> \
  --title "<descriptive title>" \
  --subtitle "<count> marks • <source description>"
```

5. Report what was produced: how many marks enhanced, how many got SVG output, where the gallery lives, and note any failures.

## Notes

- Model weights (~17 MB for x4plus-anime) are downloaded automatically on first use to `image_tools/weights/`.
- SVG output is written alongside the PNG when the mark is clean enough to vectorize (word marks, geometric designs). Illustration marks (figures, animals, landscapes) get PNG only. The gallery notes `[SVG]` next to the mark name when a vector version exists.
- Use `--force` to re-process marks that already have output files.
- The gallery is self-contained HTML with base64-embedded images — open it directly in a browser or share as a single file.
