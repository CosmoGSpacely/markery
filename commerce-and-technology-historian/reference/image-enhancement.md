# Image Enhancement

## What it is

Raw mark images in this project are PNG scans fetched from the USPTO TSDR `rawImage` endpoint. For 1900–1939 marks these are digitized from paper files — typically 750–900 px wide, with visible scan grain, soft edges, and degraded fine linework.

The `image_tools` pipeline upscales these to ~3200 px (4×) using Real-ESRGAN, a neural network trained specifically on degraded real-world images. The output is print-ready at 300 DPI up to ~10 inches wide.

## Output files

For each processed mark, `image_tools` writes to an output collection directory (e.g. `output/enhanced_may1930_designs/`):

| File | Always? | Description |
|---|---|---|
| `<serial_no>.png` | Yes | 4× upscaled PNG, ~3200 px wide |
| `<serial_no>.svg` | When clean | Vector trace of binarized image; only written when path count is below the complexity threshold |
| `gallery.html` | After `gallery` command | Self-contained HTML gallery with embedded images, metadata, and goods/services text |

## When SVG is and isn't produced

SVG output is attempted for marks without illustration-heavy design codes (human figures, animals, plants, landscapes — design-search prefixes 02–06). Marks with those codes get PNG only; the halftone-style linework in historical illustrations does not vectorize cleanly.

When SVG is produced, it is the preferred format for web display and print — it scales to any size with no quality loss. The gallery marks these cards `[SVG]`.

## Model selection

All marks in this 1900–1939 dataset are pen-and-ink or letterpress, so the `x4plus-anime` model is used across the board. This model was trained on line-art and outperforms the general `x4plus` model on the crisp edges and fine strokes typical of period trademark drawings.

## Requesting enhanced images

Use the `/enhance-marks` skill to process a set of marks and produce a gallery. You can specify marks by serial number, date range, company name, or any SQL WHERE clause against `case_file`.

Example invocations:

- *"Enhance all design marks filed in May 1930 and build a gallery"*
- *"Get me enhanced images for serial numbers 71300354 and 71301023"*
- *"Enhance every mark owned by Land O'Lakes in the database"*

## Interpreting enhanced images in analysis

When writing about a mark whose enhanced image is available, you may describe what the image shows with more confidence than from a degraded scan. Note the image source and enhancement when it matters to the evidentiary claim:

> The enhanced image (Real-ESRGAN 4×, `x4plus-anime`) makes clear that the figure in the Land O'Lakes mark (serial 71300354, filed May 12, 1930) is depicted kneeling at the water's edge, holding a butter package — a detail that reads as ambiguous in the raw TSDR scan.

Do not claim that enhancement recovers information that was not in the original. Enhancement sharpens what is there; it does not reconstruct lost content.

## Raw vs enhanced image sources

| Source | Location | Notes |
|---|---|---|
| Raw TSDR scan | `mark_images` table (BLOB) or `output/*/` PNG | Fetched via `tsdr_client.get_trademark_image()` |
| Enhanced PNG | `output/enhanced_*/` | 4× upscaled, ~3200 px |
| Enhanced SVG | `output/enhanced_*/` | Only for clean vectorizable marks |
