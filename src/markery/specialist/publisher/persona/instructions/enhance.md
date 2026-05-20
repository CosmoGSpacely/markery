# Instruction Card: Mark Image Enhancement

## When to use

When TSDR mark images are too small or low-resolution to display well in the rendered site. Raw TSDR images are often 150–300px wide and rendered at low quality. Enhancement runs Real-ESRGAN super-resolution to produce a higher-resolution version for galleries and essay pages.

Enhancement is optional — the site build displays raw TSDR images if enhanced versions are not present. Enhance when visual quality matters (public-facing gallery, Wikipedia article illustrations, print output).

---

## Commands

**Enhance a single mark by serial number:**
```bash
markery enhance enhance <serial_no> --out-dir projects/<project>/output/<slug>
```

The command reads the mark image from `trademarks.duckdb` (`mark_images` table), runs super-resolution, and writes the result to the output directory. The output filename is `<serial_no>.png`.

**Force re-enhancement if the file already exists:**
```bash
markery enhance enhance <serial_no> --out-dir projects/<project>/output/<slug> --force
```

**Enhance all marks matching a SQL condition (batch):**
```bash
markery enhance batch "cf.serial_no IN (71235764, 71246709)" --out-dir projects/<project>/output/batch
markery enhance batch "filing_dt BETWEEN DATE '1930-01-01' AND DATE '1930-12-31' AND mark_draw_cd LIKE '3%'" --out-dir output/design-marks-1930
```

The `WHERE` clause is applied to `case_file` (aliased `cf`). Only design marks (`mark_draw_cd LIKE '3%'`) have meaningful image data to enhance — word marks are stylized text and rarely benefit from super-resolution.

---

## Building an image gallery

After batch enhancement, build an HTML gallery from the enhanced PNGs:

```bash
# From enhanced PNG directory
markery enhance gallery projects/<project>/output/batch --title "Design Marks, 1930"

# From raw mark_images in trademarks.duckdb (no enhancement needed)
markery enhance gallery --where "filing_dt BETWEEN DATE '1930-01-01' AND DATE '1930-12-31'" --out output/gallery.html --title "Marks Filed 1930"
```

---

## How the site builder picks up enhanced images

During `markery site build`, the renderer checks for on-disk images in `projects/<project>/site/images/marks/` before falling back to the TSDR BLOB. Enhanced images must be in this directory to be used. The build writes images from `mark_images` (BLOB) automatically; it does not automatically pull enhanced images from the project output directory.

To use enhanced images in the site, copy or symlink the enhanced PNGs into `site/images/marks/` after building, then rebuild. Or use the `--out` flag to target that directory directly.

---

## Prerequisites

- Mark image must be in `trademarks.duckdb` (`mark_images` table). Run `markery trademark enrich <serial_no>` first if the image is missing.
- Model weights (~17 MB) are downloaded automatically on first use.
- Enhancement is CPU-intensive. A single mark takes a few seconds; batch jobs on dozens of marks may take several minutes.

---

## Human-readable request forms

```
"Enhance the mark image for serial number 71235764."

"Build an enhanced gallery of all design marks filed in 1930."

"The mark images in the site look too small. Can we enhance them?"
```
