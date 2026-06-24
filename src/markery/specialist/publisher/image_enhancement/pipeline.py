"""Classify mark type, fetch source image, upscale, optionally vectorize, write outputs."""

from __future__ import annotations

import io
from pathlib import Path
from typing import NamedTuple

import duckdb
from PIL import Image

from . import binarize, upscale as _upscale

# Design-search code prefixes that indicate illustration content heavy enough
# to make SVG vectorization impractical.
_ILLUSTRATION_PREFIXES = {
    "02",  # human figures
    "03",  # animals
    "04",  # birds
    "05",  # plants, flowers
    "06",  # landscapes, scenery
}


class MarkResult(NamedTuple):
    serial_no: str
    png_path: Path
    svg_path: Path | None
    model_used: str
    svg_clean: bool


def _classify(draw_cd: str, design_codes: list[str]) -> dict:
    """
    Return processing hints for a mark.

    All marks in this 1900–1939 dataset are pen-and-ink or letterpress —
    x4plus-anime is the right default across the board. SVG is attempted
    only when the mark lacks illustration-heavy design codes.
    """
    prefixes = {c[:2] for c in design_codes}
    has_illustration = bool(prefixes & _ILLUSTRATION_PREFIXES)
    is_word_mark = draw_cd[:1] in {"1", "2"}
    return {
        "model": "x4plus-anime",
        "attempt_svg": is_word_mark or not has_illustration,
    }


def _fetch_from_db(serial_no: str, db_path: str) -> Image.Image | None:
    from markery.common.assets import read_mark_image
    conn = duckdb.connect(db_path, read_only=True)
    data = read_mark_image(conn, serial_no)
    conn.close()
    return Image.open(io.BytesIO(data)) if data else None


def _fetch_mark_meta(serial_no: str, db_path: str) -> tuple[str, list[str]]:
    """Return (draw_cd, design_codes) for a serial number from the DB."""
    conn = duckdb.connect(db_path, read_only=True)
    cf = conn.execute(
        "SELECT mark_draw_cd FROM case_file WHERE serial_no = ?", [serial_no]
    ).fetchone()
    ds = conn.execute(
        "SELECT design_search_cd FROM design_search WHERE serial_no = ? ORDER BY design_search_cd",
        [serial_no],
    ).fetchall()
    conn.close()
    draw_cd = (cf[0] or "3000") if cf else "3000"
    return draw_cd, [r[0] for r in ds]


def process_mark(
    serial_no: str,
    *,
    img: Image.Image | None = None,
    input_path: Path | None = None,
    out_dir: Path,
    db_path: str = "data/trademarks.duckdb",
    design_codes: list[str] | None = None,
    draw_cd: str = "3000",
    force: bool = False,
) -> MarkResult:
    """
    Enhance one mark and write PNG (and SVG if clean) to out_dir.

    Image source priority: img kwarg > input_path file > mark_images DB table.
    Set force=True to re-process even when output files already exist.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"{serial_no}.png"
    svg_candidate = out_dir / f"{serial_no}.svg"

    if png_path.exists() and not force:
        svg_path = svg_candidate if svg_candidate.exists() else None
        return MarkResult(serial_no, png_path, svg_path, "cached", svg_path is not None)

    if design_codes is None or draw_cd == "3000":
        db_draw_cd, db_design_codes = _fetch_mark_meta(serial_no, db_path)
        if draw_cd == "3000":
            draw_cd = db_draw_cd
        if design_codes is None:
            design_codes = db_design_codes

    hints = _classify(draw_cd, design_codes)

    if img is None:
        if input_path and Path(input_path).exists():
            img = Image.open(input_path)
        else:
            img = _fetch_from_db(serial_no, db_path)
    if img is None:
        raise FileNotFoundError(f"No image found for serial {serial_no}")

    enhanced, actual_model = _upscale.upscale(img, model_name=hints["model"])
    enhanced.save(png_path, format="PNG", optimize=False)

    svg_path = None
    if hints["attempt_svg"]:
        binary = binarize.threshold(enhanced)
        svg_str = binarize.vectorize(binary)
        if svg_str:
            svg_candidate.write_text(svg_str, encoding="utf-8")
            svg_path = svg_candidate

    return MarkResult(serial_no, png_path, svg_path, actual_model, svg_path is not None)
