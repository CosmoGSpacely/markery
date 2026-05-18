"""Unit tests for patent figure BLOB storage."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from markery.specialist.patent.build import open_db
from markery.specialist.patent.figures import fetch_and_store, migrate_path_figures, _tiff_to_png


# ---------------------------------------------------------------------------
# _tiff_to_png
# ---------------------------------------------------------------------------

def _make_tiff_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (8, 8), color=(128, 64, 32))
    img.save(buf, format="TIFF")
    return buf.getvalue()


def test_tiff_to_png_produces_png():
    tiff = _make_tiff_bytes()
    png  = _tiff_to_png(tiff)
    assert png[:4] == b"\x89PNG"


# ---------------------------------------------------------------------------
# fetch_and_store
# ---------------------------------------------------------------------------

def _in_memory_db():
    conn = open_db(":memory:")
    return conn


def test_fetch_and_store_inserts_new_figure():
    conn   = _in_memory_db()
    tiff   = _make_tiff_bytes()
    client = MagicMock()
    client.fetch_figure.return_value = tiff

    result = fetch_and_store("US1234567A", client, conn)
    assert result is True

    row = conn.execute(
        "SELECT figure_data, figure_format FROM patent_figures WHERE patent_no = 'US1234567A'"
    ).fetchone()
    assert row is not None
    assert row[0][:4] == b"\x89PNG"
    assert row[1] == "PNG"
    conn.close()


def test_fetch_and_store_skips_if_already_stored():
    conn   = _in_memory_db()
    tiff   = _make_tiff_bytes()
    client = MagicMock()
    client.fetch_figure.return_value = tiff

    fetch_and_store("US1234567A", client, conn)
    result = fetch_and_store("US1234567A", client, conn)
    assert result is False
    assert client.fetch_figure.call_count == 1   # not called again
    conn.close()


def test_fetch_and_store_returns_false_when_no_figure():
    conn   = _in_memory_db()
    client = MagicMock()
    client.fetch_figure.return_value = None

    result = fetch_and_store("US9999999A", client, conn)
    assert result is False
    row = conn.execute(
        "SELECT 1 FROM patent_figures WHERE patent_no = 'US9999999A'"
    ).fetchone()
    assert row is None
    conn.close()


def test_fetch_and_store_updates_existing_row_without_data():
    """A row exists (figure_no=1) but figure_data is NULL — should UPDATE, not INSERT."""
    conn = _in_memory_db()
    conn.execute(
        "INSERT INTO patent_figures (patent_no, figure_no) VALUES ('US1234567A', 1)"
    )
    conn.commit()

    tiff   = _make_tiff_bytes()
    client = MagicMock()
    client.fetch_figure.return_value = tiff

    result = fetch_and_store("US1234567A", client, conn)
    assert result is True

    row = conn.execute(
        "SELECT figure_data FROM patent_figures WHERE patent_no = 'US1234567A' AND figure_no = 1"
    ).fetchone()
    assert row[0][:4] == b"\x89PNG"
    conn.close()


# ---------------------------------------------------------------------------
# migrate_path_figures
# ---------------------------------------------------------------------------

def test_migrate_path_figures(tmp_path: Path):
    conn = _in_memory_db()
    conn.execute(
        "INSERT INTO patent_figures (patent_no, figure_no) VALUES ('USTEST001A', 1)"
    )
    conn.commit()

    # Write a PNG into the expected location
    fig_dir = tmp_path / "projects" / "test-proj" / "output" / "patent-figures" / "USTEST001A"
    fig_dir.mkdir(parents=True)
    img = Image.new("RGB", (4, 4))
    img.save(fig_dir / "fig_001.png", format="PNG")

    # Patch ROOT so migrate_path_figures finds tmp_path
    import markery.specialist.patent.figures as fig_mod
    original_root = fig_mod.ROOT
    fig_mod.ROOT = tmp_path
    try:
        n = migrate_path_figures("test-proj", conn)
    finally:
        fig_mod.ROOT = original_root

    assert n == 1
    row = conn.execute(
        "SELECT figure_data FROM patent_figures WHERE patent_no = 'USTEST001A'"
    ).fetchone()
    assert row[0][:4] == b"\x89PNG"
    conn.close()


def test_migrate_path_figures_skips_missing(tmp_path: Path):
    conn = _in_memory_db()
    conn.execute(
        "INSERT INTO patent_figures (patent_no, figure_no) VALUES ('USNOFIG001A', 1)"
    )
    conn.commit()

    # No PNG file on disk
    (tmp_path / "projects" / "test-proj" / "output" / "patent-figures").mkdir(parents=True)

    import markery.specialist.patent.figures as fig_mod
    original_root = fig_mod.ROOT
    fig_mod.ROOT = tmp_path
    try:
        n = migrate_path_figures("test-proj", conn)
    finally:
        fig_mod.ROOT = original_root

    assert n == 0
    conn.close()


def test_migrate_path_figures_idempotent(tmp_path: Path):
    """Re-running migration skips rows that already have figure_data."""
    conn   = _in_memory_db()
    tiff   = _make_tiff_bytes()
    client = MagicMock()
    client.fetch_figure.return_value = tiff
    fetch_and_store("US1234567A", client, conn)  # already has data

    import markery.specialist.patent.figures as fig_mod
    original_root = fig_mod.ROOT
    fig_mod.ROOT = tmp_path
    try:
        n = migrate_path_figures("test-proj", conn)
    finally:
        fig_mod.ROOT = original_root

    assert n == 0
    conn.close()
