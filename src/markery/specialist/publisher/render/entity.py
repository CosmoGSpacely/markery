"""Entity profile page."""
from __future__ import annotations

from pathlib import Path
from markery.common.project import Project
from markery.specialist.publisher.render.components import (
    _esc, _page, _nav_links, _read_narrative,
    _page_title, _breadcrumb, _year_from_dt,
)


def render_entity_page(
    project: str,
    entity: dict,
    entities: list[dict],
    trademarks: list[dict],
    patents: list[dict],
    matches: list[dict],
    stats: dict,
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
    media_index: dict[str, dict] | None = None,
) -> Path:
    slug = entity["slug"]
    narrative = _read_narrative(Project(project).content / f"entity-{slug}.md",
                                link_index=link_index, depth=1, media_index=media_index)
    nav = _nav_links(project, entities, extra_nav)

    variants_rows = "".join(
        f'<tr><td>{_esc(v["name"])}</td><td>{_esc(v["source"])}</td></tr>'
        for v in entity.get("name_variants", [])
    )
    variants_table = (
        f'<table><thead><tr><th>Name variant</th><th>Source</th></tr></thead>'
        f'<tbody>{variants_rows}</tbody></table>'
    ) if variants_rows else ""

    def _gap_chip(m: dict) -> str:
        fy = _year_from_dt(m.get("filing_dt"))
        gy = _year_from_dt(m.get("grant_dt"))
        if fy and gy:
            return f' <span class="chip-sm">{abs(gy - fy)} yr gap</span>'
        return ""

    match_links = "".join(
        f'<li>'
        f'<a href="../matches/{m["slug"]}.html">'
        f'{_esc(m.get("trademark") or "(figurative)")} ↔ {_esc(m["patent_no"])}</a>'
        f'{_gap_chip(m)}'
        f'</li>'
        for m in matches if m.get("essay_path")
    )
    match_section = (
        f'<h2>Confirmed Pairs</h2><ul>{match_links}</ul>'
        if match_links else
        f'<h2>Confirmed Pairs</h2><p>No confirmed pairs yet.</p>'
    )

    stat_chips = (
        f'<span class="chip">{stats.get("trademark_count", 0)} marks</span>'
        f'<span class="chip">{stats.get("patent_count", 0)} patents</span>'
        f'<span class="chip">{stats.get("match_count", 0)} confirmed</span>'
        + (f'<span class="chip">{stats["active_from"]}–{stats["active_to"]}</span>'
           if stats.get("active_from") else '')
    )

    breadcrumb = _breadcrumb([
        ("Home", "../index.html"),
        ("Companies", "index.html"),
        (entity["canonical_name"], None),
    ])

    body = (
        f'{breadcrumb}'
        f'<div class="page-header">'
        f'<h1>{_esc(entity["canonical_name"])}</h1>'
        f'<div class="subtitle">{_esc(entity.get("industry", ""))} · {_esc(entity.get("entity_type", ""))}</div>'
        f'<div class="stat-chips">{stat_chips}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="narrative">'
        f'{narrative}'
        f'{variants_table}'
        f'{match_section}'
        f'<p><a href="../trademarks.html">Trademark gallery →</a> &nbsp; '
        f'<a href="../patents.html">Patent gallery →</a></p>'
        f'</div>'
        f'</div>'
    )

    tm_count  = stats.get("trademark_count", 0)
    pat_count = stats.get("patent_count", 0)
    ent_desc = " · ".join(
        p for p in (entity.get("industry", ""), entity.get("entity_type", "")) if p
    ) or f"{tm_count} trademarks · {pat_count} patents"
    og = {
        "title": entity["canonical_name"],
        "description": ent_desc[:160],
        "url": f"{base_url}/{project}/entities/{slug}.html",
    } if base_url else None
    (out_dir / "entities").mkdir(exist_ok=True)
    out_path = out_dir / "entities" / f"{slug}.html"
    out_path.write_text(_page(_page_title(entity["canonical_name"], project), body, nav, project=project, project_title=project.replace('-', ' ').title(), depth=1, og=og,
                              active="entities/index.html"), encoding="utf-8")
    return out_path


