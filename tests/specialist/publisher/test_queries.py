"""Unit tests for publisher queries pure functions."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from markery.specialist.publisher.queries import (
    get_entity_stats,
    get_content_gaps,
    get_rendered_pages,
)


def _tm(entity_id: int, year: int) -> dict:
    return {"entity_id": entity_id, "filing_dt": date(year, 1, 1)}


def _pat(entity_id: int, year: int) -> dict:
    return {"entity_id": entity_id, "grant_dt": date(year, 6, 15)}


def _match(entity_id: int) -> dict:
    return {"entity_id": entity_id}


def test_get_entity_stats_counts():
    tms     = [_tm(1, 1920), _tm(1, 1925), _tm(2, 1930)]
    patents = [_pat(1, 1922), _pat(2, 1928), _pat(2, 1935)]
    matches = [_match(1), _match(1), _match(2)]

    stats = get_entity_stats([1, 2], tms, patents, matches)

    assert stats[1]["trademark_count"] == 2
    assert stats[1]["patent_count"]    == 1
    assert stats[1]["match_count"]     == 2
    assert stats[2]["trademark_count"] == 1
    assert stats[2]["patent_count"]    == 2
    assert stats[2]["match_count"]     == 1


def test_get_entity_stats_year_range():
    tms     = [_tm(1, 1915), _tm(1, 1938)]
    patents = [_pat(1, 1920)]

    stats = get_entity_stats([1], tms, patents, [])

    assert stats[1]["active_from"] == 1915
    assert stats[1]["active_to"]   == 1938


def test_get_entity_stats_empty_lists():
    stats = get_entity_stats([1, 2], [], [], [])

    for eid in (1, 2):
        assert stats[eid]["trademark_count"] == 0
        assert stats[eid]["patent_count"]    == 0
        assert stats[eid]["match_count"]     == 0
        assert stats[eid]["active_from"]     is None
        assert stats[eid]["active_to"]       is None


# ---------------------------------------------------------------------------
# Helpers for get_content_gaps / get_rendered_pages
# ---------------------------------------------------------------------------

def _make_project(tmp_path: Path, project: str = "test-proj") -> Path:
    """Create a minimal project directory layout under tmp_path."""
    proj_dir = tmp_path / "projects" / project
    (proj_dir / "matches").mkdir(parents=True)
    (proj_dir / "content").mkdir(parents=True)
    return proj_dir


def _patch_root(tmp_path: Path):
    """Return a context manager that patches ROOT to tmp_path."""
    import markery.common.config as cfg_mod
    return patch.object(cfg_mod, "ROOT", tmp_path)


# ---------------------------------------------------------------------------
# get_rendered_pages
# ---------------------------------------------------------------------------

def test_get_rendered_pages_empty_when_no_site(tmp_path: Path):
    _make_project(tmp_path)
    with _patch_root(tmp_path):
        pages = get_rendered_pages("test-proj")
    assert pages == []


def test_get_rendered_pages_returns_sorted_html_paths(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    site = proj_dir / "site"
    site.mkdir()
    (site / "index.html").write_text("<html/>")
    (site / "entity-remington.html").write_text("<html/>")
    sub = site / "sub"
    sub.mkdir()
    (sub / "page.html").write_text("<html/>")

    with _patch_root(tmp_path):
        pages = get_rendered_pages("test-proj")

    assert pages == sorted(["entity-remington.html", "index.html", "sub/page.html"])


def test_get_rendered_pages_ignores_non_html(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    site = proj_dir / "site"
    site.mkdir()
    (site / "index.html").write_text("<html/>")
    (site / "style.css").write_text("body {}")

    with _patch_root(tmp_path):
        pages = get_rendered_pages("test-proj")

    assert pages == ["index.html"]


# ---------------------------------------------------------------------------
# get_content_gaps
# ---------------------------------------------------------------------------

def _write_confirmed(proj_dir: Path, entries: list[dict]) -> None:
    path = proj_dir / "matches" / "confirmed.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")


def test_get_content_gaps_priority3_only_when_empty(tmp_path: Path):
    _make_project(tmp_path)
    with _patch_root(tmp_path), \
         patch("markery.specialist.publisher.queries.get_confirmed_matches", return_value=[]), \
         patch("markery.specialist.publisher.queries.get_entities", return_value=[]):
        gaps = get_content_gaps("test-proj")

    types = [g["type"] for g in gaps]
    assert "sources_page"  in types
    assert "timeline_page" in types
    assert not any(g["priority"] < 3 for g in gaps)


def test_get_content_gaps_priority1_missing_essay(tmp_path: Path):
    _make_project(tmp_path)
    fake_match = {
        "trademark": "VI-DEX",
        "patent_no": "US1261167A",
        "entity_id": 1,
        "slug": "vi-dex",
        "essay_path": None,
    }
    with _patch_root(tmp_path), \
         patch("markery.specialist.publisher.queries.get_confirmed_matches",
               return_value=[fake_match]), \
         patch("markery.specialist.publisher.queries.get_entities", return_value=[]):
        gaps = get_content_gaps("test-proj")

    p1 = [g for g in gaps if g["priority"] == 1]
    assert len(p1) == 1
    assert p1[0]["slug"] == "vi-dex"
    assert p1[0]["type"] == "match_essay"


def test_get_content_gaps_no_priority1_when_essay_exists(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    (proj_dir / "content" / "vi-dex.md").write_text("essay")
    fake_match = {
        "trademark": "VI-DEX",
        "patent_no": "US1261167A",
        "entity_id": 1,
        "slug": "vi-dex",
    }
    with _patch_root(tmp_path), \
         patch("markery.specialist.publisher.queries.get_confirmed_matches",
               return_value=[fake_match]), \
         patch("markery.specialist.publisher.queries.get_entities", return_value=[]):
        gaps = get_content_gaps("test-proj")

    assert not any(g["type"] == "match_essay" for g in gaps)


def test_get_content_gaps_priority2_missing_entity_summary(tmp_path: Path):
    _make_project(tmp_path)
    fake_entity = {"slug": "remington", "canonical_name": "Remington Typewriter Company"}
    with _patch_root(tmp_path), \
         patch("markery.specialist.publisher.queries.get_confirmed_matches", return_value=[]), \
         patch("markery.specialist.publisher.queries.get_entities", return_value=[fake_entity]):
        gaps = get_content_gaps("test-proj")

    p2 = [g for g in gaps if g["priority"] == 2]
    assert len(p2) == 1
    assert p2[0]["slug"] == "remington"
    assert p2[0]["type"] == "entity_summary"


def test_get_content_gaps_no_priority2_when_summary_exists(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    (proj_dir / "content" / "entity-remington.md").write_text("summary")
    fake_entity = {"slug": "remington", "canonical_name": "Remington Typewriter Company"}
    with _patch_root(tmp_path), \
         patch("markery.specialist.publisher.queries.get_confirmed_matches", return_value=[]), \
         patch("markery.specialist.publisher.queries.get_entities", return_value=[fake_entity]):
        gaps = get_content_gaps("test-proj")

    assert not any(g["type"] == "entity_summary" for g in gaps)


def test_get_content_gaps_sorted_by_priority_then_slug(tmp_path: Path):
    _make_project(tmp_path)
    matches = [
        {"trademark": "ZZZ", "patent_no": "US1A", "entity_id": 1, "slug": "zzz"},
        {"trademark": "AAA", "patent_no": "US2A", "entity_id": 1, "slug": "aaa"},
    ]
    entities = [
        {"slug": "beta", "canonical_name": "Beta Corp"},
        {"slug": "alpha", "canonical_name": "Alpha Corp"},
    ]
    with _patch_root(tmp_path), \
         patch("markery.specialist.publisher.queries.get_confirmed_matches",
               return_value=matches), \
         patch("markery.specialist.publisher.queries.get_entities", return_value=entities):
        gaps = get_content_gaps("test-proj")

    priorities = [g["priority"] for g in gaps]
    assert priorities == sorted(priorities)

    p1_slugs = [g["slug"] for g in gaps if g["priority"] == 1]
    assert p1_slugs == sorted(p1_slugs)

    p2_slugs = [g["slug"] for g in gaps if g["priority"] == 2]
    assert p2_slugs == sorted(p2_slugs)


def test_get_content_gaps_deduplicates_slugs(tmp_path: Path):
    _make_project(tmp_path)
    matches = [
        {"trademark": "VI-DEX", "patent_no": "US1A", "entity_id": 1, "slug": "vi-dex"},
        {"trademark": "VI-DEX", "patent_no": "US2A", "entity_id": 1, "slug": "vi-dex"},
    ]
    with _patch_root(tmp_path), \
         patch("markery.specialist.publisher.queries.get_confirmed_matches",
               return_value=matches), \
         patch("markery.specialist.publisher.queries.get_entities", return_value=[]):
        gaps = get_content_gaps("test-proj")

    p1 = [g for g in gaps if g["priority"] == 1]
    assert len(p1) == 1
