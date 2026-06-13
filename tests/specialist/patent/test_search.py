"""Tests for `markery patent search --assignee` (D066 local-DB assignee read)."""

from __future__ import annotations

import argparse
from unittest.mock import patch

from markery.specialist.patent.build import open_db, insert_patent
from markery.specialist.patent.cli import cmd_search


def _seed_db(path):
    conn = open_db(str(path))
    insert_patent(conn, {
        "patent_no": "US904137A", "title": "Steering Mechanism For Automobiles",
        "app_dt": "1907-01-01", "grant_dt": "1908-11-17",
        "abstract": "", "assignee_name": "JOHN M MACK", "cpc": ["B62D"], "inventors": [],
    })
    insert_patent(conn, {
        "patent_no": "US1A", "title": "Other",
        "app_dt": "1910-01-01", "grant_dt": "1910-01-01",
        "abstract": "", "assignee_name": "ACME CORP", "cpc": ["A01B"], "inventors": [],
    })
    conn.close()


class TestPatentSearch:
    def test_assignee_substring_match(self, tmp_path, capsys):
        db = tmp_path / "patents.duckdb"
        _seed_db(db)
        with patch.dict("markery.specialist.patent.cli.DB", {"patents": db}):
            cmd_search(argparse.Namespace(assignee="MACK", examples=0))
        out = capsys.readouterr().out
        assert "JOHN M MACK" in out
        assert "ACME CORP" not in out

    def test_examples_flag_lists_patents(self, tmp_path, capsys):
        db = tmp_path / "patents.duckdb"
        _seed_db(db)
        with patch.dict("markery.specialist.patent.cli.DB", {"patents": db}):
            cmd_search(argparse.Namespace(assignee="MACK", examples=2))
        out = capsys.readouterr().out
        assert "US904137A" in out
        assert "Steering Mechanism For Automobiles" in out

    def test_no_match_message(self, tmp_path, capsys):
        db = tmp_path / "patents.duckdb"
        _seed_db(db)
        with patch.dict("markery.specialist.patent.cli.DB", {"patents": db}):
            cmd_search(argparse.Namespace(assignee="ZZZNOPE", examples=0))
        out = capsys.readouterr().out
        assert "No assignees matching" in out
