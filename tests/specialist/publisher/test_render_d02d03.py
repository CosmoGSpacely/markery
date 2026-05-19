"""Tests for D002 (_img_src) and D003 ([[figure:]] in _render_markdown)."""

from __future__ import annotations

from pathlib import Path

from markery.specialist.publisher.render import _img_src, _render_markdown


# ---------------------------------------------------------------------------
# D002: _img_src
# ---------------------------------------------------------------------------

def test_img_src_returns_relative_path_when_file_exists(tmp_path):
    images_dir = tmp_path / "images"
    (images_dir / "marks").mkdir(parents=True)
    (images_dir / "marks" / "71000001.png").write_bytes(b"\x89PNG")

    src = _img_src("mark", "71000001", depth=0, images_dir=images_dir)
    assert src == "images/marks/71000001.png"


def test_img_src_depth_prefix(tmp_path):
    images_dir = tmp_path / "images"
    (images_dir / "patents").mkdir(parents=True)
    (images_dir / "patents" / "US1234A.png").write_bytes(b"\x89PNG")

    src = _img_src("patent", "US1234A", depth=1, images_dir=images_dir)
    assert src == "../images/patents/US1234A.png"


def test_img_src_returns_none_when_no_file_and_no_db(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    # No file on disk, no DB available → None
    src = _img_src("mark", "00000000", depth=0, images_dir=images_dir)
    assert src is None


def test_img_src_returns_none_without_images_dir():
    # No images_dir, no DB file → None (DB["trademarks"] won't exist in test env)
    src = _img_src("mark", "00000000", depth=0, images_dir=None)
    assert src is None


# ---------------------------------------------------------------------------
# D003: [[figure:patent_no]] in _render_markdown
# ---------------------------------------------------------------------------

def test_render_figure_link_with_index():
    figure_index = {"US1234A": "images/patents/US1234A.png"}
    html = _render_markdown("[[figure:US1234A]]", figure_index=figure_index, depth=0)
    assert 'class="patent-figure"' in html
    assert 'src="images/patents/US1234A.png"' in html
    assert "US1234A" in html


def test_render_figure_link_with_depth():
    figure_index = {"US1234A": "images/patents/US1234A.png"}
    html = _render_markdown("[[figure:US1234A]]", figure_index=figure_index, depth=1)
    assert 'src="../images/patents/US1234A.png"' in html


def test_render_figure_link_fallback_when_not_in_index():
    figure_index: dict[str, str] = {}
    html = _render_markdown("[[figure:US9999A]]", figure_index=figure_index, depth=0)
    assert "US9999A" in html
    assert 'class="patent-figure"' not in html


def test_render_figure_link_ignored_without_figure_index():
    html = _render_markdown("[[figure:US1234A]]", figure_index=None, depth=0)
    # Without figure_index: treated as a plain [[...]] cross-link (no link_index match → escaped)
    assert "US1234A" in html
    assert 'class="patent-figure"' not in html


def test_render_figure_and_regular_link_coexist():
    figure_index = {"US1234A": "images/patents/US1234A.png"}
    link_index   = {"some-entity": "entities/some-entity.html"}
    text = "See [[Some Entity]] and [[figure:US1234A]] for details."
    html = _render_markdown(text, link_index=link_index, figure_index=figure_index, depth=0)
    assert 'href="entities/some-entity.html"' in html
    assert 'class="patent-figure"' in html
