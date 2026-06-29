"""Tests for per-record detail pages (one trademark / one patent) and the
gallery card links that point to them (SITE-REVIEW #11)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from markery.specialist.publisher.render import (
    render_trademark_detail,
    render_patent_detail,
)
from markery.specialist.publisher.render.galleries import render_patent_gallery


ENTITIES = [
    {"entity_id": 1, "canonical_name": "L.S. Starrett Company", "slug": "ls-starrett-company",
     "industry": "Precision Tools", "entity_type": "Corporation"},
]

TM = {
    "serial_no": "71055630", "mark_name": "STARRETT", "filing_dt": date(1911, 4, 8),
    "draw_cd": "5T07", "registration_no": "0090123", "status_cd": 800,
    "owner_name": "L. S. STARRETT CO.", "goods": "precision measuring instruments",
    "first_use_dt": date(1900, 1, 1), "entity_id": 1, "entity_name": "L.S. Starrett Company",
    "image_available": False,
}

PAT = {
    "patent_no": "US1525813A", "title": "Combination Square", "grant_dt": date(1925, 2, 10),
    "application_dt": date(1923, 6, 1), "assignee_name": "STARRETT L S CO",
    "cpc_classes": ["G01B"], "inventors": ["King Edward P"], "figure_available": False,
    "entity_id": 1, "entity_name": "L.S. Starrett Company",
}

MATCHES = [
    {"trademark_serial": 71055630, "patent_no": "US1525813A", "entity_id": 1,
     "slug": "starrett-us1525813a", "essay_path": "/x.md"},
]


def test_patent_render_tolerates_null_inventors(tmp_path: Path):
    # EPO-fetched patents can carry null inventor names; rendering must not crash.
    pat = dict(PAT, inventors=[None, "King Edward P", None])
    html = render_patent_detail("precision-tools", pat, ENTITIES, [], tmp_path).read_text()
    assert "King Edward P" in html                          # valid inventor kept
    g = render_patent_gallery("precision-tools", ENTITIES, [pat], [], {1: "#abc"}, tmp_path)
    assert "King Edward P" in g.read_text()                 # gallery card too, no crash


def test_trademark_detail_path_and_fields(tmp_path: Path):
    p = render_trademark_detail("precision-tools", TM, ENTITIES, [], tmp_path)
    assert p == tmp_path / "trademarks" / "71055630.html"
    html = p.read_text()
    assert "<h1>STARRETT</h1>" in html
    assert "precision measuring instruments" in html       # full goods
    assert "5T07" in html                                   # drawing code
    assert "April 08, 1911" in html                         # full filing date
    assert 'href="../entities/ls-starrett-company.html"' in html  # entity link
    assert 'aria-label="Breadcrumb"' in html
    assert 'class="active" aria-current="page"' in html     # active nav


def test_trademark_detail_word_mark_placeholder_when_no_image(tmp_path: Path):
    html = render_trademark_detail("precision-tools", TM, ENTITIES, [], tmp_path).read_text()
    assert "detail-image-placeholder" in html
    assert ">STARRETT</div>" in html


def test_patent_detail_path_and_fields(tmp_path: Path):
    p = render_patent_detail("precision-tools", PAT, ENTITIES, [], tmp_path)
    assert p == tmp_path / "patents" / "US1525813A.html"
    html = p.read_text()
    assert "<h1>Combination Square</h1>" in html
    assert "February 10, 1925" in html                      # full grant date
    assert "King Edward P" in html                          # inventor
    assert "G01B" in html                                   # classification
    assert 'href="../entities/ls-starrett-company.html"' in html


def test_detail_confirmed_pair_link_prominent(tmp_path: Path):
    html = render_patent_detail("precision-tools", PAT, ENTITIES, MATCHES, tmp_path).read_text()
    assert "match-link--lg" in html
    assert 'href="../matches/starrett-us1525813a.html"' in html


def test_detail_no_match_link_when_unconfirmed(tmp_path: Path):
    # Note: the nav always carries a "../matches/index.html" link, so check the
    # specific essay link and the prominent-link class instead.
    html = render_patent_detail("precision-tools", PAT, ENTITIES, [], tmp_path).read_text()
    assert "starrett-us1525813a.html" not in html
    assert "Confirmed pair" not in html
