"""Tests for the two-tier page chrome (global bar + project sub-header) and the
Markery root portal (Phase 26)."""

from __future__ import annotations

from pathlib import Path

from markery.specialist.publisher.render import _page, render_portal, render_root_search


# ── two-tier chrome ──────────────────────────────────────────────────────────

def test_root_page_has_global_bar_no_project_bar():
    html = _page("Markery Research", "<p>x</p>", {})
    assert 'class="global-bar"' in html
    assert 'class="project-bar"' not in html
    # Root page links resolve at the site root.
    assert 'class="site-title" href="index.html"' in html
    assert 'action="search.html"' in html


def test_project_page_has_both_bars_and_root_links_go_up():
    html = _page("Trademark Gallery", "<p>x</p>",
                 {"Trademarks": "trademarks.html"},
                 active="trademarks.html",
                 project="precision-tools", project_title="Precision Tools")
    assert 'class="global-bar"' in html
    assert 'class="project-bar"' in html
    assert "Precision Tools" in html
    # From a project page the global bar points up to the site root.
    assert 'class="site-title" href="../index.html"' in html
    assert 'action="../search.html"' in html
    # Project nav stays within the project and marks the active section.
    assert '<a href="trademarks.html" class="active" aria-current="page">' in html


def test_project_page_depth_adds_another_level_to_root():
    html = _page("Company", "<p>x</p>", {"Companies": "entities/index.html"},
                 depth=1, active="entities/index.html",
                 project="precision-tools", project_title="Precision Tools")
    assert 'class="site-title" href="../../index.html"' in html   # root, two up
    assert 'action="../../search.html"' in html
    assert '<a class="project-bar-title" href="../index.html">' in html  # project root, one up


# ── portal ───────────────────────────────────────────────────────────────────

def _project(slug, **kw):
    base = {
        "slug": slug, "title": slug.replace("-", " ").title(),
        "summary": f"Scope of {slug}.",
        "counts": {"companies": 4, "marks": 6, "patents": 30, "pairs": 3},
        "mark_src": None, "mark_label": "STARRETT",
        "fig_src": None, "fig_label": "Combination Square",
    }
    base.update(kw)
    return base


def test_portal_lists_projects_and_matches(tmp_path: Path):
    projects = [_project("precision-tools"), _project("radio-pioneers")]
    matches = [{
        "url": "precision-tools/matches/x.html", "label": "STARRETT",
        "patent_no": "US1525813A", "project_title": "Precision Tools",
        "entity": "L.S. Starrett", "note": "n", "thumb_src": None,
    }]
    p = render_portal(tmp_path, projects, matches)
    assert p == tmp_path / "index.html"
    html = p.read_text()
    assert "<h1>Markery Research</h1>" in html
    assert 'href="precision-tools/index.html"' in html
    assert 'href="radio-pioneers/index.html"' in html
    assert "Confirmed Pairs — All Projects" in html
    assert 'href="precision-tools/matches/x.html"' in html
    assert 'class="project-bar"' not in html   # portal has no project bar


def test_portal_card_shows_summary_and_counts(tmp_path: Path):
    html = render_portal(tmp_path, [_project("precision-tools")], []).read_text()
    assert "Scope of precision-tools." in html
    assert "30 patents" in html
    assert "STARRETT" in html               # representative mark label (placeholder)


def test_root_search_page(tmp_path: Path):
    p = render_root_search(tmp_path)
    assert p == tmp_path / "search.html"
    html = p.read_text()
    assert "All Markery projects" in html
    assert "search.json" in html            # client fetches the combined index
    assert 'class="project-bar"' not in html
