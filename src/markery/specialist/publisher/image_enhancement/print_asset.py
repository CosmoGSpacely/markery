"""Print-ready image files for on-demand printing (Amazon Merch) — Phase 24 P5.

Builds a print-spec PNG from a public-domain corpus image (a design mark or a
patent figure) into ``projects/<name>/print/`` — a local export for uploading to
a print-on-demand service, **not** surfaced on the built site.

Eligibility is gated on two distinct rights:
  * copyright — PD by expiration (published before today − 95 years);
  * trademark — a design mark must be **dead/abandoned** (no live trademark
    rights, ``cfh_status_cd >= 700``); patent figures have no trademark issue.
"""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
from PIL import Image

from markery.common import config
from markery.common.project import Project
from . import upscale as _upscale

# Amazon Merch on Demand reference spec (other POD services are similar).
SPECS: dict[str, dict] = {
    "merch": {"w": 4500, "h": 5400, "dpi": 300, "max_bytes": 25 * 1024 * 1024,
              "margin": 0.06, "white_thresh": 240},
}


def pd_cutoff_year() -> int:
    """Works published in a year < this value are PD in the US (95-year term)."""
    return date.today().year - 95


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------

def _year(dt) -> int | None:
    if dt is None:
        return None
    return dt.year if hasattr(dt, "year") else int(str(dt)[:4])


def check_mark_eligible(serial_no: str) -> tuple[bool, str]:
    """A design mark is printable only if PD (filing < cutoff) AND dead/abandoned."""
    conn = duckdb.connect(str(config.DB["trademarks"]), read_only=True)
    row = conn.execute(
        "SELECT filing_dt, cfh_status_cd FROM case_file WHERE serial_no = ?",
        [serial_no],
    ).fetchone()
    conn.close()
    if row is None:
        return False, f"serial {serial_no} not found"
    filing_dt, status_cd = row
    yr = _year(filing_dt)
    if yr is None or yr >= pd_cutoff_year():
        return False, f"not public domain (filed {yr}; PD requires < {pd_cutoff_year()})"
    try:
        dead = int(status_cd) >= 700
    except (TypeError, ValueError):
        dead = False
    if not dead:
        return False, (f"mark is live (status {status_cd}); printing risks live trademark "
                       "rights — only dead/abandoned marks are eligible")
    return True, "PD + dead"


def check_patent_eligible(patent_no: str) -> tuple[bool, str]:
    """A patent figure is printable if the patent is PD (granted < cutoff)."""
    conn = duckdb.connect(str(config.DB["patents"]), read_only=True)
    row = conn.execute(
        "SELECT grant_dt FROM patents WHERE patent_no = ?", [patent_no]
    ).fetchone()
    conn.close()
    if row is None:
        return False, f"patent {patent_no} not found"
    yr = _year(row[0])
    if yr is None or yr >= pd_cutoff_year():
        return False, f"not public domain (granted {yr}; PD requires < {pd_cutoff_year()})"
    return True, "PD"


# ---------------------------------------------------------------------------
# Source images
# ---------------------------------------------------------------------------

def _load_mark(serial_no: str) -> Image.Image | None:
    from markery.common.assets import read_mark_image
    conn = duckdb.connect(str(config.DB["trademarks"]), read_only=True)
    data = read_mark_image(conn, serial_no)
    conn.close()
    return Image.open(io.BytesIO(data)) if data else None


def _load_patent_figure(patent_no: str) -> Image.Image | None:
    from markery.common.assets import read_patent_figure
    conn = duckdb.connect(str(config.DB["patents"]), read_only=True)
    data = read_patent_figure(conn, patent_no)
    conn.close()
    return Image.open(io.BytesIO(data)) if data else None


# ---------------------------------------------------------------------------
# Print transform (pure — no DB)
# ---------------------------------------------------------------------------

def to_print_asset(img: Image.Image, spec: dict) -> Image.Image:
    """Turn a source image into a print-ready RGBA canvas at the spec size.

    Near-white pixels become transparent (graded by luminance, preserving
    anti-aliased edges); the artwork is trimmed to content and centered on a
    transparent W×H canvas with a margin. Returns an RGBA image.
    """
    rgba = img.convert("RGBA")
    arr = np.array(rgba).astype(np.int16)
    gray = arr[..., :3].mean(axis=2)
    # alpha = how far from white: white→0 (transparent), dark→255 (opaque).
    alpha = np.clip(255 - gray, 0, 255).astype(np.uint8)
    arr[..., 3] = alpha
    keyed = Image.fromarray(arr.astype(np.uint8), "RGBA")

    # Trim to the non-transparent bounding box.
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)

    W, H = spec["w"], spec["h"]
    margin = spec.get("margin", 0.06)
    max_w, max_h = int(W * (1 - 2 * margin)), int(H * (1 - 2 * margin))
    w, h = keyed.size
    scale = min(max_w / w, max_h / h)
    new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
    art = keyed.resize(new_size, Image.LANCZOS)

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(art, ((W - new_size[0]) // 2, (H - new_size[1]) // 2))
    return canvas


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def _detect_kind(ident: str) -> str:
    return "patent" if any(c.isalpha() for c in ident) else "mark"


def build_print_asset(
    ident: str,
    project: str,
    *,
    kind: str | None = None,
    spec_name: str = "merch",
    out_dir: Path | None = None,
    upscale_first: bool = True,
) -> Path:
    """Build a print-ready PNG for an eligible mark/patent into the project print dir.

    Raises PermissionError if the source is not copyright+trademark clear,
    FileNotFoundError if no source image exists.
    """
    if spec_name not in SPECS:
        raise ValueError(f"unknown spec '{spec_name}'; choose from {list(SPECS)}")
    spec = SPECS[spec_name]
    kind = kind or _detect_kind(ident)

    if kind == "mark":
        ok, reason = check_mark_eligible(ident)
    elif kind == "patent":
        ok, reason = check_patent_eligible(ident)
    else:
        raise ValueError(f"unknown kind '{kind}' (expected 'mark' or 'patent')")
    if not ok:
        raise PermissionError(f"{kind} {ident} not eligible for print: {reason}")

    img = _load_mark(ident) if kind == "mark" else _load_patent_figure(ident)
    if img is None:
        raise FileNotFoundError(f"no source image for {kind} {ident}")

    # Only upscale when the source is smaller than the printable area — otherwise
    # to_print_asset would just downscale it again (and a 4× of an already-large
    # scan wastes work and can trip Pillow's decompression-bomb guard).
    target_max = int(max(spec["w"], spec["h"]) * (1 - 2 * spec.get("margin", 0.06)))
    if upscale_first and max(img.size) < target_max:
        img, _model = _upscale.upscale(img)

    canvas = to_print_asset(img, spec)

    out_dir = out_dir or (Project(project).root / "print")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ident}.png"
    canvas.save(out_path, format="PNG", dpi=(spec["dpi"], spec["dpi"]), optimize=True)

    size = out_path.stat().st_size
    if size > spec["max_bytes"]:
        raise ValueError(f"output {size} bytes exceeds spec max {spec['max_bytes']}")
    return out_path


def build_print_batch(
    where: str,
    project: str,
    *,
    spec_name: str = "merch",
    upscale_first: bool = True,
) -> tuple[list[str], list[tuple[str, str]]]:
    """Build print assets for every trademark drawing matching a SQL WHERE clause.

    `where` is applied to ``case_file`` (aliased ``cf``), e.g.
    "cf.mark_draw_cd LIKE '3%' AND cf.filing_dt BETWEEN DATE '1930-01-01' AND DATE '1930-12-31'".
    Only marks with a stored image are attempted; ineligible ones (live, not PD)
    are skipped with a reason. Returns (printed_serials, skipped[(serial, reason)]).
    """
    conn = duckdb.connect(str(config.DB["trademarks"]), read_only=True)
    serials = [str(r[0]) for r in conn.execute(
        f"SELECT cf.serial_no FROM case_file cf "
        f"JOIN mark_images mi ON cf.serial_no = mi.serial_no "
        f"WHERE {where} ORDER BY cf.serial_no"
    ).fetchall()]
    conn.close()

    printed: list[str] = []
    skipped: list[tuple[str, str]] = []
    for sn in serials:
        try:
            build_print_asset(sn, project, kind="mark", spec_name=spec_name,
                              upscale_first=upscale_first)
            printed.append(sn)
        except PermissionError as e:
            skipped.append((sn, str(e)))
        except (FileNotFoundError, ValueError) as e:
            skipped.append((sn, str(e)))
    return printed, skipped
