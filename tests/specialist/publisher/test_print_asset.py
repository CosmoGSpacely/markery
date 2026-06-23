"""Tests for print-ready asset generation (Phase 24 P5)."""

from __future__ import annotations

import io
from datetime import date

import duckdb
import pytest
from PIL import Image

import markery.common.config as cfg
import markery.common.project as projmod
from markery.specialist.publisher.image_enhancement import print_asset as pa


def _png_bytes(color=(0, 0, 0)) -> bytes:
    # A small image: black square on white (so it has content + white margin).
    im = Image.new("RGB", (100, 80), (255, 255, 255))
    for x in range(20, 80):
        for y in range(20, 60):
            im.putpixel((x, y), color)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


# ── pure transform ───────────────────────────────────────────────────────────

def test_to_print_asset_size_mode_and_transparency():
    src = Image.open(io.BytesIO(_png_bytes()))
    spec = pa.SPECS["merch"]
    out = pa.to_print_asset(src, spec)
    assert out.size == (spec["w"], spec["h"])     # 4500x5400
    assert out.mode == "RGBA"
    import numpy as np
    alpha = np.array(out)[..., 3]
    assert alpha.min() == 0      # transparent margin/background
    assert alpha.max() > 0       # opaque artwork present


def test_detect_kind():
    assert pa._detect_kind("71055630") == "mark"
    assert pa._detect_kind("US1525813A") == "patent"


def test_pd_cutoff_is_95_years():
    assert pa.pd_cutoff_year() == date.today().year - 95


# ── eligibility (temp DBs) ───────────────────────────────────────────────────

@pytest.fixture()
def temp_dbs(tmp_path, monkeypatch):
    tdb = tmp_path / "trademarks.duckdb"
    pdb = tmp_path / "patents.duckdb"
    c = duckdb.connect(str(tdb))
    c.execute("CREATE TABLE case_file (serial_no VARCHAR, filing_dt DATE, cfh_status_cd VARCHAR, mark_draw_cd VARCHAR)")
    c.execute("CREATE TABLE mark_images (serial_no VARCHAR, image_data BLOB)")
    # dead + PD, live + PD, dead + too-new
    c.execute("INSERT INTO case_file VALUES ('111', DATE '1925-01-01', '710', '3000')")
    c.execute("INSERT INTO case_file VALUES ('222', DATE '1925-01-01', '600', '3000')")
    c.execute("INSERT INTO case_file VALUES ('333', DATE '2000-01-01', '710', '3000')")
    c.execute("INSERT INTO mark_images VALUES ('111', ?)", [_png_bytes()])
    c.close()
    p = duckdb.connect(str(pdb))
    p.execute("CREATE TABLE patents (patent_no VARCHAR, grant_dt DATE)")
    p.execute("CREATE TABLE patent_figures (patent_no VARCHAR, figure_no INT, figure_data BLOB)")
    p.execute("INSERT INTO patents VALUES ('US1525813A', DATE '1925-02-10')")
    p.execute("INSERT INTO patents VALUES ('US9999999A', DATE '2010-01-01')")
    p.execute("INSERT INTO patent_figures VALUES ('US1525813A', 1, ?)", [_png_bytes()])
    p.close()
    monkeypatch.setitem(cfg.DB, "trademarks", tdb)
    monkeypatch.setitem(cfg.DB, "patents", pdb)
    monkeypatch.setattr(projmod, "ROOT", tmp_path)
    (tmp_path / "projects" / "demo").mkdir(parents=True)
    return tmp_path


def test_mark_eligibility(temp_dbs):
    assert pa.check_mark_eligible("111")[0] is True               # dead + PD
    assert pa.check_mark_eligible("222")[0] is False              # live → trademark risk
    assert "live" in pa.check_mark_eligible("222")[1]
    assert pa.check_mark_eligible("333")[0] is False              # too new → not PD
    assert "public domain" in pa.check_mark_eligible("333")[1]


def test_patent_eligibility(temp_dbs):
    assert pa.check_patent_eligible("US1525813A")[0] is True
    assert pa.check_patent_eligible("US9999999A")[0] is False     # granted 2010 → not PD


# ── end-to-end build ─────────────────────────────────────────────────────────

def test_build_eligible_mark_writes_print_png(temp_dbs):
    out = pa.build_print_asset("111", "demo", upscale_first=False)
    assert out == temp_dbs / "projects" / "demo" / "print" / "111.png"
    im = Image.open(out)
    assert im.size == (4500, 5400)
    dpi = im.info.get("dpi")
    assert dpi and round(dpi[0]) == 300 and round(dpi[1]) == 300  # PNG stores ppm (≈299.999)
    assert im.mode == "RGBA"


def test_build_rejects_live_mark(temp_dbs):
    with pytest.raises(PermissionError):
        pa.build_print_asset("222", "demo", upscale_first=False)
