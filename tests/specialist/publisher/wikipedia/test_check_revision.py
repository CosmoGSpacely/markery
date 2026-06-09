"""Tests for markery wikipedia check-revision (Phase 21 P5)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import markery.common.config as cfg_mod
from markery.specialist.publisher.wikipedia import cli as wiki_cli


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_submissions(wiki_dir: Path, entries: list[dict]) -> Path:
    wiki_dir.mkdir(parents=True, exist_ok=True)
    path = wiki_dir / "submissions.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
    return path


def _live_status(revid: int = 1357391696) -> dict:
    return {"exists": True, "reverted": False,
            "tags": [], "timestamp": "2026-06-06T12:00:00Z"}


def _reverted_status(revid: int = 1357391696) -> dict:
    return {"exists": True, "reverted": True,
            "tags": ["mw-reverted"], "timestamp": "2026-06-06T12:00:00Z"}


def _unknown_status() -> dict:
    return {"exists": False, "reverted": False, "tags": [], "timestamp": ""}


def _run_check(tmp_path: Path, project: str = "test-proj") -> None:
    """Call cmd_check_revision with ROOT patched to tmp_path."""
    with patch.object(cfg_mod, "ROOT", tmp_path), \
         patch.object(wiki_cli, "ROOT", tmp_path):
        wiki_cli.cmd_check_revision(project)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCheckRevision:
    def _wiki_dir(self, tmp_path: Path, project: str = "test-proj") -> Path:
        return tmp_path / "projects" / project / "wikipedia"

    def test_exits_0_when_all_live(self, tmp_path, capsys):
        wiki_dir = self._wiki_dir(tmp_path)
        _write_submissions(wiki_dir, [
            {"revision_id": 111, "article": "Soundex",
             "submitted_at": "2026-06-06", "status": "live"},
        ])
        mock_client = MagicMock()
        mock_client.get_revision_status.return_value = _live_status(111)

        with patch("markery.specialist.publisher.wikipedia.api.WikipediaClient",
                   return_value=mock_client):
            _run_check(tmp_path)  # should not raise

        out = capsys.readouterr().out
        assert "live" in out
        assert "All checked revisions are live" in out

    def test_exits_1_when_any_reverted(self, tmp_path):
        wiki_dir = self._wiki_dir(tmp_path)
        _write_submissions(wiki_dir, [
            {"revision_id": 222, "article": "SOUNDEX",
             "submitted_at": "2026-06-06", "status": "live"},
        ])
        mock_client = MagicMock()
        mock_client.get_revision_status.return_value = _reverted_status(222)

        with patch("markery.specialist.publisher.wikipedia.api.WikipediaClient",
                   return_value=mock_client), \
             pytest.raises(SystemExit) as exc:
            _run_check(tmp_path)

        assert exc.value.code == 1

    def test_reverted_label_shown_in_output(self, tmp_path, capsys):
        wiki_dir = self._wiki_dir(tmp_path)
        _write_submissions(wiki_dir, [
            {"revision_id": 333, "article": "Library Bureau",
             "submitted_at": "2026-06-06", "status": "live"},
        ])
        mock_client = MagicMock()
        mock_client.get_revision_status.return_value = _reverted_status(333)

        with patch("markery.specialist.publisher.wikipedia.api.WikipediaClient",
                   return_value=mock_client), \
             pytest.raises(SystemExit):
            _run_check(tmp_path)

        out = capsys.readouterr().out
        assert "REVERTED" in out

    def test_updates_status_field_on_revert(self, tmp_path):
        wiki_dir = self._wiki_dir(tmp_path)
        path = _write_submissions(wiki_dir, [
            {"revision_id": 444, "article": "Soundex",
             "submitted_at": "2026-06-06", "status": "live"},
        ])
        mock_client = MagicMock()
        mock_client.get_revision_status.return_value = _reverted_status(444)

        with patch("markery.specialist.publisher.wikipedia.api.WikipediaClient",
                   return_value=mock_client), \
             pytest.raises(SystemExit):
            _run_check(tmp_path)

        updated = json.loads(path.read_text().strip())
        assert updated["status"] == "reverted"

    def test_does_not_update_file_when_all_live(self, tmp_path):
        wiki_dir = self._wiki_dir(tmp_path)
        original = [{"revision_id": 555, "article": "SOUNDEX",
                     "submitted_at": "2026-06-06", "status": "live"}]
        path = _write_submissions(wiki_dir, original)
        mtime_before = path.stat().st_mtime

        mock_client = MagicMock()
        mock_client.get_revision_status.return_value = _live_status(555)

        with patch("markery.specialist.publisher.wikipedia.api.WikipediaClient",
                   return_value=mock_client):
            _run_check(tmp_path)

        assert path.stat().st_mtime == mtime_before

    def test_unknown_revision_shown_as_unknown(self, tmp_path, capsys):
        wiki_dir = self._wiki_dir(tmp_path)
        _write_submissions(wiki_dir, [
            {"revision_id": 666, "article": "Rolodex",
             "submitted_at": "2026-06-06", "status": "live"},
        ])
        mock_client = MagicMock()
        mock_client.get_revision_status.return_value = _unknown_status()

        with patch("markery.specialist.publisher.wikipedia.api.WikipediaClient",
                   return_value=mock_client):
            _run_check(tmp_path)  # unknown ≠ reverted → exits 0

        out = capsys.readouterr().out
        assert "unknown" in out

    def test_skips_entries_without_revision_id(self, tmp_path, capsys):
        wiki_dir = self._wiki_dir(tmp_path)
        _write_submissions(wiki_dir, [
            {"revision_id": None, "article": "Rolodex",
             "submitted_at": "2026-06-06", "status": "live"},
            {"revision_id": 777, "article": "Soundex",
             "submitted_at": "2026-06-06", "status": "live"},
        ])
        mock_client = MagicMock()
        mock_client.get_revision_status.return_value = _live_status(777)

        with patch("markery.specialist.publisher.wikipedia.api.WikipediaClient",
                   return_value=mock_client):
            _run_check(tmp_path)

        # API called once (for revision 777), not twice
        assert mock_client.get_revision_status.call_count == 1

    def test_exits_1_when_submissions_missing(self, tmp_path):
        (tmp_path / "projects" / "test-proj").mkdir(parents=True)
        with pytest.raises(SystemExit) as exc:
            _run_check(tmp_path)
        assert exc.value.code == 1

    def test_mixed_live_and_reverted_exits_1(self, tmp_path, capsys):
        wiki_dir = self._wiki_dir(tmp_path)
        _write_submissions(wiki_dir, [
            {"revision_id": 888, "article": "Soundex",
             "submitted_at": "2026-06-06", "status": "live"},
            {"revision_id": 999, "article": "Rolodex",
             "submitted_at": "2026-06-06", "status": "live"},
        ])

        def _side_effect(revid):
            return _reverted_status(revid) if revid == 999 else _live_status(revid)

        mock_client = MagicMock()
        mock_client.get_revision_status.side_effect = _side_effect

        with patch("markery.specialist.publisher.wikipedia.api.WikipediaClient",
                   return_value=mock_client), \
             pytest.raises(SystemExit) as exc:
            _run_check(tmp_path)

        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "live" in out
        assert "REVERTED" in out


class TestGetRevisionStatus:
    """Unit tests for WikipediaClient.get_revision_status() response parsing."""

    def _make_client(self) -> "WikipediaClient":
        from markery.specialist.publisher.wikipedia.api import WikipediaClient
        client = WikipediaClient.__new__(WikipediaClient)
        client._session = MagicMock()
        client._logged_in = False
        return client

    def test_live_revision_returns_exists_true_reverted_false(self):
        client = self._make_client()
        client._session.get.return_value.json.return_value = {
            "query": {"pages": {"12345": {"revisions": [
                {"revid": 111, "timestamp": "2026-06-06T00:00:00Z", "tags": [], "comment": ""}
            ]}}}
        }
        result = client.get_revision_status(111)
        assert result["exists"] is True
        assert result["reverted"] is False
        assert result["timestamp"] == "2026-06-06T00:00:00Z"

    def test_reverted_tag_sets_reverted_true(self):
        client = self._make_client()
        client._session.get.return_value.json.return_value = {
            "query": {"pages": {"12345": {"revisions": [
                {"revid": 222, "timestamp": "2026-06-06T00:00:00Z",
                 "tags": ["mw-reverted"], "comment": ""}
            ]}}}
        }
        result = client.get_revision_status(222)
        assert result["reverted"] is True

    def test_bad_revid_returns_exists_false(self):
        client = self._make_client()
        client._session.get.return_value.json.return_value = {
            "query": {"badrevids": {"9999999": {"revid": 9999999}}}
        }
        result = client.get_revision_status(9999999)
        assert result["exists"] is False
        assert result["reverted"] is False
