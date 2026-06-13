"""Tests for build_site stale-output pruning (D064)."""

from __future__ import annotations

from pathlib import Path

from markery.specialist.publisher.build import _prune_stale


class TestPruneStale:
    def test_removes_unwritten_html(self, tmp_path):
        out = tmp_path / "site"
        (out / "matches").mkdir(parents=True)
        live = out / "matches" / "live.html"
        stale = out / "matches" / "stale.html"
        live.write_text("x")
        stale.write_text("x")
        written = {live.resolve()}
        removed = _prune_stale(out, written)
        assert stale in removed
        assert not stale.exists()
        assert live.exists()

    def test_removes_unwritten_images(self, tmp_path):
        out = tmp_path / "site"
        (out / "images" / "marks").mkdir(parents=True)
        live = out / "images" / "marks" / "111.png"
        stale = out / "images" / "marks" / "999.png"
        live.write_bytes(b"a")
        stale.write_bytes(b"b")
        written = {live.resolve()}
        removed = _prune_stale(out, written)
        assert stale in removed
        assert not stale.exists()
        assert live.exists()

    def test_leaves_pagefind_and_searchjson(self, tmp_path):
        out = tmp_path / "site"
        (out / "pagefind").mkdir(parents=True)
        pf = out / "pagefind" / "index.js"
        sj = out / "search.json"
        pf.write_text("x")
        sj.write_text("[]")
        removed = _prune_stale(out, set())
        # neither .html nor under images/ — untouched
        assert pf.exists()
        assert sj.exists()
        assert removed == []

    def test_nothing_removed_when_all_written(self, tmp_path):
        out = tmp_path / "site"
        out.mkdir()
        page = out / "index.html"
        page.write_text("x")
        removed = _prune_stale(out, {page.resolve()})
        assert removed == []
