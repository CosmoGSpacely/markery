"""Unit tests for historian review helper functions."""

from __future__ import annotations

import json
from pathlib import Path

from markery.specialist.historian.review import (
    wordwrap,
    load_confirmed,
    load_rejected,
    write_confirmed,
    write_rejected,
)


def test_wordwrap_short_text():
    result = wordwrap("hello world", 40)
    assert result == ["hello world"]


def test_wordwrap_long_text():
    text = "one two three four five six seven eight nine ten"
    result = wordwrap(text, 20)
    assert len(result) > 1
    for line in result:
        assert len(line) <= 20


def test_wordwrap_empty_text():
    assert wordwrap("", 40) == ["—"]


def test_load_confirmed_empty_when_missing(tmp_path: Path):
    assert load_confirmed(tmp_path / "no_such_file.jsonl") == set()


def test_load_confirmed_parses_jsonl(tmp_path: Path):
    p = tmp_path / "confirmed.jsonl"
    rows = [
        {"patent_no": "US123A", "trademark_serial": "71000001"},
        {"patent_no": "US456A", "trademark_serial": "71000002"},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    result = load_confirmed(p)
    assert len(result) == 2
    assert ("US123A", "71000001") in result
    assert ("US456A", "71000002") in result


def test_write_confirmed_appends(tmp_path: Path):
    p = tmp_path / "confirmed.jsonl"
    write_confirmed(p, {"patent_no": "US1A", "trademark_serial": "71000001"})
    write_confirmed(p, {"patent_no": "US2A", "trademark_serial": "71000002"})
    lines = [l for l in p.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0])["patent_no"] == "US1A"
    assert json.loads(lines[1])["patent_no"] == "US2A"


def test_write_confirmed_creates_parent_dir(tmp_path: Path):
    p = tmp_path / "deep" / "nested" / "confirmed.jsonl"
    write_confirmed(p, {"patent_no": "US1A", "trademark_serial": "71000001"})
    assert p.exists()


def test_load_rejected_empty_when_missing(tmp_path: Path):
    assert load_rejected(tmp_path / "no_such_file.jsonl") == set()


def test_load_rejected_parses_jsonl(tmp_path: Path):
    p = tmp_path / "rejected.jsonl"
    rows = [
        {"patent_no": "US123A", "trademark_serial": "71000001", "rejection_note": ""},
        {"patent_no": "US456A", "trademark_serial": "71000002", "rejection_note": "too old"},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    result = load_rejected(p)
    assert len(result) == 2
    assert ("US123A", "71000001") in result
    assert ("US456A", "71000002") in result


def test_write_rejected_appends(tmp_path: Path):
    p = tmp_path / "rejected.jsonl"
    write_rejected(p, {"patent_no": "US1A", "trademark_serial": "71000001", "rejection_note": ""})
    write_rejected(p, {"patent_no": "US2A", "trademark_serial": "71000002", "rejection_note": ""})
    lines = [l for l in p.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0])["patent_no"] == "US1A"


def test_write_rejected_creates_parent_dir(tmp_path: Path):
    p = tmp_path / "deep" / "nested" / "rejected.jsonl"
    write_rejected(p, {"patent_no": "US1A", "trademark_serial": "71000001", "rejection_note": ""})
    assert p.exists()
