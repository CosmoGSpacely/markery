"""Landing page and section index pages."""
from __future__ import annotations

import re
from pathlib import Path
from markery.common.project import Project
from markery.specialist.publisher.render.components import (
    _esc, _img_src, _page, _nav_links,
    _read_narrative, _narrative_block, _page_title,
    _year_from_dt,
)


def render_landing(
    project: str,
    entities: list[dict],
    trademarks: list[dict],
    patents: list[dict],
    matches: list[dict],
    entity_stats: dict[int, dict],
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
    images_dir: Path | None = None,
    research_question: str | None = None,
) -> Path:
    narrative = _read_narrative(Project(project).content / "index-narrative.md",
                                link_index=link_index, depth=0)
    nav = _nav_links(project, entities, extra_nav)

    match_cards = []
    for m in matches:
        tm_label = m["trademark"] or "(figurative)"
        tm_thumb = (m["trademark"] or "◆")[:3]
        src = _img_src("mark", str(m["trademark_serial"]), 0, images_dir) if m.get("has_image") else None
        if src:
            thumb = f'<img class="match-card-thumb" loading="lazy" src="{src}" alt="{_esc(tm_label)}">'
        else:
            thumb = f'<div class="match-card-thumb-placeholder">{_esc(tm_thumb)}</div>'

        essay_link = ""
        if m.get("essay_path"):
            essay_link = f'<a href="matches/{m["slug"]}.html">Read essay →</a>'

        grant = m.get("grant_dt", "")
        filed = m.get("filing_dt", "")
        gy, fy = _year_from_dt(grant), _year_from_dt(filed)
        gap_chip = f'<span class="chip-sm">{abs(gy - fy)} yr gap</span>' if gy and fy else ""
        match_cards.append(
            f'<div class="match-card">'
            f'{thumb}'
            f'<div class="match-card-body">'
            f'<div class="match-card-title">{_esc(tm_label)} ↔ {_esc(m["patent_no"])}</div>'
            f'<div class="match-card-meta">{_esc(m.get("entity", ""))} · '
            f'Patent {grant} · Mark filed {filed} {gap_chip}</div>'
            f'<div class="match-card-note">{_esc(m.get("note", ""))}</div>'
            f'{essay_link}'
            f'</div></div>'
        )

    entity_cards = []
    for e in entities:
        s = entity_stats.get(e["entity_id"], {})
        slug = e["slug"]
        entity_cards.append(
            f'<div class="entity-card">'
            f'<h3><a href="entities/{slug}.html">{_esc(e["canonical_name"])}</a></h3>'
            f'<div class="entity-meta">{_esc(e.get("industry", ""))} · {_esc(e.get("entity_type", ""))}</div>'
            f'<div class="entity-stats">'
            f'<span><span class="stat-val">{s.get("trademark_count", 0)}</span> marks</span>'
            f'<span><span class="stat-val">{s.get("patent_count", 0)}</span> patents</span>'
            f'<span><span class="stat-val">{s.get("match_count", 0)}</span> confirmed</span>'
            f'</div>'
            f'<div class="links">'
            f'<a href="trademarks.html">Trademarks</a>'
            f'<a href="patents.html">Patents</a>'
            f'</div>'
            f'</div>'
        )

    stat_chips = (
        f'<span class="chip">{len(entities)} companies</span>'
        f'<span class="chip">{len(trademarks)} marks</span>'
        f'<span class="chip">{len(patents)} patents</span>'
        f'<span class="chip">{len(matches)} confirmed pairs</span>'
    )

    rq_html = ""
    if research_question:
        paras = "".join(
            f'<p>{_esc(p.strip())}</p>'
            for p in research_question.split("\n\n") if p.strip()
        )
        rq_html = (
            f'<div class="research-question">'
            f'<span class="rq-label">Research Question</span>{paras}</div>'
        )

    body = (
        f'<div class="page-header">'
        f'<h1>{_esc(project.replace("-", " ").title())}</h1>'
        f'<div class="subtitle">USPTO Patent-Trademark Research Project · 1900–1939</div>'
        f'<div class="stat-chips">{stat_chips}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'{rq_html}'
        f'{_narrative_block(narrative)}'
        + (f'<p class="section-title">Confirmed Pairs</p>'
           f'<div class="match-cards">{"".join(match_cards)}</div>' if match_cards else '')
        + f'<p class="section-title">Companies</p>'
        f'<div class="entity-grid">{"".join(entity_cards)}</div>'
        f'</div>'
    )

    title = f"{project.replace('-', ' ').title()} — Markery"
    if research_question:
        landing_desc = re.split(r'(?<=[.!?])\s', research_question.strip())[0][:160]
    else:
        landing_desc = "USPTO Patent-Trademark Research Project · 1900–1939"
    og = {
        "title": title,
        "description": landing_desc,
        "url": f"{base_url}/{project}/index.html",
    } if base_url else None
    out_path = out_dir / "index.html"
    out_path.write_text(_page(title, body, nav, og=og), encoding="utf-8")
    return out_path


def render_entities_index(
    project: str,
    entities: list[dict],
    entity_stats: dict[int, dict],
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
) -> Path:
    """Render the Companies section index → entities/index.html (depth 1)."""
    nav = _nav_links(project, entities, extra_nav)

    cards = []
    for e in entities:
        s = entity_stats.get(e["entity_id"], {})
        cards.append(
            f'<div class="entity-card">'
            f'<h3><a href="{e["slug"]}.html">{_esc(e["canonical_name"])}</a></h3>'
            f'<div class="entity-meta">{_esc(e.get("industry", ""))} · {_esc(e.get("entity_type", ""))}</div>'
            f'<div class="entity-stats">'
            f'<span><span class="stat-val">{s.get("trademark_count", 0)}</span> marks</span>'
            f'<span><span class="stat-val">{s.get("patent_count", 0)}</span> patents</span>'
            f'<span><span class="stat-val">{s.get("match_count", 0)}</span> confirmed</span>'
            f'</div></div>'
        )

    listing = (
        f'<div class="entity-grid">{"".join(cards)}</div>'
        if cards else '<p class="empty-state">No companies recorded for this project yet.</p>'
    )
    body = (
        f'<div class="page-header">'
        f'<h1>Companies</h1>'
        f'<div class="subtitle">{_esc(project.replace("-", " ").title())} · {len(entities)} companies</div>'
        f'</div>'
        f'<div class="page-body">{listing}</div>'
    )

    og = {
        "title": "Companies",
        "description": f"All {len(entities)} companies in the {project.replace('-', ' ').title()} project",
        "url": f"{base_url}/{project}/entities/index.html",
    } if base_url else None
    (out_dir / "entities").mkdir(exist_ok=True)
    out_path = out_dir / "entities" / "index.html"
    out_path.write_text(_page(_page_title("Companies", project), body, nav, depth=1, og=og,
                              active="entities/index.html"),
                        encoding="utf-8")
    return out_path


def render_matches_index(
    project: str,
    matches: list[dict],
    entities: list[dict],
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
    images_dir: Path | None = None,
) -> Path:
    """Render the Matches section index → matches/index.html (depth 1)."""
    nav = _nav_links(project, entities, extra_nav)

    cards = []
    seen: set[str] = set()
    for m in matches:
        slug = m.get("slug", "")
        if not slug or slug in seen or not m.get("essay_path"):
            continue
        seen.add(slug)
        src = _img_src("mark", str(m["trademark_serial"]), 1, images_dir) if m.get("has_image") else None
        if src:
            thumb = f'<img class="match-card-thumb" loading="lazy" src="{src}" alt="{_esc(m.get("trademark") or "(figurative)")}">'
        else:
            label = (m.get("trademark") or "·")[:3]
            thumb = f'<div class="match-card-thumb-placeholder">{_esc(label)}</div>'
        gy, fy = _year_from_dt(m.get("grant_dt")), _year_from_dt(m.get("filing_dt"))
        gap_chip = f'<span class="chip-sm">{abs(gy - fy)} yr gap</span>' if gy and fy else ""
        cards.append(
            f'<div class="match-card">'
            f'{thumb}'
            f'<div class="match-card-body">'
            f'<div class="match-card-title">'
            f'<a href="{slug}.html">{_esc(m.get("trademark") or "(figurative)")} ↔ {_esc(m["patent_no"])}</a>'
            f'</div>'
            f'<div class="match-card-meta">{_esc(m.get("entity", ""))} {gap_chip}</div>'
            f'<div class="match-card-note">{_esc(m.get("note", ""))}</div>'
            f'</div></div>'
        )

    listing = (
        f'<div class="match-cards">{"".join(cards)}</div>'
        if cards else '<p>No confirmed pairs yet.</p>'
    )
    body = (
        f'<div class="page-header">'
        f'<h1>Confirmed Pairs</h1>'
        f'<div class="subtitle">{_esc(project.replace("-", " ").title())} · {len(seen)} pairs</div>'
        f'</div>'
        f'<div class="page-body">{listing}</div>'
    )

    og = {
        "title": "Confirmed Pairs",
        "description": f"All {len(seen)} confirmed patent-trademark pairs in the {project.replace('-', ' ').title()} project",
        "url": f"{base_url}/{project}/matches/index.html",
    } if base_url else None
    (out_dir / "matches").mkdir(exist_ok=True)
    out_path = out_dir / "matches" / "index.html"
    out_path.write_text(_page(_page_title("Confirmed Pairs", project), body, nav, depth=1, og=og,
                              active="matches/index.html"),
                        encoding="utf-8")
    return out_path


