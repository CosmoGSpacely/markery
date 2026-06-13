"""Tests for `markery site check` — internal link / orphan validation (D063)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from markery.specialist.publisher.check import (
    check_site, run_check, _is_internal, _LinkExtractor,
)


# ── helpers ────────────────────────────────────────────────────────────────

def _patch_project(out: Path):
    """Patch load_project/Project so check_site uses `out` as the site dir."""
    fake = type("P", (), {"site": out})()
    return (
        patch("markery.specialist.publisher.check.load_project", return_value=fake),
        patch("markery.specialist.publisher.check.Project",
              return_value=type("PR", (), {"root": out.parent})()),
    )


def _build_site(out: Path, pages: dict[str, str], extra_files: list[str] = ()):
    out.mkdir(parents=True, exist_ok=True)
    for rel, html in pages.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
    for rel in extra_files:
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")


# ── unit: link classification ──────────────────────────────────────────────

class TestInternalClassification:
    def test_relative_is_internal(self):
        assert _is_internal("entities/index.html")
        assert _is_internal("../index.html")
        assert _is_internal("page.html#section")

    def test_external_not_internal(self):
        assert not _is_internal("https://example.com")
        assert not _is_internal("mailto:a@b.com")
        assert not _is_internal("data:image/png;base64,AAAA")

    def test_anchor_only_not_internal(self):
        assert not _is_internal("#top")
        assert not _is_internal("")

    def test_extractor_collects_href_and_src(self):
        ex = _LinkExtractor()
        ex.feed('<a href="a.html">x</a><img src="b.png"><link href="c.css">')
        assert ex.links == ["a.html", "b.png", "c.css"]


# ── check_site behaviour ───────────────────────────────────────────────────

class TestCheckSite:
    def test_all_links_resolve(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"
        _build_site(out, {
            "index.html": '<a href="entities/index.html">E</a><img src="images/m.png">',
            "entities/index.html": '<a href="../index.html">home</a>',
        }, extra_files=["images/m.png"])
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            report = check_site("p")
        assert report["broken"] == []
        assert report["pages"] == 2
        assert report["links_checked"] >= 3
        assert report["orphans"] == []

    def test_broken_link_detected(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"
        _build_site(out, {
            "index.html": '<a href="missing.html">gone</a>',
        })
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            report = check_site("p")
        assert len(report["broken"]) == 1
        assert report["broken"][0][1] == "missing.html"

    def test_orphan_detected(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"
        _build_site(out, {
            "index.html": '<a href="index.html">self</a>',
            "stale.html": "<p>nobody links here</p>",
        })
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            report = check_site("p")
        assert "stale.html" in report["orphans"]
        # index.html is an entry point, never an orphan
        assert "index.html" not in report["orphans"]

    def test_anchor_target_with_fragment_resolves(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"
        _build_site(out, {
            "index.html": '<a href="page.html#sec">x</a><a href="index.html">h</a>',
            "page.html": "<h2 id='sec'>S</h2>",
        })
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            report = check_site("p")
        assert report["broken"] == []

    def test_external_links_ignored(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"
        _build_site(out, {
            "index.html": '<a href="https://example.com/x">ext</a><a href="index.html">h</a>',
        })
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            report = check_site("p")
        assert report["broken"] == []


# ── run_check exit codes ───────────────────────────────────────────────────

class TestRunCheckExit:
    def test_clean_site_returns_0(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"
        _build_site(out, {"index.html": '<a href="index.html">h</a>'})
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            assert run_check("p") == 0

    def test_broken_returns_1(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"
        _build_site(out, {"index.html": '<a href="ghost.html">x</a>'})
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            assert run_check("p") == 1

    def test_orphan_only_fails_under_strict(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"
        _build_site(out, {
            "index.html": '<a href="index.html">h</a>',
            "stale.html": "<p>x</p>",
        })
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            assert run_check("p", strict=False) == 0
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            assert run_check("p", strict=True) == 1

    def test_missing_site_dir_returns_1(self, tmp_path):
        out = tmp_path / "projects" / "p" / "site"  # never created
        p_lp, p_pr = _patch_project(out)
        with p_lp, p_pr:
            assert run_check("p") == 1
