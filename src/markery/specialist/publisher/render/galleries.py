"""Trademark and patent gallery pages."""
from __future__ import annotations

from pathlib import Path
from markery.common.project import Project
from markery.specialist.publisher.render.components import (
    _esc, _img_src, _page, _nav_links,
    _read_narrative, _narrative_block, _page_title, _timeline_layout,
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
    media_index: dict[str, dict] | None = None,
) -> Path:
    narrative = _read_narrative(Project(project).content / "trademarks-narrative.md",
                                link_index=link_index, depth=0, media_index=media_index)
    nav = _nav_links(project, entities, extra_nav)
    match_serials = {str(m["trademark_serial"]): m["slug"] for m in matches if m.get("essay_path")}
    focus_set = {str(s) for s in focus_serials} if focus_serials else None
    slug_by_id = {e["entity_id"]: e["slug"] for e in entities}

    def _make_card(tm: dict, is_focus: bool = False) -> str:
        sn  = tm["serial_no"]
        detail_url = f"trademarks/{sn}.html"
        src = _img_src("mark", sn, 0, images_dir) if tm.get("image_available") else None
        if src:
            inner = f'<img class="card-image" loading="lazy" src="{src}" alt="{_esc(tm["mark_name"])}">'
        else:
            # No image: fall back to the word mark, not the (meaningless) serial number.
            word_mark = tm["mark_name"] or "(design mark)"
            inner = f'<div class="card-image-placeholder">{_esc(word_mark)}</div>'
        img_html = f'<a class="card-image-link" href="{detail_url}">{inner}</a>'

        match_slug = match_serials.get(sn)
        match_html = (f'<a class="match-link" href="matches/{match_slug}.html">Confirmed pair →</a>'
                      if match_slug else "")

        filing = tm["filing_dt"].strftime("%B %d, %Y") if tm["filing_dt"] else ""
        status = _STATUS_LABELS.get(tm["status_cd"], str(tm["status_cd"]) if tm["status_cd"] else "")
        goods_full = tm.get("goods") or ""
        goods = goods_full[:120] + ("…" if len(goods_full) > 120 else "")
        goods_attr = f' title="{_esc(goods_full)}"' if goods_full else ""
        focus_badge = '<span class="focus-badge">Project Mark</span>' if is_focus else ""
        card_class = "card card--focus" if is_focus else "card"

        slug = slug_by_id.get(tm["entity_id"])
        entity_badge = (
            f'<a class="entity-badge" href="entities/{slug}.html">{_esc(tm["entity_name"])}</a>'
            if slug else f'<span class="entity-badge">{_esc(tm["entity_name"])}</span>'
        )
        draw_footer = f' · Drawing Code {_esc(tm["draw_cd"])}' if tm.get("draw_cd") else ""

        return (
            f'<div class="{card_class}" id="sn-{sn}">'
            f'{img_html}'
            f'<div class="card-body">'
            f'<div class="card-name"><a href="{detail_url}">{_esc(tm["mark_name"] or "(design mark)")}</a></div>'
            f'<div class="card-meta">Filed {_esc(filing)} · {_esc(status)}</div>'
            f'{entity_badge}'
            f'{focus_badge}'
            f'<div class="card-goods"{goods_attr}>{_esc(goods)}</div>'
            f'{match_html}'
            f'<div class="card-footer">{_esc(sn)}{draw_footer}</div>'
            f'</div></div>'
        )

    if focus_set:
        focus_tms = [tm for tm in trademarks if tm["serial_no"] in focus_set]
        other_tms = [tm for tm in trademarks if tm["serial_no"] not in focus_set]
        gallery_html = (
            f'<p class="section-title">Project Marks</p>'
            + _timeline_layout(focus_tms, "filing_dt", lambda tm: _make_card(tm, True))
            + (f'<p class="section-title">All Entity Trademarks</p>'
               + _timeline_layout(other_tms, "filing_dt", _make_card)
               if other_tms else "")
        )
    elif trademarks:
        gallery_html = (
            f'<p class="section-title">All Marks</p>'
            + _timeline_layout(trademarks, "filing_dt", _make_card)
        )
    else:
        gallery_html = '<p class="empty-state">No trademarks recorded for this project yet.</p>'

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
        f'{gallery_html}'
        f'</div>'
    )

    og = {
        "title": "Trademark Gallery",
        "description": f"All trademarks in the {project.replace('-', ' ').title()} project",
        "url": f"{base_url}/{project}/trademarks.html",
    } if base_url else None
    out_path = out_dir / "trademarks.html"
    out_path.write_text(_page(_page_title("Trademark Gallery", project), body, nav, project=project, project_title=project.replace('-', ' ').title(), og=og,
                              active="trademarks.html"), encoding="utf-8")
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
    media_index: dict[str, dict] | None = None,
) -> Path:
    narrative = _read_narrative(Project(project).content / "patents-narrative.md",
                                link_index=link_index, depth=0, media_index=media_index)
    nav = _nav_links(project, entities, extra_nav)
    match_patents = {m["patent_no"]: m["slug"] for m in matches if m.get("essay_path")}
    slug_by_id = {e["entity_id"]: e["slug"] for e in entities}

    def _make_card(pat: dict) -> str:
        pn  = pat["patent_no"]
        detail_url = f"patents/{pn}.html"
        title_full = pat.get("title") or ""
        src = _img_src("patent", pn, 0, images_dir) if pat.get("figure_available") else None
        if src:
            inner = f'<img class="card-image" loading="lazy" src="{src}" alt="{_esc(title_full or pn)}">'
        else:
            # No figure: fall back to the patent title, not the bare patent number.
            inner = f'<div class="card-image-placeholder">{_esc(title_full or pn)}</div>'
        img_html = f'<a class="card-image-link" href="{detail_url}">{inner}</a>'

        match_slug = match_patents.get(pn)
        match_html = (f'<a class="match-link" href="matches/{match_slug}.html">Confirmed pair →</a>'
                      if match_slug else "")

        grant = pat["grant_dt"].strftime("%B %d, %Y") if pat["grant_dt"] else ""
        inv_list = [i for i in (pat["inventors"] or []) if i]   # EPO records may carry null inventors
        inventors_full = ", ".join(inv_list)
        inventors = ", ".join(inv_list[:2]) + ("…" if len(inv_list) > 2 else "")
        inv_attr = f' title="{_esc(inventors_full)}"' if inventors_full else ""
        classes = " · ".join(pat["cpc_classes"][:3])
        class_label = "Class" if len(pat["cpc_classes"]) == 1 else "Classes"
        class_footer = f'{class_label} {_esc(classes)}' if classes else ""
        title = title_full[:70] + ("…" if len(title_full) > 70 else "")
        title_attr = f' title="{_esc(title_full)}"' if title_full else ""

        slug = slug_by_id.get(pat["entity_id"])
        entity_badge = (
            f'<a class="entity-badge" href="entities/{slug}.html">{_esc(pat["entity_name"])}</a>'
            if slug else f'<span class="entity-badge">{_esc(pat["entity_name"])}</span>'
        )

        return (
            f'<div class="card" id="pat-{pn}">'
            f'{img_html}'
            f'<div class="card-body">'
            f'<div class="card-name"{title_attr}><a href="{detail_url}">{_esc(title)}</a></div>'
            f'<div class="card-meta">{_esc(pn)} · Granted {_esc(grant)}</div>'
            f'{entity_badge}'
            f'<div class="card-goods"{inv_attr}>{_esc(inventors)}</div>'
            f'{match_html}'
            f'<div class="card-footer">{class_footer}</div>'
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
        + (f'<p class="section-title">All Patents</p>'
           + _timeline_layout(patents, "grant_dt", _make_card)
           if patents else '<p class="empty-state">No patents recorded for this project yet.</p>')
        + f'</div>'
    )

    og = {
        "title": "Patent Gallery",
        "description": f"All patents in the {project.replace('-', ' ').title()} project",
        "url": f"{base_url}/{project}/patents.html",
    } if base_url else None
    out_path = out_dir / "patents.html"
    out_path.write_text(_page(_page_title("Patent Gallery", project), body, nav, project=project, project_title=project.replace('-', ' ').title(), og=og,
                              active="patents.html"), encoding="utf-8")
    return out_path


