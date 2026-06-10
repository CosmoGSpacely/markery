"""Trademark and patent gallery pages."""
from __future__ import annotations

from pathlib import Path
from markery.common.project import Project
from markery.specialist.publisher.render.components import (
    _esc, _img_src, _page, _nav_links,
    _read_narrative, _narrative_block, _page_title, _timeline_svg,
    _STATUS_LABELS,
)


def render_trademark_gallery(
    project: str,
    entities: list[dict],
    trademarks: list[dict],
    matches: list[dict],
    entity_colors: dict[int, str],
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
    images_dir: Path | None = None,
    focus_serials: set[int] | None = None,
) -> Path:
    narrative = _read_narrative(Project(project).content / "trademarks-narrative.md",
                                link_index=link_index, depth=0)
    nav = _nav_links(project, entities, extra_nav)
    match_serials = {str(m["trademark_serial"]): m["slug"] for m in matches if m.get("essay_path")}
    focus_set = {str(s) for s in focus_serials} if focus_serials else None

    timeline = _timeline_svg(trademarks, "filing_dt", "mark_name", "entity_id", entity_colors)

    def _make_card(tm: dict, is_focus: bool = False) -> str:
        sn  = tm["serial_no"]
        src = _img_src("mark", sn, 0, images_dir) if tm.get("image_available") else None
        if src:
            img_html = f'<img class="card-image" loading="lazy" src="{src}" alt="{_esc(tm["mark_name"])}">'
        else:
            img_html = f'<div class="card-image-placeholder">{_esc(sn)}</div>'

        match_slug = match_serials.get(sn)
        match_html = (f'<a class="match-link" href="matches/{match_slug}.html">Confirmed pair →</a>'
                      if match_slug else "")

        filing = tm["filing_dt"].strftime("%B %d, %Y") if tm["filing_dt"] else ""
        status = _STATUS_LABELS.get(tm["status_cd"], str(tm["status_cd"]) if tm["status_cd"] else "")
        goods = (tm.get("goods") or "")[:120] + ("…" if (tm.get("goods") or "") and len(tm.get("goods", "")) > 120 else "")
        focus_badge = '<span class="focus-badge">Project Mark</span>' if is_focus else ""
        card_class = "card card--focus" if is_focus else "card"

        return (
            f'<div class="{card_class}" id="sn-{sn}">'
            f'{img_html}'
            f'<div class="card-body">'
            f'<div class="card-name">{_esc(tm["mark_name"] or "(design mark)")}</div>'
            f'<div class="card-meta">Filed {_esc(filing)} · {_esc(status)}</div>'
            f'<span class="entity-badge">{_esc(tm["entity_name"])}</span>'
            f'{focus_badge}'
            f'<div class="card-goods">{_esc(goods)}</div>'
            f'{match_html}'
            f'<div class="card-footer">{_esc(sn)} · Draw {_esc(tm["draw_cd"])}</div>'
            f'</div></div>'
        )

    if focus_set:
        focus_tms = [tm for tm in trademarks if tm["serial_no"] in focus_set]
        other_tms = [tm for tm in trademarks if tm["serial_no"] not in focus_set]
        gallery_html = (
            f'<p class="section-title">Project Marks</p>'
            f'<div class="card-grid">{"".join(_make_card(tm, True) for tm in focus_tms)}</div>'
            + (f'<p class="section-title">All Entity Trademarks</p>'
               f'<div class="card-grid">{"".join(_make_card(tm) for tm in other_tms)}</div>'
               if other_tms else "")
        )
    else:
        gallery_html = (
            f'<p class="section-title">All Marks</p>'
            f'<div class="card-grid">{"".join(_make_card(tm) for tm in trademarks)}</div>'
        )

    stat_chips = (
        f'<span class="chip">{len(trademarks)} marks</span>'
        f'<span class="chip">{sum(1 for t in trademarks if t["image_available"])} with images</span>'
        f'<span class="chip">{len(match_serials)} confirmed pairs</span>'
    )
    if focus_set:
        stat_chips += f'<span class="chip">{len([t for t in trademarks if t["serial_no"] in focus_set])} project marks</span>'

    body = (
        f'<div class="page-header">'
        f'<h1>Trademark Gallery</h1>'
        f'<div class="subtitle">{_esc(project.replace("-", " ").title())}</div>'
        f'<div class="stat-chips">{stat_chips}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'{_narrative_block(narrative)}'
        f'<div class="timeline-section"><p class="section-title">Filing Timeline</p>{timeline}</div>'
        f'{gallery_html}'
        f'</div>'
    )

    og = {
        "title": "Trademark Gallery",
        "description": f"All trademarks in the {project.replace('-', ' ').title()} project",
        "url": f"{base_url}/{project}/trademarks.html",
    } if base_url else None
    out_path = out_dir / "trademarks.html"
    out_path.write_text(_page(_page_title("Trademark Gallery", project), body, nav, og=og), encoding="utf-8")
    return out_path


def render_patent_gallery(
    project: str,
    entities: list[dict],
    patents: list[dict],
    matches: list[dict],
    entity_colors: dict[int, str],
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
    images_dir: Path | None = None,
) -> Path:
    narrative = _read_narrative(Project(project).content / "patents-narrative.md",
                                link_index=link_index, depth=0)
    nav = _nav_links(project, entities, extra_nav)
    match_patents = {m["patent_no"]: m["slug"] for m in matches if m.get("essay_path")}

    timeline = _timeline_svg(patents, "grant_dt", "title", "entity_id", entity_colors)

    cards = []
    for pat in patents:
        pn  = pat["patent_no"]
        src = _img_src("patent", pn, 0, images_dir) if pat.get("figure_available") else None
        if src:
            img_html = f'<img class="card-image" loading="lazy" src="{src}" alt="{_esc(pn)}">'
        else:
            img_html = f'<div class="card-image-placeholder">{_esc(pn)}</div>'

        match_slug = match_patents.get(pn)
        match_html = (f'<a class="match-link" href="matches/{match_slug}.html">Confirmed pair →</a>'
                      if match_slug else "")

        grant = pat["grant_dt"].strftime("%Y") if pat["grant_dt"] else ""
        inventors = ", ".join(pat["inventors"][:2]) + ("…" if len(pat["inventors"]) > 2 else "")
        classes = " · ".join(pat["cpc_classes"][:3])
        title = (pat.get("title") or "")[:70] + ("…" if len(pat.get("title") or "") > 70 else "")

        cards.append(
            f'<div class="card" id="pat-{pn}">'
            f'{img_html}'
            f'<div class="card-body">'
            f'<div class="card-name">{_esc(title)}</div>'
            f'<div class="card-meta">{_esc(pn)} · Granted {_esc(grant)}</div>'
            f'<span class="entity-badge">{_esc(pat["entity_name"])}</span>'
            f'<div class="card-goods">{_esc(inventors)}</div>'
            f'{match_html}'
            f'<div class="card-footer">{_esc(classes)}</div>'
            f'</div></div>'
        )

    stat_chips = (
        f'<span class="chip">{len(patents)} patents</span>'
        f'<span class="chip">{sum(1 for p in patents if p["figure_available"])} with figures</span>'
        f'<span class="chip">{len(match_patents)} confirmed pairs</span>'
    )

    body = (
        f'<div class="page-header">'
        f'<h1>Patent Gallery</h1>'
        f'<div class="subtitle">{_esc(project.replace("-", " ").title())}</div>'
        f'<div class="stat-chips">{stat_chips}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'{_narrative_block(narrative)}'
        f'<div class="timeline-section"><p class="section-title">Grant Timeline</p>{timeline}</div>'
        f'<p class="section-title">All Patents</p>'
        f'<div class="card-grid">{"".join(cards)}</div>'
        f'</div>'
    )

    og = {
        "title": "Patent Gallery",
        "description": f"All patents in the {project.replace('-', ' ').title()} project",
        "url": f"{base_url}/{project}/patents.html",
    } if base_url else None
    out_path = out_dir / "patents.html"
    out_path.write_text(_page(_page_title("Patent Gallery", project), body, nav, og=og), encoding="utf-8")
    return out_path


