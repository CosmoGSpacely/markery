"""Markery root portal: a landing page spanning all projects, plus a site-wide
search page. These live at the site root (site/index.html, site/search.html)
above the per-project nested sites.
"""
from __future__ import annotations

from pathlib import Path

from markery.specialist.publisher.render.components import _esc, _page
from markery.specialist.publisher.render.aux import _SEARCH_JS


def _thumb(src: str | None, label: str) -> str:
    if src:
        return f'<img class="portal-thumb" loading="lazy" src="{src}" alt="{_esc(label)}">'
    return f'<div class="portal-thumb portal-thumb--ph">{_esc(label)}</div>'


def render_portal(
    out_dir: Path,
    projects: list[dict],
    matches: list[dict],
    base_url: str | None = None,
) -> Path:
    """Render the root portal index.

    `projects`: dicts with slug, title, summary, counts{companies,marks,patents,pairs},
    mark_src/mark_label, fig_src/fig_label.
    `matches`: aggregated confirmed pairs with url, label, patent_no, project_title,
    entity, note, thumb_src.
    """
    cards = []
    for p in projects:
        c = p["counts"]
        cards.append(
            f'<div class="portal-card">'
            f'<h2 class="portal-title"><a href="{p["slug"]}/index.html">{_esc(p["title"])}</a></h2>'
            f'<div class="portal-thumbs">'
            f'{_thumb(p.get("mark_src"), p["mark_label"])}'
            f'{_thumb(p.get("fig_src"), p["fig_label"])}'
            f'</div>'
            f'<p class="portal-summary">{_esc(p["summary"])}</p>'
            f'<div class="portal-stats">'
            f'<span class="chip-sm">{c["companies"]} companies</span>'
            f'<span class="chip-sm">{c["marks"]} marks</span>'
            f'<span class="chip-sm">{c["patents"]} patents</span>'
            f'<span class="chip-sm">{c["pairs"]} pairs</span>'
            f'</div>'
            f'<a class="portal-enter" href="{p["slug"]}/index.html">Explore →</a>'
            f'</div>'
        )

    match_cards = []
    for m in matches:
        if m.get("thumb_src"):
            thumb = f'<img class="match-card-thumb" loading="lazy" src="{m["thumb_src"]}" alt="{_esc(m["label"])}">'
        else:
            thumb = f'<div class="match-card-thumb-placeholder">{_esc((m["label"] or "·")[:3])}</div>'
        match_cards.append(
            f'<div class="match-card">{thumb}'
            f'<div class="match-card-body">'
            f'<div class="match-card-title"><a href="{m["url"]}">'
            f'{_esc(m["label"])} ↔ {_esc(m["patent_no"])}</a></div>'
            f'<div class="match-card-meta">{_esc(m["project_title"])} · {_esc(m.get("entity", ""))}</div>'
            f'<div class="match-card-note">{_esc(m.get("note", ""))}</div>'
            f'</div></div>'
        )

    body = (
        '<div class="page-header">'
        '<h1>Markery Research</h1>'
        '<div class="subtitle">A cross-reference of U.S. trademarks and patents · 1900–1939</div>'
        '</div>'
        '<div class="page-body">'
        '<p class="section-title">Projects</p>'
        f'<div class="portal-grid">{"".join(cards)}</div>'
        + ('<p class="section-title">Confirmed Pairs — All Projects</p>'
           f'<div class="match-cards">{"".join(match_cards)}</div>' if match_cards else '')
        + '</div>'
    )

    og = {
        "title": "Markery Research",
        "description": "A cross-reference of U.S. trademarks and patents, 1900–1939.",
        "url": f"{base_url.rstrip('/')}/index.html" if base_url else "",
    } if base_url else None
    out_path = out_dir / "index.html"
    out_path.write_text(_page("Markery Research", body, {}, og=og), encoding="utf-8")
    return out_path


def render_root_search(out_dir: Path) -> Path:
    """Render the site-wide search page (searches the combined root search.json)."""
    body = (
        '<div class="page-header"><h1>Search</h1>'
        '<div class="subtitle">All Markery projects</div></div>'
        '<div class="page-body"><div class="search-form">'
        '<input type="search" id="q" placeholder="Search all projects…" autofocus>'
        '<button id="search-btn">Search</button></div>'
        '<ul class="search-results" id="results"></ul>'
        f'<script>{_SEARCH_JS}</script></div>'
    )
    out_path = out_dir / "search.html"
    out_path.write_text(_page("Search — Markery", body, {}), encoding="utf-8")
    return out_path
