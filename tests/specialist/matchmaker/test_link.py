"""Unit tests for link.py helper functions."""

from __future__ import annotations

import json
from pathlib import Path

from markery.specialist.matchmaker.link import (
    entity_ids_for_project,
    read_confirmed,
    read_rejected,
    write_candidates,
)


def test_entity_ids_for_project_reads_integers(tmp_path: Path):
    f = tmp_path / "entities.txt"
    f.write_text("1\n2\n3\n")
    assert entity_ids_for_project(f) == [1, 2, 3]


def test_entity_ids_for_project_ignores_comments(tmp_path: Path):
    f = tmp_path / "entities.txt"
    f.write_text("# header comment\n1\n2  # inline comment\n\n3\n")
    assert entity_ids_for_project(f) == [1, 2, 3]


def test_entity_ids_for_project_missing_file(tmp_path: Path):
    assert entity_ids_for_project(tmp_path / "no_such_file.txt") == []


def test_read_confirmed_returns_empty_when_missing(tmp_path: Path):
    assert read_confirmed(tmp_path / "missing.jsonl") == []


def test_read_confirmed_parses_jsonl(tmp_path: Path):
    p = tmp_path / "confirmed.jsonl"
    rows = [
        {"patent_no": "US123A", "trademark_serial": "71000001", "score": 0.8},
        {"patent_no": "US456A", "trademark_serial": "71000002", "score": 0.6},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    result = read_confirmed(p)
    assert len(result) == 2
    assert result[0]["patent_no"] == "US123A"


def test_write_candidates_roundtrip(tmp_path: Path):
    candidates = [
        {"patent_no": "US123A", "trademark_serial": 71000001, "score": 0.75},
        {"patent_no": "US456A", "trademark_serial": 71000002, "score": 0.50},
    ]
    out = tmp_path / "matches" / "candidates.jsonl"
    write_candidates(candidates, out)

    assert out.exists()
    lines = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    assert lines[0]["score"] == 0.75


def test_write_candidates_creates_parent_dir(tmp_path: Path):
    out = tmp_path / "deep" / "nested" / "candidates.jsonl"
    write_candidates([{"x": 1}], out)
    assert out.exists()


def test_read_rejected_returns_empty_when_missing(tmp_path: Path):
    assert read_rejected(tmp_path / "missing.jsonl") == set()


def test_read_rejected_parses_jsonl(tmp_path: Path):
    p = tmp_path / "rejected.jsonl"
    rows = [
        {"patent_no": "US123A", "trademark_serial": "71000001", "rejection_note": ""},
        {"patent_no": "US456A", "trademark_serial": 71000002,   "rejection_note": ""},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    result = read_rejected(p)
    assert ("US123A", "71000001") in result
    assert ("US456A", "71000002") in result


def test_read_rejected_handles_integer_serial(tmp_path: Path):
    p = tmp_path / "rejected.jsonl"
    p.write_text(json.dumps({"patent_no": "US789A", "trademark_serial": 71000003}) + "\n")
    result = read_rejected(p)
    assert ("US789A", "71000003") in result
