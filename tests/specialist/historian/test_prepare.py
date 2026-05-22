"""Unit tests for historian prepare module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from markery.specialist.historian.prepare import (
    count_unreviewed,
    top_candidates,
    render_brief,
    gather_patent_state,
    gather_trademark_state,
)
from markery.specialist.patent.build import open_db as pat_open_db, insert_patent
from markery.specialist.trademark.build import open_db as tm_open_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PATENT = {
    "patent_no":     "US1261167A",
    "title":         "Index",
    "app_dt":        "1917-10-25",
    "grant_dt":      "1918-04-02",
    "abstract":      "Phonetic indexing system for surnames.",
    "assignee_name": "Remington Typewriter Company",
    "cpc":           ["B42F17/00"],
    "inventors":     ["Russell Robert C"],
}

_PATENT_NO_ABSTRACT = {
    "patent_no":     "US9999999A",
    "title":         "Widget",
    "app_dt":        "1920-01-01",
    "grant_dt":      "1921-01-01",
    "abstract":      None,
    "assignee_name": "Widget Corp",
    "cpc":           [],
    "inventors":     [],
}

_CONFIRMED = [
    {"patent_no": "US1261167A", "trademark_serial": 71246709,
     "trademark": "SOUNDEX", "entity_id": 1, "entity": "Remington Rand"},
]

_CANDIDATE = {
    "patent_no": "US1435663A", "trademark_serial": 71255821,
    "trademark": "SOUNDEX QUICK AS A FLASH", "entity_id": 1,
    "entity": "Remington Rand", "score": 0.75,
}


def _make_project(tmp_path: Path, project: str = "test-proj") -> Path:
    proj_dir = tmp_path / "projects" / project
    (proj_dir / "matches").mkdir(parents=True)
    (proj_dir / "content").mkdir(parents=True)
    return proj_dir


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


from contextlib import contextmanager

@contextmanager
def _patch_root(tmp_path: Path):
    """Patch ROOT in both config and project modules."""
    import markery.common.config as cfg_mod
    import markery.common.project as proj_mod
    with patch.object(cfg_mod, "ROOT", tmp_path), \
         patch.object(proj_mod, "ROOT", tmp_path):
        yield


# ---------------------------------------------------------------------------
# gather_patent_state
# ---------------------------------------------------------------------------

def test_gather_patent_state_abstract_true():
    conn = pat_open_db(":memory:")
    insert_patent(conn, _PATENT)
    state = gather_patent_state(conn, ["US1261167A"])
    assert state["US1261167A"]["abstract"] is True
    conn.close()


def test_gather_patent_state_abstract_false():
    conn = pat_open_db(":memory:")
    insert_patent(conn, _PATENT_NO_ABSTRACT)
    state = gather_patent_state(conn, ["US9999999A"])
    assert state["US9999999A"]["abstract"] is False
    conn.close()


def test_gather_patent_state_figure_false_when_no_blob():
    conn = pat_open_db(":memory:")
    insert_patent(conn, _PATENT)
    state = gather_patent_state(conn, ["US1261167A"])
    assert state["US1261167A"]["figure"] is False
    conn.close()


def test_gather_patent_state_figure_true_when_blob():
    conn = pat_open_db(":memory:")
    insert_patent(conn, _PATENT)
    conn.execute(
        "INSERT INTO patent_figures (patent_no, figure_no, figure_data) VALUES (?,?,?)",
        ["US1261167A", 1, b"\x89PNG"],
    )
    state = gather_patent_state(conn, ["US1261167A"])
    assert state["US1261167A"]["figure"] is True
    conn.close()


def test_gather_patent_state_empty_list():
    conn = pat_open_db(":memory:")
    assert gather_patent_state(conn, []) == {}
    conn.close()


# ---------------------------------------------------------------------------
# gather_trademark_state
# ---------------------------------------------------------------------------

_CASE_FILE_DDL = """
CREATE TABLE IF NOT EXISTS case_file (
    serial_no VARCHAR PRIMARY KEY, mark_id_char VARCHAR,
    filing_dt DATE, mark_draw_cd VARCHAR, registration_no VARCHAR, cfh_status_cd VARCHAR
)
"""
_STATEMENT_DDL = """
CREATE TABLE IF NOT EXISTS statement (
    serial_no VARCHAR, statement_type_cd VARCHAR, statement_text VARCHAR
)
"""


def _tm_db():
    conn = tm_open_db(":memory:")
    conn.execute(_CASE_FILE_DDL)
    conn.execute(_STATEMENT_DDL)
    return conn


def test_gather_trademark_state_true_when_goods_desc_present():
    conn = _tm_db()
    conn.execute(
        "INSERT INTO statement (serial_no, statement_type_cd, statement_text) VALUES (?,?,?)",
        ["71246709", "GS0001", "Card filing systems"],
    )
    state = gather_trademark_state(conn, ["71246709"])
    assert state["71246709"] is True
    conn.close()


def test_gather_trademark_state_false_when_no_desc():
    conn = _tm_db()
    state = gather_trademark_state(conn, ["71246709"])
    assert state["71246709"] is False
    conn.close()


def test_gather_trademark_state_empty_list():
    conn = _tm_db()
    assert gather_trademark_state(conn, []) == {}
    conn.close()


# ---------------------------------------------------------------------------
# count_unreviewed
# ---------------------------------------------------------------------------

def test_count_unreviewed_basic(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    _write_jsonl(proj_dir / "matches" / "candidates.jsonl", [
        {**_CANDIDATE, "score": 0.80},
        {"patent_no": "US1435663A", "trademark_serial": "71111111",
         "trademark": "OTHER", "score": 0.75, "entity": "X"},
    ])
    _write_jsonl(proj_dir / "matches" / "confirmed.jsonl", _CONFIRMED)

    with _patch_root(tmp_path):
        from markery.common.project import Project
        proj = Project("test-proj")
        n = count_unreviewed(proj, min_score=0.5)

    assert n == 2  # neither candidate matches a confirmed pair


def test_count_unreviewed_excludes_confirmed(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    _write_jsonl(proj_dir / "matches" / "candidates.jsonl", [
        {"patent_no": "US1261167A", "trademark_serial": 71246709,
         "trademark": "SOUNDEX", "score": 0.90, "entity": "Remington Rand"},
    ])
    _write_jsonl(proj_dir / "matches" / "confirmed.jsonl", _CONFIRMED)

    with _patch_root(tmp_path):
        from markery.common.project import Project
        proj = Project("test-proj")
        n = count_unreviewed(proj, min_score=0.5)

    assert n == 0


def test_count_unreviewed_excludes_below_min_score(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    _write_jsonl(proj_dir / "matches" / "candidates.jsonl", [
        {**_CANDIDATE, "score": 0.30},
    ])

    with _patch_root(tmp_path):
        from markery.common.project import Project
        proj = Project("test-proj")
        n = count_unreviewed(proj, min_score=0.5)

    assert n == 0


def test_count_unreviewed_excludes_rejected(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    _write_jsonl(proj_dir / "matches" / "candidates.jsonl", [_CANDIDATE])
    _write_jsonl(proj_dir / "matches" / "rejected.jsonl", [
        {"patent_no": "US1435663A", "trademark_serial": "71255821",
         "trademark": "SOUNDEX QUICK AS A FLASH", "rejection_note": ""},
    ])

    with _patch_root(tmp_path):
        from markery.common.project import Project
        proj = Project("test-proj")
        n = count_unreviewed(proj, min_score=0.5)

    assert n == 0


def test_count_unreviewed_empty_candidates(tmp_path: Path):
    _make_project(tmp_path)

    with _patch_root(tmp_path):
        from markery.common.project import Project
        proj = Project("test-proj")
        n = count_unreviewed(proj)

    assert n == 0


# ---------------------------------------------------------------------------
# top_candidates
# ---------------------------------------------------------------------------

def test_top_candidates_sorted_by_score_descending(tmp_path: Path):
    proj_dir = _make_project(tmp_path)
    cands = [
        {"patent_no": f"US{i}A", "trademark_serial": f"7100{i}",
         "trademark": f"MARK{i}", "score": i * 0.1, "entity": "X"}
        for i in range(1, 8)
    ]
    _write_jsonl(proj_dir / "matches" / "candidates.jsonl", cands)

    with _patch_root(tmp_path):
        from markery.common.project import Project
        proj = Project("test-proj")
        top = top_candidates(proj, min_score=0.5, n=3)

    scores = [c["score"] for c in top]
    assert scores == sorted(scores, reverse=True)
    assert len(top) == 3


# ---------------------------------------------------------------------------
# render_brief
# ---------------------------------------------------------------------------

def test_render_brief_contains_yaml_frontmatter():
    result = render_brief(
        project="test-proj",
        confirmed=_CONFIRMED,
        gaps=[],
        patent_state={"US1261167A": {"abstract": True, "figure": False}},
        tm_state={"71246709": True},
        unreviewed_count=5,
        top_cands=[],
        prepared_at="2026-05-19T10:00:00",
    )
    assert result.startswith("---\n")
    assert "project: test-proj" in result
    assert "prepared: 2026-05-19T10:00:00" in result
    assert "confirmed_count: 1" in result
    assert "candidate_count_unreviewed: 5" in result


def test_render_brief_signals_in_yaml():
    result = render_brief(
        project="test-proj",
        confirmed=_CONFIRMED,
        gaps=[],
        patent_state={"US1261167A": {"abstract": True, "figure": True}},
        tm_state={},
        unreviewed_count=0,
        top_cands=[],
        prepared_at="2026-05-19T10:00:00",
    )
    assert "US1261167A" in result
    assert "signals_available" in result
    assert "figures_available" in result


def test_render_brief_content_gaps_listed():
    gaps = [{"type": "match_essay", "slug": "vi-dex", "priority": 1,
             "label": "VI-DEX ↔ US1527374A", "path": "content/vi-dex.md"}]
    result = render_brief(
        project="test-proj",
        confirmed=[],
        gaps=gaps,
        patent_state={},
        tm_state={},
        unreviewed_count=0,
        top_cands=[],
        prepared_at="2026-05-19T10:00:00",
    )
    assert "Content Gaps" in result
    assert "vi-dex" in result


def test_render_brief_session_recommendation_present():
    gaps = [{"type": "match_essay", "slug": "handiref", "priority": 1,
             "label": "HANDIREF ↔ US1614080A", "path": "content/handiref.md"}]
    result = render_brief(
        project="test-proj",
        confirmed=[],
        gaps=gaps,
        patent_state={},
        tm_state={},
        unreviewed_count=0,
        top_cands=[],
        prepared_at="2026-05-19T10:00:00",
    )
    assert "Session Recommendation" in result
    assert "HANDIREF" in result


def test_render_brief_no_gaps_message():
    result = render_brief(
        project="test-proj",
        confirmed=[],
        gaps=[],
        patent_state={},
        tm_state={},
        unreviewed_count=0,
        top_cands=[],
        prepared_at="2026-05-19T10:00:00",
    )
    assert "No content gaps detected" in result


def test_render_brief_candidate_highlights_table():
    cands = [
        {"patent_no": "US1435663A", "trademark_serial": "71255821",
         "trademark": "SOUNDEX QAF", "score": 0.82, "entity": "Remington Rand"},
    ]
    result = render_brief(
        project="test-proj",
        confirmed=[],
        gaps=[],
        patent_state={},
        tm_state={},
        unreviewed_count=1,
        top_cands=cands,
        prepared_at="2026-05-19T10:00:00",
    )
    assert "Candidate Highlights" in result
    assert "US1435663A" in result
    assert "0.820" in result
