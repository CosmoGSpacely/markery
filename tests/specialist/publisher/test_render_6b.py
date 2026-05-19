"""Tests for Phase 6B render additions: cross-links, new page types, search."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from markery.specialist.publisher.render import (
    _render_markdown,
    _strip_frontmatter,
    _text_excerpt,
    _parse_site_mode,
    build_link_index,
    render_thematic_essay,
    render_sources_page,
    render_timeline_page,
    render_search_page,
)
from markery.common.config import Project


# ---------------------------------------------------------------------------
# _strip_frontmatter
# ---------------------------------------------------------------------------

def test_strip_frontmatter_removes_yaml_block():
    text = "---\nkey: value\n---\n\nBody text."
    assert _strip_frontmatter(text) == "Body text."


def test_strip_frontmatter_noop_without_markers():
    text = "Just plain text."
    assert _strip_frontmatter(text) == "Just plain text."


def test_strip_frontmatter_noop_single_dash():
    text = "---\nOnly one marker."
    assert _strip_frontmatter(text) == "---\nOnly one marker."


# ---------------------------------------------------------------------------
# _render_markdown cross-links
# ---------------------------------------------------------------------------

_LINK_INDEX = {
    "soundex":         "matches/soundex.html",
    "remington-rand":  "entities/remington-rand.html",
    "card-index":      "themes/card-index.html",
}


def test_render_markdown_crosslink_resolves():
    result = _render_markdown("See [[SOUNDEX]] for details.", link_index=_LINK_INDEX)
    assert 'href="matches/soundex.html"' in result
    assert ">SOUNDEX<" in result


def test_render_markdown_crosslink_depth_1():
    result = _render_markdown("See [[SOUNDEX]].", link_index=_LINK_INDEX, depth=1)
    assert 'href="../matches/soundex.html"' in result


def test_render_markdown_crosslink_depth_0_no_prefix():
    result = _render_markdown("See [[SOUNDEX]].", link_index=_LINK_INDEX, depth=0)
    assert 'href="matches/soundex.html"' in result


def test_render_markdown_crosslink_unknown_slug_plain_text():
    result = _render_markdown("See [[UNKNOWN]].", link_index=_LINK_INDEX)
    assert "<a " not in result
    assert "UNKNOWN" in result


def test_render_markdown_crosslink_no_index_no_links():
    result = _render_markdown("See [[SOUNDEX]].", link_index=None)
    assert "<a " not in result
    assert "[[SOUNDEX]]" in result


def test_render_markdown_crosslink_inside_paragraph():
    result = _render_markdown(
        "The [[Remington Rand]] company filed many patents.",
        link_index=_LINK_INDEX,
        depth=0,
    )
    assert 'href="entities/remington-rand.html"' in result
    assert "company filed many patents" in result


def test_render_markdown_crosslink_does_not_affect_code_blocks():
    md = "```\n[[SOUNDEX]] in a code block\n```"
    result = _render_markdown(md, link_index=_LINK_INDEX)
    # Code block content should be escaped, not linked
    assert 'href=' not in result


# ---------------------------------------------------------------------------
# _parse_site_mode
# ---------------------------------------------------------------------------

def test_parse_site_mode_reads_from_objectives(tmp_path):
    import markery.common.config as cfg
    proj_dir = tmp_path / "projects" / "test"
    proj_dir.mkdir(parents=True)
    (proj_dir / "OBJECTIVES.md").write_text("---\nsite_mode: metrics\n---\n")
    with patch.object(cfg, "ROOT", tmp_path):
        proj = Project("test")
        assert _parse_site_mode(proj) == "metrics"


def test_parse_site_mode_default_when_missing(tmp_path):
    import markery.common.config as cfg
    proj_dir = tmp_path / "projects" / "test"
    proj_dir.mkdir(parents=True)
    with patch.object(cfg, "ROOT", tmp_path):
        proj = Project("test")
        assert _parse_site_mode(proj) == "narrative"


# ---------------------------------------------------------------------------
# build_link_index
# ---------------------------------------------------------------------------

def test_build_link_index_entities():
    entities = [{"slug": "remington-rand", "canonical_name": "Remington Rand"}]
    idx = build_link_index(entities, [], [])
    assert idx["remington-rand"] == "entities/remington-rand.html"


def test_build_link_index_matches():
    matches = [{"slug": "soundex", "trademark": "SOUNDEX"}]
    idx = build_link_index([], matches, [])
    assert idx["soundex"] == "matches/soundex.html"


def test_build_link_index_themes():
    idx = build_link_index([], [], ["card-index"])
    assert idx["card-index"] == "themes/card-index.html"


def test_build_link_index_all_combined():
    entities = [{"slug": "wilson-jones"}]
    matches  = [{"slug": "vi-dex"}]
    themes   = ["card-index"]
    idx = build_link_index(entities, matches, themes)
    assert "wilson-jones" in idx
    assert "vi-dex" in idx
    assert "card-index" in idx


def test_build_link_index_match_without_slug():
    matches = [{"trademark": "SOUNDEX"}]  # no slug key
    idx = build_link_index([], matches, [])
    assert idx == {}


# ---------------------------------------------------------------------------
# _text_excerpt
# ---------------------------------------------------------------------------

def test_text_excerpt_strips_markdown(tmp_path):
    p = tmp_path / "essay.md"
    p.write_text("## Heading\n\n**Bold** and `code` text here.")
    excerpt = _text_excerpt(p)
    assert "##" not in excerpt
    assert "**" not in excerpt
    assert "`" not in excerpt
    assert "Bold" in excerpt
    assert "code" in excerpt


def test_text_excerpt_strips_frontmatter(tmp_path):
    p = tmp_path / "essay.md"
    p.write_text("---\nkey: value\n---\n\nActual content here.")
    excerpt = _text_excerpt(p)
    assert "key" not in excerpt
    assert "Actual content" in excerpt


def test_text_excerpt_missing_file(tmp_path):
    p = tmp_path / "nonexistent.md"
    assert _text_excerpt(p) == ""


def test_text_excerpt_truncates(tmp_path):
    p = tmp_path / "long.md"
    p.write_text("word " * 200)
    assert len(_text_excerpt(p, max_chars=50)) <= 50


# ---------------------------------------------------------------------------
# render_thematic_essay
# ---------------------------------------------------------------------------

def _make_proj(tmp_path, name="test"):
    d = tmp_path / "projects" / name
    (d / "content").mkdir(parents=True)
    (d / "site" / "themes").mkdir(parents=True)
    return d


def test_render_thematic_essay_creates_file(tmp_path):
    import markery.common.config as cfg
    _make_proj(tmp_path)
    (tmp_path / "projects" / "test" / "content" / "theme-card-index.md").write_text(
        "# The Card Index\n\nA thematic essay about card indexes."
    )
    out = tmp_path / "site"
    out.mkdir(exist_ok=True)
    (out / "themes").mkdir(exist_ok=True)
    with patch.object(cfg, "ROOT", tmp_path):
        from markery.specialist.publisher.queries import get_mark_image_b64, get_patent_figure_b64
        path = render_thematic_essay("test", "card-index", out, entities=[])
    assert path.exists()
    content = path.read_text()
    assert "card-index" in path.name
    assert "The Card Index" in content
    assert "thematic essay" in content.lower()


def test_render_thematic_essay_placeholder_when_no_file(tmp_path):
    import markery.common.config as cfg
    _make_proj(tmp_path)
    out = tmp_path / "site"
    out.mkdir(exist_ok=True)
    (out / "themes").mkdir(exist_ok=True)
    with patch.object(cfg, "ROOT", tmp_path):
        path = render_thematic_essay("test", "missing-essay", out, entities=[])
    assert path.exists()
    assert "not yet written" in path.read_text()


# ---------------------------------------------------------------------------
# render_sources_page
# ---------------------------------------------------------------------------

def test_render_sources_page_creates_file(tmp_path):
    import markery.common.config as cfg
    _make_proj(tmp_path)
    (tmp_path / "projects" / "test" / "content" / "sources.md").write_text(
        "## Primary Sources\n\nUSPTO filings."
    )
    out = tmp_path / "site"
    out.mkdir(exist_ok=True)
    with patch.object(cfg, "ROOT", tmp_path):
        path = render_sources_page("test", out, entities=[])
    assert path.name == "sources.html"
    assert "Primary Sources" in path.read_text()


def test_render_sources_page_placeholder_when_missing(tmp_path):
    import markery.common.config as cfg
    _make_proj(tmp_path)
    out = tmp_path / "site"
    out.mkdir(exist_ok=True)
    with patch.object(cfg, "ROOT", tmp_path):
        path = render_sources_page("test", out, entities=[])
    assert "not yet written" in path.read_text()


# ---------------------------------------------------------------------------
# render_timeline_page
# ---------------------------------------------------------------------------

def test_render_timeline_page_creates_file(tmp_path):
    import markery.common.config as cfg
    _make_proj(tmp_path)
    (tmp_path / "projects" / "test" / "content" / "timeline.md").write_text(
        "This project spans 1910–1935.\n\n### 1918\n\n**Russell patents Soundex.**"
    )
    out = tmp_path / "site"
    out.mkdir(exist_ok=True)
    with patch.object(cfg, "ROOT", tmp_path):
        path = render_timeline_page(
            "test", out, entities=[], patents=[], trademarks=[], entity_colors={}
        )
    assert path.name == "timeline.html"
    html = path.read_text()
    assert "1918" in html
    assert "Russell" in html


def test_render_timeline_page_placeholder_when_missing(tmp_path):
    import markery.common.config as cfg
    _make_proj(tmp_path)
    out = tmp_path / "site"
    out.mkdir(exist_ok=True)
    with patch.object(cfg, "ROOT", tmp_path):
        path = render_timeline_page(
            "test", out, entities=[], patents=[], trademarks=[], entity_colors={}
        )
    assert path.name == "timeline.html"


# ---------------------------------------------------------------------------
# render_search_page
# ---------------------------------------------------------------------------

def test_render_search_page_creates_file(tmp_path):
    import markery.common.config as cfg
    out = tmp_path / "site"
    out.mkdir()
    path = render_search_page("test", out, entities=[])
    assert path.name == "search.html"
    html = path.read_text()
    assert "search.json" in html
    assert "search-results" in html


def test_render_search_page_has_query_input(tmp_path):
    out = tmp_path / "site"
    out.mkdir()
    path = render_search_page("test", out, entities=[])
    assert 'id="q"' in path.read_text()
