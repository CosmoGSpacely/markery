"""Record-image asset storage (Phase 28 P3).

Mark drawings and patent figures are stored as files under ``config.ASSETS_DIR``
(``data/assets/marks/<serial>.png`` and ``data/assets/patents/<patent_no>.png``),
not as DuckDB BLOBs. The ``mark_images`` / ``patent_figures`` rows reference the
file via a ``file`` column (path relative to ASSETS_DIR) plus a ``sha256``.

All readers and writers route through this module so the storage layout lives in
one place. Resolution is relative to ``config.ASSETS_DIR`` (which follows
``MARKERY_DATA_DIR`` / ``MARKERY_ROOT``), so a checkout/rebuild stays portable.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb

from markery.common import config


def assets_dir() -> Path:
    return config.ASSETS_DIR


def mark_rel(serial_no: str | int) -> str:
    return f"marks/{serial_no}.png"


def patent_rel(patent_no: str, figure_no: int = 1) -> str:
    suffix = "" if figure_no == 1 else f"-{figure_no}"
    return f"patents/{patent_no}{suffix}.png"


def _abs(rel: str) -> Path:
    return assets_dir() / rel


def write_asset(rel: str, data: bytes) -> str:
    """Write bytes to the asset file for ``rel``; return its sha256."""
    path = _abs(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def read_asset(rel: str | None) -> bytes | None:
    """Read bytes for a relative asset path; None if missing/absent."""
    if not rel:
        return None
    path = _abs(rel)
    if not path.exists():
        return None
    return path.read_bytes()


# ---------------------------------------------------------------------------
# Mark images
# ---------------------------------------------------------------------------

def read_mark_image(conn: duckdb.DuckDBPyConnection, serial_no: str | int) -> bytes | None:
    row = conn.execute(
        "SELECT file FROM mark_images WHERE serial_no = ?", [str(serial_no)]
    ).fetchone()
    if not row:
        # serial_no may be stored as BIGINT in some callers' joins; retry loosely.
        row = conn.execute(
            "SELECT file FROM mark_images WHERE CAST(serial_no AS VARCHAR) = ?",
            [str(serial_no)],
        ).fetchone()
    return read_asset(row[0]) if row else None


def store_mark_image(conn: duckdb.DuckDBPyConnection, serial_no: str | int,
                     data: bytes, fetched_dt=None) -> str:
    """Write the file and upsert the mark_images row. Returns the relative path."""
    from datetime import date
    rel = mark_rel(serial_no)
    sha = write_asset(rel, data)
    serial = str(serial_no)
    exists = conn.execute(
        "SELECT 1 FROM mark_images WHERE serial_no = ?", [serial]
    ).fetchone()
    if exists:
        conn.execute(
            "UPDATE mark_images SET file = ?, sha256 = ?, image_format = 'PNG', "
            "image_size = ?, fetched_dt = ? WHERE serial_no = ?",
            [rel, sha, len(data), fetched_dt or date.today(), serial],
        )
    else:
        conn.execute(
            "INSERT INTO mark_images (serial_no, file, sha256, image_format, image_size, fetched_dt) "
            "VALUES (?, ?, ?, 'PNG', ?, ?)",
            [serial, rel, sha, len(data), fetched_dt or date.today()],
        )
    conn.commit()
    return rel


# ---------------------------------------------------------------------------
# Patent figures
# ---------------------------------------------------------------------------

def read_patent_figure(conn: duckdb.DuckDBPyConnection, patent_no: str) -> bytes | None:
    row = conn.execute(
        "SELECT file FROM patent_figures "
        "WHERE patent_no = ? AND file IS NOT NULL ORDER BY figure_no LIMIT 1",
        [patent_no],
    ).fetchone()
    return read_asset(row[0]) if row else None


def store_patent_figure(conn: duckdb.DuckDBPyConnection, patent_no: str,
                        data: bytes, figure_no: int = 1, fetched_dt=None) -> str:
    from datetime import date
    rel = patent_rel(patent_no, figure_no)
    sha = write_asset(rel, data)
    exists = conn.execute(
        "SELECT 1 FROM patent_figures WHERE patent_no = ? AND figure_no = ?",
        [patent_no, figure_no],
    ).fetchone()
    if exists:
        conn.execute(
            "UPDATE patent_figures SET file = ?, sha256 = ?, figure_format = 'PNG', "
            "fetched_dt = ? WHERE patent_no = ? AND figure_no = ?",
            [rel, sha, fetched_dt or date.today(), patent_no, figure_no],
        )
    else:
        conn.execute(
            "INSERT INTO patent_figures (patent_no, figure_no, file, sha256, figure_format, fetched_dt) "
            "VALUES (?, ?, ?, ?, 'PNG', ?)",
            [patent_no, figure_no, rel, sha, fetched_dt or date.today()],
        )
    conn.commit()
    return rel
