"""Patent figure fetch and BLOB storage.

Figures are stored as PNG BLOBs in patent_figures.figure_data.
Two entry points:

    fetch_and_store(patent_no, client, conn)
        Fetch page-1 drawing from EPO OPS, convert TIFF→PNG, upsert BLOB.

    migrate_path_figures(project, conn)
        One-time migration: read existing PNGs from projects/<project>/output/
        patent-figures/ and insert as BLOBs. Idempotent -- skips rows that
        already have figure_data set.

Note: Google Patents PDF download was considered and dropped. EPO OPS is the
authoritative source for pre-1940 drawings. See reference/epo-ops-api.md for
endpoint details and known limitations.
"""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import duckdb
from PIL import Image

from markery.common.config import ROOT
from markery.specialist.patent.epo_client import EPOClient


def fetch_and_store(
    patent_no: str,
    client: EPOClient,
    conn: duckdb.DuckDBPyConnection,
) -> bool:
    """Fetch page-1 figure from EPO OPS and upsert as PNG BLOB.

    Returns True if a new figure was stored, False if the patent had no
    figure available or already has a BLOB stored.
    """
    existing = conn.execute(
        "SELECT figure_data FROM patent_figures WHERE patent_no = ? AND figure_no = 1",
        [patent_no],
    ).fetchone()
    if existing and existing[0] is not None:
        return False  # already stored

    tiff_bytes = client.fetch_figure(patent_no, page=1)
    if tiff_bytes is None:
        return False

    png_bytes = _tiff_to_png(tiff_bytes)

    if existing:
        conn.execute(
            """UPDATE patent_figures
               SET figure_data = ?, figure_format = 'PNG', fetched_dt = ?
               WHERE patent_no = ? AND figure_no = 1""",
            [png_bytes, date.today(), patent_no],
        )
    else:
        conn.execute(
            """INSERT INTO patent_figures (patent_no, figure_no, figure_data, figure_format, fetched_dt)
               VALUES (?, 1, ?, 'PNG', ?)""",
            [patent_no, png_bytes, date.today()],
        )
    conn.commit()
    return True


def migrate_path_figures(project: str, conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate on-disk PNG files to BLOB storage. Returns count inserted.

    Reads from projects/<project>/output/patent-figures/<patent_no>/fig_001.png.
    Skips any patent_no that already has figure_data populated.
    Safe to re-run (idempotent).
    """
    fig_root = ROOT / "projects" / project / "output" / "patent-figures"
    if not fig_root.is_dir():
        print(f"  No figures directory found at {fig_root}")
        return 0

    rows = conn.execute(
        "SELECT patent_no FROM patent_figures WHERE figure_data IS NULL"
    ).fetchall()

    inserted = 0
    for (patent_no,) in rows:
        png_path = fig_root / patent_no / "fig_001.png"
        if not png_path.exists():
            png_path = None
        if png_path is None:
            print(f"  {patent_no}: no PNG found, skipping")
            continue

        png_bytes = png_path.read_bytes()  # type: ignore[union-attr]
        conn.execute(
            """UPDATE patent_figures
               SET figure_data = ?, figure_format = 'PNG', fetched_dt = ?
               WHERE patent_no = ? AND figure_no = 1""",
            [png_bytes, date.today(), patent_no],
        )
        inserted += 1

    conn.commit()
    return inserted


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _tiff_to_png(tiff_bytes: bytes) -> bytes:
    buf = io.BytesIO()
    with Image.open(io.BytesIO(tiff_bytes)) as img:
        img.save(buf, format="PNG")
    return buf.getvalue()
