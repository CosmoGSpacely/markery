"""Unit tests for historian status helper functions."""

from __future__ import annotations

from pathlib import Path

from markery.specialist.historian.status import human_size, count_jsonl


def test_human_size_bytes(tmp_path: Path):
    f = tmp_path / "small.bin"
    f.write_bytes(b"x" * 500)
    assert human_size(f) == "500 B"


def test_human_size_kilobytes(tmp_path: Path):
    f = tmp_path / "medium.bin"
    f.write_bytes(b"x" * 2048)
    assert human_size(f) == "2 KB"


def test_count_jsonl_empty_when_missing(tmp_path: Path):
    assert count_jsonl(tmp_path / "no_such_file.jsonl") == 0


def test_count_jsonl_counts_nonempty_lines(tmp_path: Path):
    p = tmp_path / "data.jsonl"
    p.write_text('{"a": 1}\n{"b": 2}\n\n{"c": 3}\n')
    assert count_jsonl(p) == 3
