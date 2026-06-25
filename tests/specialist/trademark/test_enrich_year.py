"""Phase 31 / D075 — design-mark image backfill query (hermetic)."""

from __future__ import annotations

import duckdb

from markery.specialist.trademark.cli import _design_serials_missing_image
from tests.fixtures.synthetic import build_synthetic_repo, REVIEW_SERIAL, REVIEW_YEAR, CAND_SERIAL


def test_finds_figurative_marks_missing_image(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    conn = duckdb.connect(str(repo.db_tm))
    # REVIEW_SERIAL: mark_draw_cd '3' (figurative), filed REVIEW_YEAR, no image → candidate.
    serials = _design_serials_missing_image(conn, REVIEW_YEAR, limit=10)
    conn.close()
    assert str(REVIEW_SERIAL) in serials
    # CAND_SERIAL is mark_draw_cd '4' (standard char) → excluded even though it
    # has an image; and design marks already imaged are excluded.
    assert str(CAND_SERIAL) not in serials


def test_limit_is_respected(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    conn = duckdb.connect(str(repo.db_tm))
    serials = _design_serials_missing_image(conn, REVIEW_YEAR, limit=0)
    conn.close()
    assert serials == []
