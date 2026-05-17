# Image Enhancement Workflow

**Enhancement is a manual, selective step.** Run it only on specific marks chosen after human review. The pipeline is compute-intensive and its output represents a deliberate curatorial choice — marks found interesting and selected for closer study.

---

## Gallery vs. enhancement

These are two independent operations:

| Operation | Command | When to use |
|---|---|---|
| Build gallery from DB | `markery enhance gallery --where "..." --out <path>` | Browsing a query result; no enhancement needed |
| Enhance specific marks | `markery enhance enhance <serial> --out-dir <dir>` | After selecting marks of interest |
| Build gallery from enhanced PNGs | `markery enhance gallery <dir>` | After enhancement, for the final enhanced gallery |

Build the DB gallery first to browse. Enhance only the marks worth it.

---

## Build a gallery from DB images (no enhancement)

Reads raw TSDR images directly from `mark_images` table. Fast; no compute.

```bash
markery enhance gallery \
  --where "cf.mark_draw_cd LIKE '3%' AND cf.filing_dt BETWEEN DATE '1930-06-01' AND DATE '1930-06-30'" \
  --out projects/monthly-image-review/output/june1930/gallery.html \
  --title "Design Marks, June 1930" \
  --subtitle "7 marks"
```

Images must already be in `mark_images` (fetched from TSDR). Check first:

```bash
python - <<'EOF'
import duckdb
conn = duckdb.connect("data/trademarks.duckdb", read_only=True)
print(conn.execute("SELECT COUNT(*) FROM mark_images").fetchone()[0], "images in DB")
EOF
```

---

## Enhance specific marks (selective, manual)

After browsing the gallery, if specific marks warrant enhancement:

### 1. Confirm serial numbers with the user

Surface the candidates, then ask which ones to enhance before running anything.

```bash
python - <<'EOF'
import duckdb
conn = duckdb.connect("data/trademarks.duckdb", read_only=True)
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

Do not proceed until the user has reviewed the list and confirmed which serial numbers to enhance.

### 2. Enhance the confirmed selection

Single mark:

```bash
markery enhance enhance 71302575 --out-dir projects/monthly-image-review/output/june1930-enhanced
```

Batch of confirmed serials:

```bash
markery enhance batch "cf.serial_no IN ('71302575','71302764')" \
  --out-dir projects/monthly-image-review/output/june1930-enhanced
```

### 3. Build enhanced gallery

```bash
markery enhance gallery projects/monthly-image-review/output/june1930-enhanced \
  --title "Design Marks, June 1930 — Enhanced" \
  --subtitle "2 marks selected"
```

---

## Notes

- Model weights (~17 MB for `x4plus-anime`) are downloaded automatically on first use to `tools/image_enhancement/weights/`.
- SVG output is written alongside PNG when the mark is clean enough to vectorize (word marks, geometric designs). Illustration marks get PNG only. Enhanced gallery labels SVG-capable marks with `[SVG]`.
- Use `--force` to re-process marks that already have output files.
- Galleries are self-contained HTML with base64-embedded images — open in a browser or share as a single file.
