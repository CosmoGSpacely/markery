"""Auxiliary pages: sources, timeline, search."""
from __future__ import annotations

from pathlib import Path
from markery.common.project import Project
from markery.specialist.publisher.render.components import (
    _esc, _page, _nav_links, _render_markdown,
    _page_title, _strip_frontmatter, _timeline_svg,
)


def render_sources_page(
    project: str,
    out_dir: Path,
    entities: list[dict],
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
) -> Path:
    """Render content/sources.md → sources.html."""
    proj = Project(project)
    src  = proj.content / "sources.md"
    nav  = _nav_links(project, entities, extra_nav)

    raw = _strip_frontmatter(src.read_text()) if src.exists() else ""
    content_html = _render_markdown(raw, link_index=link_index, depth=0) if raw else (
        '<p style="color:#999;font-style:italic">Sources page not yet written.</p>'
    )

    body = (
        f'<div class="page-header">'
        f'<h1>Sources</h1>'
        f'<div class="subtitle">{_esc(project.replace("-", " ").title())} · Primary and secondary sources</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="narrative">{content_html}</div>'
        f'</div>'
    )

    og = {
        "title": "Sources",
        "description": f"Primary and secondary sources for the {project.replace('-', ' ').title()} project",
        "url": f"{base_url}/{project}/sources.html",
    } if base_url else None
    out_path = out_dir / "sources.html"
    out_path.write_text(_page(_page_title("Sources", project), body, nav, project=project, project_title=project.replace('-', ' ').title(), og=og), encoding="utf-8")
    return out_path


def render_timeline_page(
    project: str,
    out_dir: Path,
    entities: list[dict],
    patents: list[dict],
    trademarks: list[dict],
    entity_colors: dict[int, str],
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
) -> Path:
    """Render content/timeline.md → timeline.html with combined patent+trademark SVG."""
    proj = Project(project)
    src  = proj.content / "timeline.md"
    nav  = _nav_links(project, entities, extra_nav)

    raw = _strip_frontmatter(src.read_text()) if src.exists() else ""

    preamble_html = ""
    entries_html  = ""
    if raw:
        lines = raw.split("\n")
        preamble_lines: list[str] = []
        found_first_entry = False
        for line in lines:
            if line.startswith("### "):
                found_first_entry = True
            if not found_first_entry:
                preamble_lines.append(line)
        preamble_text = "\n".join(preamble_lines).strip()
        if preamble_text:
            preamble_html = _render_markdown(preamble_text, link_index=link_index, depth=0)
        entries_html = (
            f'<div class="timeline-entries">'
            + _render_markdown(raw, link_index=link_index, depth=0)
            + '</div>'
        )

    pat_svg  = _timeline_svg(patents,    "grant_dt",  "title",     "entity_id", entity_colors)
    tm_svg   = _timeline_svg(trademarks, "filing_dt", "mark_name", "entity_id", entity_colors)

    body = (
        f'<div class="page-header">'
        f'<h1>Timeline</h1>'
        f'<div class="subtitle">{_esc(project.replace("-", " ").title())} · Patent grants and trademark filings</div>'
        f'</div>'
        f'<div class="page-body">'
        + (f'<div class="narrative">{preamble_html}</div>' if preamble_html else '')
        + f'<div class="timeline-section">'
        f'<p class="section-title">Patent Grants</p>{pat_svg}'
        f'<p class="section-title" style="margin-top:16px">Trademark Filings</p>{tm_svg}'
        f'</div>'
        + entries_html
        + f'</div>'
    )

    og = {
        "title": "Timeline",
        "description": f"Chronological arc of patents and trademarks in the {project.replace('-', ' ').title()} project",
        "url": f"{base_url}/{project}/timeline.html",
    } if base_url else None
    out_path = out_dir / "timeline.html"
    out_path.write_text(_page(_page_title("Timeline", project), body, nav, project=project, project_title=project.replace('-', ' ').title(), og=og), encoding="utf-8")
    return out_path


_SEARCH_JS = r"""
(function () {
  var idx = null;
  function load(cb) {
    if (idx !== null) { cb(); return; }
    fetch('search.json').then(function(r){ return r.json(); }).then(function(data){
      idx = data;
      cb();
    }).catch(function(){ idx = []; cb(); });
  }
  function run(q) {
    q = q.toLowerCase().trim();
    var ul = document.getElementById('results');
    ul.innerHTML = '';
    if (!q) return;
    var hits = idx.filter(function(p){
      return (p.title + ' ' + p.excerpt).toLowerCase().indexOf(q) !== -1;
    });
    if (!hits.length) {
      ul.innerHTML = '<li>No results.</li>';
      return;
    }
    hits.forEach(function(p) {
      var li = document.createElement('li');
      li.innerHTML = '<div class="result-title"><a href="' + p.url + '">' +
        p.title.replace(/</g,'&lt;') + '</a><span class="result-type">' +
        p.type + '</span></div><div class="result-excerpt">' +
        p.excerpt.replace(/</g,'&lt;').substring(0,180) + '…</div>';
      ul.appendChild(li);
    });
  }
  document.addEventListener('DOMContentLoaded', function() {
    var input = document.getElementById('q');
    var btn   = document.getElementById('search-btn');
    var params = new URLSearchParams(window.location.search);
    var initial = params.get('q') || '';
    if (initial) { input.value = initial; load(function(){ run(initial); }); }
    btn.addEventListener('click', function(){ load(function(){ run(input.value); }); });
    input.addEventListener('keydown', function(e){
      if (e.key === 'Enter') { load(function(){ run(input.value); }); }
    });
  });
})();
"""


def render_search_page(
    project: str,
    out_dir: Path,
    entities: list[dict],
    extra_nav: dict[str, str] | None = None,
) -> Path:
    """Render a client-side search page backed by search.json."""
    nav  = _nav_links(project, entities, extra_nav)

    body = (
        f'<div class="page-header">'
        f'<h1>Search</h1>'
        f'<div class="subtitle">{_esc(project.replace("-", " ").title())}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="search-form">'
        f'<input type="search" id="q" placeholder="Search marks, patents, essays…" autofocus>'
        f'<button id="search-btn">Search</button>'
        f'</div>'
        f'<ul class="search-results" id="results"></ul>'
        f'<script>{_SEARCH_JS}</script>'
        f'</div>'
    )

    out_path = out_dir / "search.html"
    out_path.write_text(_page(_page_title("Search", project), body, nav, project=project, project_title=project.replace('-', ' ').title()), encoding="utf-8")
    return out_path
