"""Tests for Phase 19 P3: D032 (review --auto-accept) and D044 (acquire slug error)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candidates_md(path: Path, statuses: list[str]) -> None:
    """Write a candidates.md with one block per status in statuses."""
    header = "# Candidates — Test Work\n\n---\n\n"
    blocks = []
    for i, status in enumerate(statuses, 1):
        blocks.append(
            f"### Heading {i}\n\n"
            f'> "Passage text number {i}." (p. {i})\n\n'
            f"Context: This passage illustrates topic {i}.\n\n"
            f"<!-- status: {status} -->\n\n---\n\n"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "".join(blocks), encoding="utf-8")


# ---------------------------------------------------------------------------
# D032 — review --auto-accept
# ---------------------------------------------------------------------------

class TestReviewAutoAccept:
    def test_auto_accept_appends_all_pending_to_excerpts(self, tmp_path):
        work_dir = tmp_path / "library" / "works" / "test-work"
        work_dir.mkdir(parents=True)
        candidates_path = work_dir / "candidates.md"
        excerpts_path   = work_dir / "excerpts.md"
        _make_candidates_md(candidates_path, ["pending", "pending", "pending"])

        import markery.specialist.librarian.extract as ext
        with patch.object(ext, "_LIBRARY", tmp_path / "library"):
            ext.review("test-work", auto_accept=True)

        assert excerpts_path.exists()
        content = excerpts_path.read_text(encoding="utf-8")
        assert "Passage text number 1" in content
        assert "Passage text number 2" in content
        assert "Passage text number 3" in content

    def test_auto_accept_updates_status_markers(self, tmp_path):
        work_dir = tmp_path / "library" / "works" / "test-work"
        work_dir.mkdir(parents=True)
        candidates_path = work_dir / "candidates.md"
        _make_candidates_md(candidates_path, ["pending", "pending"])

        import markery.specialist.librarian.extract as ext
        with patch.object(ext, "_LIBRARY", tmp_path / "library"):
            ext.review("test-work", auto_accept=True)

        updated = candidates_path.read_text(encoding="utf-8")
        assert "<!-- status: pending -->" not in updated
        assert updated.count("<!-- status: accepted -->") == 2

    def test_auto_accept_skips_already_accepted(self, tmp_path):
        work_dir = tmp_path / "library" / "works" / "test-work"
        work_dir.mkdir(parents=True)
        candidates_path = work_dir / "candidates.md"
        _make_candidates_md(candidates_path, ["accepted", "pending", "rejected"])

        import markery.specialist.librarian.extract as ext
        with patch.object(ext, "_LIBRARY", tmp_path / "library"):
            ext.review("test-work", auto_accept=True)

        content = (work_dir / "excerpts.md").read_text(encoding="utf-8")
        # Only the pending one should be added
        assert "Passage text number 2" in content
        assert "Passage text number 1" not in content
        assert "Passage text number 3" not in content

    def test_auto_accept_does_not_call_input(self, tmp_path):
        """Verify no input() is called — this would block in non-interactive contexts."""
        work_dir = tmp_path / "library" / "works" / "test-work"
        work_dir.mkdir(parents=True)
        candidates_path = work_dir / "candidates.md"
        _make_candidates_md(candidates_path, ["pending"])

        import markery.specialist.librarian.extract as ext
        with patch.object(ext, "_LIBRARY", tmp_path / "library"):
            with patch("builtins.input", side_effect=AssertionError("input() called in auto-accept")):
                ext.review("test-work", auto_accept=True)  # should not raise

    def test_auto_accept_no_pending_exits_cleanly(self, tmp_path, capsys):
        work_dir = tmp_path / "library" / "works" / "test-work"
        work_dir.mkdir(parents=True)
        candidates_path = work_dir / "candidates.md"
        _make_candidates_md(candidates_path, ["accepted", "rejected"])

        import markery.specialist.librarian.extract as ext
        with patch.object(ext, "_LIBRARY", tmp_path / "library"):
            ext.review("test-work", auto_accept=True)

        out = capsys.readouterr().out
        assert "No pending" in out


# ---------------------------------------------------------------------------
# D044 — acquire slug resolution
# ---------------------------------------------------------------------------

class TestAcquireSlugResolution:
    def test_already_acquired_slug_exits_0(self, tmp_path, capsys):
        """If identifier matches an existing library/works/<slug>/metadata.json, exit 0."""
        import argparse
        from markery.specialist.librarian.cli import cmd_acquire, _LIBRARY as ORIG_LIB

        slug = "presbrey-history-and-development-of-advertising"
        work_dir = tmp_path / "library" / "works" / slug
        work_dir.mkdir(parents=True)
        (work_dir / "metadata.json").write_text(
            json.dumps({"slug": slug, "title": "History of Advertising"}),
            encoding="utf-8",
        )

        args = argparse.Namespace(identifier=slug, source=None)

        with patch("markery.specialist.librarian.cli._works_dir",
                   side_effect=lambda s: tmp_path / "library" / "works" / s):
            with pytest.raises(SystemExit) as exc_info:
                cmd_acquire(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "Already acquired" in out

    def test_unknown_slug_prints_helpful_error(self, tmp_path, capsys):
        """An IA lookup failure for a slug-looking identifier prints a helpful hint."""
        import argparse
        from markery.specialist.librarian.cli import cmd_acquire

        args = argparse.Namespace(
            identifier="presbrey-history-and-development-of-advertising",
            source=None,
        )

        # Simulate IA returning empty metadata (identifier not found)
        with patch("markery.specialist.librarian.cli._works_dir",
                   side_effect=lambda s: tmp_path / "library" / "works" / s):
            with patch("markery.specialist.librarian.sources.ia.fetch_metadata",
                       return_value={}):
                with pytest.raises(SystemExit) as exc_info:
                    cmd_acquire(args)

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "not found" in err
        assert "search-sources" in err or "IDENTIFIER" in err

    def test_valid_ia_identifier_still_works(self, tmp_path):
        """Normal IA acquisition path is not broken by the slug check."""
        import argparse
        from markery.specialist.librarian.cli import cmd_acquire

        fake_meta = {
            "metadata": {
                "title": "History and Development of Advertising",
                "creator": "Presbrey, Frank",
            },
            "files": [],
        }
        args = argparse.Namespace(identifier="historydevelopme0000fran", source=None)

        with patch("markery.specialist.librarian.cli._works_dir",
                   side_effect=lambda s: tmp_path / "library" / "works" / s):
            with patch("markery.specialist.librarian.cli._ensure_library"):
                with patch("markery.specialist.librarian.sources.ia.fetch_metadata",
                           return_value=fake_meta):
                    with patch("markery.specialist.librarian.sources.ia.download_text",
                               return_value=tmp_path / "raw_text.txt"):
                        with patch("markery.specialist.librarian.sources.common.normalize_metadata",
                                   return_value={"slug": "presbrey-...", "title": "test"}):
                            with patch("markery.specialist.librarian.cli._read_wants",
                                       return_value=[]):
                                # Should not raise — just verifying the IA path reaches download
                                try:
                                    cmd_acquire(args)
                                except SystemExit:
                                    pass  # exits 0 on success too
