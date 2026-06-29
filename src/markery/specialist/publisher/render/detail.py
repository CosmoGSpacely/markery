"""Per-record detail pages: one page per trademark and per patent.

These are the link targets for the gallery cards (SITE-REVIEW #11) — a reader
clicks a card's image or title and lands on the full record.
"""
from __future__ import annotations

from pathlib import Path

from markery.specialist.publisher.render.components import (
    _esc, _img_src, _page, _nav_links, _page_title, _breadcrumb, _STATUS_LABELS,
)


def _fmt_date(dt: object) -> str:
    return dt.strftime("%B %d, %Y") if hasattr(dt, "strftime") else (str(dt) if dt else "")


def _dl(rows: list[tuple[str, str]]) -> str:
    """Render a definition list from (label, value) pairs, skipping empty values."""
    items = "".join(
        f'<dt>{_esc(label)}</dt><dd>{value}</dd>'
        for label, value in rows if value
    )
    return f'<dl class="detail-fields">{items}</dl>' if items else ""


def render_trademark_detail(
    project: str,
    tm: dict,
    entities: list[dict],
    matches: list[dict],
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
    images_dir: Path | None = None,
) -> Path:
    nav = _nav_links(project, entities, extra_nav)
    sn = tm["serial_no"]
    slug_by_id = {e["entity_id"]: e["slug"] for e in entities}
    match_slug = next(
        (m["slug"] for m in matches
         if str(m.get("trademark_serial")) == str(sn) and m.get("essay_path")),
        None,
    )

    mark_name = tm["mark_name"] or "(design mark)"
    src = _img_src("mark", sn, 1, images_dir) if tm.get("image_available") else None
    if src:
        img = f'<img class="detail-image" src="{src}" alt="{_esc(mark_name)}">'
    else:
        img = f'<div class="detail-image-placeholder">{_esc(mark_name)}</div>'

    status = _STATUS_LABELS.get(tm["status_cd"], str(tm["status_cd"]) if tm["status_cd"] else "")
    slug = slug_by_id.get(tm["entity_id"])
    entity_link = (
        f'<a href="../entities/{slug}.html">{_esc(tm["entity_name"])}</a>'
        if slug else _esc(tm["entity_name"])
    )
    fields = _dl([
        ("Serial No.", _esc(sn)),
        ("Owner", _esc(tm.get("owner_name") or "")),
        ("Company", entity_link),
        ("Filed", _esc(_fmt_date(tm.get("filing_dt")))),
        ("First use", _esc(_fmt_date(tm.get("first_use_dt")))),
        ("Registration No.", _esc(tm.get("registration_no") or "")),
        ("Status", _esc(status)),
        ("Drawing Code", _esc(tm.get("draw_cd") or "")),
        ("Goods & services", _esc(tm.get("goods") or "")),
    ])

    match_html = (
        f'<a class="match-link match-link--lg" href="../matches/{match_slug}.html">'
        f'Confirmed pair → read the essay</a>'
        if match_slug else ""
    )

    breadcrumb = _breadcrumb([
        ("Home", "../index.html"),
        ("Trademarks", "../trademarks.html"),
        (mark_name, None),
    ])
    body = (
        f'{breadcrumb}'
        f'<div class="page-header">'
        f'<h1>{_esc(mark_name)}</h1>'
        f'<div class="subtitle">Trademark · {_esc(tm["entity_name"])}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="detail-layout">'
        f'<div class="detail-media">{img}{match_html}</div>'
        f'<div class="detail-body">{fields}</div>'
        f'</div>'
        f'</div>'
    )

    og = {
        "title": mark_name,
        "description": (tm.get("goods") or f'{mark_name} — {tm["entity_name"]}')[:160],
        "url": f"{base_url}/{project}/trademarks/{sn}.html",
    } if base_url else None
    (out_dir / "trademarks").mkdir(exist_ok=True)
    out_path = out_dir / "trademarks" / f"{sn}.html"
    out_path.write_text(
        _page(_page_title(mark_name, project), body, nav, project=project, project_title=project.replace('-', ' ').title(), depth=1, og=og,
              active="trademarks.html"),
        encoding="utf-8",
    )
    return out_path


def render_patent_detail(
    project: str,
    pat: dict,
    entities: list[dict],
    matches: list[dict],
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
    images_dir: Path | None = None,
) -> Path:
    nav = _nav_links(project, entities, extra_nav)
    pn = pat["patent_no"]
    slug_by_id = {e["entity_id"]: e["slug"] for e in entities}
    match_slug = next(
        (m["slug"] for m in matches
         if m.get("patent_no") == pn and m.get("essay_path")),
        None,
    )

    title = pat.get("title") or pn
    src = _img_src("patent", pn, 1, images_dir) if pat.get("figure_available") else None
    if src:
        img = f'<img class="detail-image" src="{src}" alt="{_esc(title)}">'
    else:
        img = f'<div class="detail-image-placeholder">{_esc(title)}</div>'

    slug = slug_by_id.get(pat["entity_id"])
    entity_link = (
        f'<a href="../entities/{slug}.html">{_esc(pat["entity_name"])}</a>'
        if slug else _esc(pat["entity_name"])
    )
    fields = _dl([
        ("Patent No.", _esc(pn)),
        ("Assignee", _esc(pat.get("assignee_name") or "")),
        ("Company", entity_link),
        ("Granted", _esc(_fmt_date(pat.get("grant_dt")))),
        ("Filed", _esc(_fmt_date(pat.get("application_dt")))),
        ("Inventors", _esc(", ".join(i for i in (pat.get("inventors") or []) if i))),
        ("Classification", _esc(" · ".join(pat.get("cpc_classes") or []))),
    ])

    match_html = (
        f'<a class="match-link match-link--lg" href="../matches/{match_slug}.html">'
        f'Confirmed pair → read the essay</a>'
        if match_slug else ""
    )

    breadcrumb = _breadcrumb([
        ("Home", "../index.html"),
        ("Patents", "../patents.html"),
        (title, None),
    ])
    body = (
        f'{breadcrumb}'
        f'<div class="page-header">'
        f'<h1>{_esc(title)}</h1>'
        f'<div class="subtitle">Patent {_esc(pn)} · {_esc(pat["entity_name"])}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="detail-layout">'
        f'<div class="detail-media">{img}{match_html}</div>'
        f'<div class="detail-body">{fields}</div>'
        f'</div>'
        f'</div>'
    )

    og = {
        "title": title,
        "description": f'Patent {pn} — {pat["entity_name"]}'[:160],
        "url": f"{base_url}/{project}/patents/{pn}.html",
    } if base_url else None
    (out_dir / "patents").mkdir(exist_ok=True)
    out_path = out_dir / "patents" / f"{pn}.html"
    out_path.write_text(
        _page(_page_title(title, project), body, nav, project=project, project_title=project.replace('-', ' ').title(), depth=1, og=og,
              active="patents.html"),
        encoding="utf-8",
    )
    return out_path
