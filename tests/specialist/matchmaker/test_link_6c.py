"""Tests for Phase 6C: rescore_candidates() and resolve_report()."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from markery.specialist.matchmaker.link import (
    rescore_candidates,
    _parse_date,
    UNCERTAINTY_BAND,
)


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------

def test_parse_date_valid_iso():
    assert _parse_date("1918-04-02") == date(1918, 4, 2)


def test_parse_date_none_returns_none():
    assert _parse_date(None) is None


def test_parse_date_empty_returns_none():
    assert _parse_date("") is None


def test_parse_date_invalid_returns_none():
    assert _parse_date("not-a-date") is None


# ---------------------------------------------------------------------------
# UNCERTAINTY_BAND
# ---------------------------------------------------------------------------

def test_uncertainty_band_values():
    low, high = UNCERTAINTY_BAND
    assert low == 0.40
    assert high == 0.60


# ---------------------------------------------------------------------------
# rescore_candidates
# ---------------------------------------------------------------------------

def _candidate(
    patent_no: str = "US1261167A",
    serial_no: str = "71246709",
    grant_dt: str = "1918-04-02",
    filing_dt: str = "1921-06-07",
    cpc: list | None = None,
    title_name_hit: bool = False,
    abstract_name_hit: bool = False,
    goods_title_overlap: float = 0.0,
    goods_abstract_overlap: float = 0.0,
    score: float = 0.0,
) -> dict:
    return {
        "patent_no":            patent_no,
        "trademark_serial":     serial_no,
        "trademark":            "SOUNDEX",
        "entity_id":            1,
        "entity":               "Remington Rand",
        "patent_grant_dt":      grant_dt,
        "tm_filing_dt":         filing_dt,
        "cpc_classes":          cpc or ["B42F"],
        "title_name_hit":       title_name_hit,
        "abstract_name_hit":    abstract_name_hit,
        "goods_title_overlap":  goods_title_overlap,
        "goods_abstract_overlap": goods_abstract_overlap,
        "score":                score,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_rescore_candidates_updates_score(tmp_path):
    p = tmp_path / "candidates.jsonl"
    _write_jsonl(p, [_candidate(score=0.0)])
    n = rescore_candidates(p)
    assert n == 1
    result = json.loads(p.read_text().splitlines()[0])
    # structural: date_score(1918-04-02, 1921-06-07) + class_score(["B42F"])
    # date gap ~3.2 years → proximity ≈ 0.84 → date_score ≈ 0.42
    # class_score = 0.3 → structural ≈ 0.72
    assert result["score"] > 0.0


def test_rescore_candidates_adds_semantic_bonus_for_title_hit(tmp_path):
    p = tmp_path / "candidates.jsonl"
    base_row = _candidate()
    hit_row  = _candidate(title_name_hit=True)
    _write_jsonl(p, [base_row])
    rescore_candidates(p)
    base_score = json.loads(p.read_text().splitlines()[0])["score"]

    _write_jsonl(p, [hit_row])
    rescore_candidates(p)
    hit_score = json.loads(p.read_text().splitlines()[0])["score"]

    assert round(hit_score - base_score, 4) == 0.20


def test_rescore_candidates_caps_semantic_at_025(tmp_path):
    p = tmp_path / "candidates.jsonl"
    row = _candidate(
        title_name_hit=True, abstract_name_hit=True,
        goods_title_overlap=0.20, goods_abstract_overlap=0.20,
    )
    _write_jsonl(p, [row])
    rescore_candidates(p)
    result = json.loads(p.read_text().splitlines()[0])
    # structural ~ 0.72 + semantic_cap 0.25 = ~0.97; raw semantic = 0.45 > cap
    # verify semantic portion is exactly 0.25
    from markery.specialist.matchmaker.score import date_score, class_score
    struct = date_score(date(1918, 4, 2), date(1921, 6, 7)) + class_score(["B42F"])
    assert abs(result["score"] - round(struct + 0.25, 4)) < 1e-6


def test_rescore_candidates_no_signal_fields_uses_zero_bonus(tmp_path):
    """Candidates without signal fields rescore to their structural score."""
    p = tmp_path / "candidates.jsonl"
    row = {
        "patent_no": "US1261167A", "trademark_serial": "71246709",
        "trademark": "SOUNDEX", "score": 0.99,
        "patent_grant_dt": "1918-04-02", "tm_filing_dt": "1921-06-07",
        "cpc_classes": [],
    }
    _write_jsonl(p, [row])
    rescore_candidates(p)
    result = json.loads(p.read_text().splitlines()[0])
    from markery.specialist.matchmaker.score import date_score, class_score
    expected = round(date_score(date(1918, 4, 2), date(1921, 6, 7)) + class_score([]), 4)
    assert result["score"] == expected


def test_rescore_candidates_missing_file(tmp_path, capsys):
    n = rescore_candidates(tmp_path / "nonexistent.jsonl")
    assert n == 0
    assert "No candidates" in capsys.readouterr().out


def test_rescore_candidates_preserves_other_fields(tmp_path):
    p = tmp_path / "candidates.jsonl"
    row = _candidate()
    row["custom_field"] = "preserved"
    _write_jsonl(p, [row])
    rescore_candidates(p)
    result = json.loads(p.read_text().splitlines()[0])
    assert result["custom_field"] == "preserved"


def test_rescore_candidates_multi_row(tmp_path):
    p = tmp_path / "candidates.jsonl"
    rows = [
        _candidate("US1261167A", "71246709"),
        _candidate("US1527374A", "71297261",
                   grant_dt="1924-02-19", filing_dt="1926-09-17"),
    ]
    _write_jsonl(p, rows)
    n = rescore_candidates(p)
    assert n == 2
    results = [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]
    assert all(r["score"] > 0 for r in results)
