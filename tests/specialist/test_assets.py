"""Phase 28 P3 — record-image externalization (blobs → files), hermetic."""

from __future__ import annotations

import duckdb
import pytest

import markery.common.config as cfg
from markery.common import assets
from markery.specialist.patent import open_db as pat_open_db
from markery.specialist.trademark import open_db as tm_open_db

_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6360000002000001a721be6f0000000049454e44ae"
    "426082"
)


@pytest.fixture
def assets_dir(tmp_path, monkeypatch):
    d = tmp_path / "assets"
    monkeypatch.setattr(cfg, "ASSETS_DIR", d)
    return d


# ---------------------------------------------------------------------------
# asset layer round-trips
# ---------------------------------------------------------------------------

def test_store_and_read_mark_image(tmp_path, assets_dir):
    conn = tm_open_db(tmp_path / "tm.duckdb")
    rel = assets.store_mark_image(conn, "71999001", _PNG)
    assert rel == "marks/71999001.png"
    assert (assets_dir / rel).read_bytes() == _PNG
    assert assets.read_mark_image(conn, "71999001") == _PNG
    sha = conn.execute(
        "SELECT sha256 FROM mark_images WHERE serial_no = '71999001'"
    ).fetchone()[0]
    assert len(sha) == 64
    conn.close()


def test_store_and_read_patent_figure(tmp_path, assets_dir):
    conn = pat_open_db(tmp_path / "p.duckdb")
    rel = assets.store_patent_figure(conn, "US1999001A", _PNG)
    assert rel == "patents/US1999001A.png"
    assert assets.read_patent_figure(conn, "US1999001A") == _PNG
    conn.close()


def test_read_missing_returns_none(tmp_path, assets_dir):
    conn = tm_open_db(tmp_path / "tm.duckdb")
    assert assets.read_mark_image(conn, "70000000") is None
    conn.close()


# ---------------------------------------------------------------------------
# externalization migrations (old BLOB schema → files)
# ---------------------------------------------------------------------------

def test_mark_image_blob_migration(tmp_path, assets_dir):
    db = tmp_path / "legacy_tm.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute(
        "CREATE TABLE mark_images (serial_no VARCHAR PRIMARY KEY, image_data BLOB, "
        "image_format VARCHAR, image_size INTEGER, fetched_dt DATE)"
    )
    conn.execute("INSERT INTO mark_images VALUES ('71999001', ?, 'PNG', ?, NULL)",
                 [_PNG, len(_PNG)])
    conn.close()
    # Writable open externalizes the blob and drops image_data.
    conn = tm_open_db(db)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(mark_images)").fetchall()}
    assert "image_data" not in cols and "file" in cols
    assert (assets_dir / "marks/71999001.png").read_bytes() == _PNG
    assert assets.read_mark_image(conn, "71999001") == _PNG
    conn.close()


def test_patent_figure_blob_migration(tmp_path, assets_dir):
    db = tmp_path / "legacy_p.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute(
        "CREATE TABLE patent_figures (patent_no VARCHAR, figure_no INTEGER, "
        "figure_data BLOB, figure_format VARCHAR, fetched_dt DATE, "
        "PRIMARY KEY (patent_no, figure_no))"
    )
    conn.execute("INSERT INTO patent_figures VALUES ('US1A', 1, ?, 'PNG', NULL)", [_PNG])
    conn.close()
    conn = pat_open_db(db)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(patent_figures)").fetchall()}
    assert "figure_data" not in cols and "file" in cols
    assert assets.read_patent_figure(conn, "US1A") == _PNG
    conn.close()
