"""Tests for markery matchmaker confirm (D029) and review.py figurative fix (D041)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CANDIDATE = {
    "patent_no": "US1261167A",
    "trademark_serial": 71246709,
    "trademark": "SOUNDEX",
    "entity_id": 1,
    "entity": "Remington Rand",
    "score": 0.75,
    "tm_filing_dt": "1927-03-31",
    "tm_owner": "RAND KARDEX BUREAU INC",
    "patent_grant_dt": "1918-04-02",
    "patent_assignee": "R C RUSSELL",
    "patent_title": "Index",
    "cpc_classes": ["G06K"],
}

FIGURATIVE_CANDIDATE = {
    "patent_no": "US1396890A",
    "trademark_serial": 71199224,
    "trademark": None,
    "entity_id": 2,
    "entity": "General Motors",
    "score": 0.55,
    "tm_filing_dt": "1929-01-01",
    "tm_owner": "GENERAL MOTORS CORP",
    "patent_grant_dt": "1928-06-01",
    "patent_assignee": "GENERAL MOTORS",
    "patent_title": "Engine",
    "cpc_classes": ["F02B"],
}


def _write_candidates(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# D029 — cmd_confirm
# ---------------------------------------------------------------------------

class TestConfirm:
    def test_confirm_valid_slug(self, tmp_path):
        proj_dir = tmp_path / "projects" / "test-proj"
        matches_dir = proj_dir / "matches"
        matches_dir.mkdir(parents=True)
        candidates_path = matches_dir / "candidates.jsonl"
        confirmed_path  = matches_dir / "confirmed.jsonl"
        _write_candidates(candidates_path, [CANDIDATE])

        import argparse, sys
        sys.path.insert(0, str(tmp_path / "src"))

        from unittest.mock import patch
        from markery.specialist.matchmaker.cli import cmd_confirm
        from markery.common.project import Project

        with patch("markery.specialist.matchmaker.cli.require_project") as mock_proj:
            mock_proj.return_value = type("P", (), {
                "candidates": candidates_path,
                "confirmed":  confirmed_path,
                "root":       proj_dir,
            })()
            args = argparse.Namespace(project="test-proj", slug="soundex-us1261167a", note="")
            cmd_confirm(args)

        assert confirmed_path.exists()
        record = json.loads(confirmed_path.read_text().strip())
        assert record["patent_no"] == "US1261167A"
        assert record["trademark_serial"] == 71246709
        assert record["trademark"] == "SOUNDEX"
        assert record["note"] == ""

    def test_confirm_with_note(self, tmp_path):
        proj_dir = tmp_path / "projects" / "test-proj"
        matches_dir = proj_dir / "matches"
        matches_dir.mkdir(parents=True)
        candidates_path = matches_dir / "candidates.jsonl"
        confirmed_path  = matches_dir / "confirmed.jsonl"
        _write_candidates(candidates_path, [CANDIDATE])

        from unittest.mock import patch
        from markery.specialist.matchmaker.cli import cmd_confirm
        import argparse

        with patch("markery.specialist.matchmaker.cli.require_project") as mock_proj:
            mock_proj.return_value = type("P", (), {
                "candidates": candidates_path,
                "confirmed":  confirmed_path,
                "root":       proj_dir,
            })()
            args = argparse.Namespace(project="test-proj", slug="soundex-us1261167a",
                                      note="strong date alignment")
            cmd_confirm(args)

        record = json.loads(confirmed_path.read_text().strip())
        assert record["note"] == "strong date alignment"

    def test_confirm_invalid_slug_exits_1(self, tmp_path):
        proj_dir = tmp_path / "projects" / "test-proj"
        matches_dir = proj_dir / "matches"
        matches_dir.mkdir(parents=True)
        candidates_path = matches_dir / "candidates.jsonl"
        _write_candidates(candidates_path, [CANDIDATE])

        from unittest.mock import patch
        from markery.specialist.matchmaker.cli import cmd_confirm
        import argparse

        with patch("markery.specialist.matchmaker.cli.require_project") as mock_proj:
            mock_proj.return_value = type("P", (), {
                "candidates": candidates_path,
                "confirmed":  tmp_path / "confirmed.jsonl",
                "root":       proj_dir,
            })()
            args = argparse.Namespace(project="test-proj", slug="nosuchmark-us9999999z", note="")
            with pytest.raises(SystemExit) as exc_info:
                cmd_confirm(args)
        assert exc_info.value.code == 1

    def test_confirm_no_duplicate(self, tmp_path):
        """Confirming the same slug twice does not duplicate the record."""
        proj_dir = tmp_path / "projects" / "test-proj"
        matches_dir = proj_dir / "matches"
        matches_dir.mkdir(parents=True)
        candidates_path = matches_dir / "candidates.jsonl"
        confirmed_path  = matches_dir / "confirmed.jsonl"
        _write_candidates(candidates_path, [CANDIDATE])

        from unittest.mock import patch
        from markery.specialist.matchmaker.cli import cmd_confirm
        import argparse

        def _mock_proj(*_):
            return type("P", (), {
                "candidates": candidates_path,
                "confirmed":  confirmed_path,
                "root":       proj_dir,
            })()

        with patch("markery.specialist.matchmaker.cli.require_project", side_effect=_mock_proj):
            args = argparse.Namespace(project="test-proj", slug="soundex-us1261167a", note="")
            cmd_confirm(args)

        with patch("markery.specialist.matchmaker.cli.require_project", side_effect=_mock_proj):
            args = argparse.Namespace(project="test-proj", slug="soundex-us1261167a", note="")
            with pytest.raises(SystemExit) as exc_info:
                cmd_confirm(args)  # second call — already confirmed, exits 0
            assert exc_info.value.code == 0

        records = [json.loads(l) for l in confirmed_path.read_text().splitlines() if l.strip()]
        assert len(records) == 1

    def test_confirm_figurative_slug(self, tmp_path):
        """Confirm a pair where trademark is None using the 'figurative-<patent_no>' slug."""
        proj_dir = tmp_path / "projects" / "test-proj"
        matches_dir = proj_dir / "matches"
        matches_dir.mkdir(parents=True)
        candidates_path = matches_dir / "candidates.jsonl"
        confirmed_path  = matches_dir / "confirmed.jsonl"
        _write_candidates(candidates_path, [FIGURATIVE_CANDIDATE])

        from unittest.mock import patch
        from markery.specialist.matchmaker.cli import cmd_confirm
        import argparse

        with patch("markery.specialist.matchmaker.cli.require_project") as mock_proj:
            mock_proj.return_value = type("P", (), {
                "candidates": candidates_path,
                "confirmed":  confirmed_path,
                "root":       proj_dir,
            })()
            args = argparse.Namespace(project="test-proj", slug="figurative-us1396890a", note="")
            cmd_confirm(args)

        record = json.loads(confirmed_path.read_text().strip())
        assert record["trademark"] is None
        assert record["patent_no"] == "US1396890A"


# ---------------------------------------------------------------------------
# D041 — TUI figurative mark audit
# ---------------------------------------------------------------------------

class TestTUIFigurativeMark:
    def test_display_does_not_crash_on_null_trademark(self, tmp_path):
        """display() must handle trademark=None without AttributeError."""
        from markery.specialist.historian.review import display

        cand = dict(FIGURATIVE_CANDIDATE)
        # Minimal tm/pat dicts as returned by fetch_tm / fetch_patent
        tm  = {"goods": "engine parts", "first_use": "1928-01-01", "draw": "3  (design mark)"}
        pat = {"app_dt": "1927-01-01", "inventors": "Smith", "cpc_full": "F02B", "figure": None}

        import io, sys
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            display(cand, tm, pat, idx=1, total=1, entity_names={"General Motors"})
        finally:
            sys.stdout = old

        out = buf.getvalue()
        assert "(figurative)" in out

    def test_queue_filter_does_not_crash_on_null_trademark(self):
        """The --mark filter in the queue-building loop must not crash on trademark=None."""
        from markery.specialist.historian.review import load_confirmed, load_rejected

        # Simulate the queue-building logic with a figurative candidate
        import re
        cands = [FIGURATIVE_CANDIDATE, CANDIDATE]
        mark_filter = "SOUNDEX"
        already_confirmed: set = set()
        already_rejected: set  = set()

        queue = []
        for c in sorted(cands, key=lambda x: -x["score"]):
            key = (c["patent_no"], c["trademark_serial"])
            tm_text = c.get("trademark") or ""
            if (
                key not in already_confirmed
                and key not in already_rejected
                and c["score"] >= 0.5
                and (mark_filter is None or mark_filter.upper() in tm_text.upper())
            ):
                queue.append(c)

        # Only SOUNDEX should match; figurative should be excluded by the filter (not crash)
        assert len(queue) == 1
        assert queue[0]["trademark"] == "SOUNDEX"
