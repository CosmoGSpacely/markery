"""Tests for the Entities and Matches section index pages, the nav links that
reach them, and the breadcrumb trails that walk through them."""

from __future__ import annotations

from pathlib import Path

from markery.specialist.publisher.render import (
    render_entities_index,
    render_matches_index,
    _nav_links,
)


ENTITIES = [
    {"entity_id": 1, "canonical_name": "Radio Corp", "slug": "radio-corp",
     "industry": "Electronics", "entity_type": "Corporation"},
    {"entity_id": 2, "canonical_name": "Mack Trucks", "slug": "mack-trucks",
     "industry": "Automotive", "entity_type": "Corporation"},
]

STATS = {
    1: {"trademark_count": 5, "patent_count": 3, "match_count": 1},
    2: {"trademark_count": 2, "patent_count": 0, "match_count": 0},
}

MATCHES = [
    {"trademark_serial": 71423019, "trademark": "STERILAMP", "patent_no": "US2168861A",
     "entity_id": 1, "entity": "Radio Corp", "slug": "sterilamp-us2168861a",
     "essay_path": "/x.md", "has_image": False, "note": "A lamp story.",
     "filing_dt": "1939-08-25", "grant_dt": "1939-08-08"},
]


# ── nav links ────────────────────────────────────────────────────────────

def test_nav_links_point_to_section_indexes():
    links = _nav_links("p", ENTITIES)
    assert links["Entities"] == "entities/index.html"
    assert links["Matches"] == "matches/index.html"


def test_nav_links_do_not_enumerate_entities():
    # The nav must stay bounded regardless of entity count.
    links = _nav_links("p", ENTITIES)
    assert "Radio Corp" not in links
    assert "Mack Trucks" not in links


# ── entities index ───────────────────────────────────────────────────────

def test_entities_index_lists_every_entity(tmp_path: Path):
    p = render_entities_index("radio-pioneers", ENTITIES, STATS, tmp_path)
    html = p.read_text()
    assert p == tmp_path / "entities" / "index.html"
    assert 'href="radio-corp.html"' in html
    assert 'href="mack-trucks.html"' in html
    assert "Radio Corp" in html and "Mack Trucks" in html


def test_entities_index_has_breadcrumb(tmp_path: Path):
    html = render_entities_index("radio-pioneers", ENTITIES, STATS, tmp_path).read_text()
    assert 'aria-label="Breadcrumb"' in html
    assert 'href="../index.html">Home</a>' in html


# ── matches index ────────────────────────────────────────────────────────

def test_matches_index_lists_confirmed_pairs(tmp_path: Path):
    p = render_matches_index("radio-pioneers", MATCHES, ENTITIES, tmp_path)
    html = p.read_text()
    assert p == tmp_path / "matches" / "index.html"
    assert 'href="sterilamp-us2168861a.html"' in html
    assert "STERILAMP" in html


def test_matches_index_empty_message(tmp_path: Path):
    html = render_matches_index("radio-pioneers", [], ENTITIES, tmp_path).read_text()
    assert "No confirmed pairs yet." in html


def test_matches_index_skips_unconfirmed(tmp_path: Path):
    # A match without an essay_path is a candidate, not a confirmed pair.
    candidate = dict(MATCHES[0], essay_path=None, slug="x-y")
    html = render_matches_index("radio-pioneers", [candidate], ENTITIES, tmp_path).read_text()
    assert "No confirmed pairs yet." in html
