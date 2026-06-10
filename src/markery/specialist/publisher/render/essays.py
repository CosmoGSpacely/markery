"""Match essays and thematic essays."""
from __future__ import annotations

import re
from pathlib import Path
from markery.common.project import Project
from markery.specialist.publisher.render.components import (
    _esc, _img_src, _page, _nav_links,
    _render_markdown, _page_title, _breadcrumb, _strip_frontmatter,
    _text_excerpt,
)


def render_match_essay(
    project: str,
    match: dict,
    entities: list[dict],
    out_dir: Path,
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
    images_dir: Path | None = None,
    figure_index: dict[str, str] | None = None,
) -> Path:
    slug = match["slug"]
    nav = _nav_links(project, entities, extra_nav)

    raw_essay: str | None = None
    if match.get("essay_path") and Path(match["essay_path"]).exists():
        raw_essay = _strip_frontmatter(Path(match["essay_path"]).read_text())
        essay_md = _render_markdown(raw_essay, link_index=link_index, depth=1,
                                    figure_index=figure_index)
        # Auto-embed: append figure below essay when no [[figure:]] tag but figure exists.
        pno = match.get("patent_no", "")
        if figure_index and pno and pno in figure_index and f"[[figure:{pno}]]" not in raw_essay:
            img_path = figure_index[pno]
            essay_md += (
                f'\n<figure class="patent-figure">'
                f'<img src="../{img_path}" alt="Patent drawing: {_esc(pno)}">'
                f'<figcaption>Patent drawing: {_esc(pno)}</figcaption>'
                f'</figure>'
            )
    else:
        essay_md = (
            f'<p style="color:#999;font-style:italic">'
            f'Essay not yet written. See <code>content-schemas/match-narrative.md</code>.</p>'
        )

    mark_src = _img_src("mark",   str(match["trademark_serial"]), 1, images_dir)
    fig_src  = _img_src("patent", match["patent_no"],             1, images_dir)

    media = ""
    if mark_src or fig_src:
        media_parts = []
        if mark_src:
            media_parts.append(
                f'<div><img src="{mark_src}" alt="{_esc(match["trademark"])}">'
                f'<div class="media-label">{_esc(match["trademark"])} · Serial {_esc(str(match["trademark_serial"]))}</div>'
                f'</div>'
            )
        if fig_src:
            media_parts.append(
                f'<div><img src="{fig_src}" alt="{_esc(match["patent_no"])}">'
                f'<div class="media-label">{_esc(match["patent_no"])} · Patent figure</div>'
                f'</div>'
            )
        media = f'<div class="essay-media">{"".join(media_parts)}</div>'

    sources = (
        f'<div class="sources"><h2>Primary Sources</h2><dl>'
        f'<dt>Trademark</dt>'
        f'<dd>Serial No. {_esc(str(match["trademark_serial"]))} · '
        f'{_esc(match["trademark"])} · Filed {match.get("filing_dt", "")}</dd>'
        f'<dt>Patent</dt>'
        f'<dd>{_esc(match["patent_no"])} · '
        f'{_esc(match.get("patent_title", ""))} · Granted {match.get("grant_dt", "")}</dd>'
        f'</dl></div>'
    )

    entity_rec  = next((e for e in entities if e.get("entity_id") == match.get("entity_id")), None)
    entity_slug = entity_rec["slug"] if entity_rec else None
    filed_by = (
        f'<span class="chip"><a href="../entities/{_esc(entity_slug)}.html">'
        f'Filed by: {_esc(match.get("entity", ""))}</a></span>'
        if entity_slug and match.get("entity") else
        f'<span class="chip">{_esc(match.get("entity", ""))}</span>'
    )
    stat_chips = (
        filed_by
        + f'<span class="chip">Patent {match.get("grant_dt", "")}</span>'
        + f'<span class="chip">Mark filed {match.get("filing_dt", "")}</span>'
    )

    crumb_title = f"{match['trademark'] or '(figurative)'} ↔ {match['patent_no']}"
    breadcrumb = _breadcrumb([
        ("Home", "../index.html"),
        ("Matches", "index.html"),
        (crumb_title, None),
    ])

    body = (
        f'{breadcrumb}'
        f'<div class="page-header">'
        f'<h1>{_esc(match["trademark"])} ↔ {_esc(match["patent_no"])}</h1>'
        f'<div class="subtitle">Confirmed patent-trademark pair · {_esc(project.replace("-", " ").title())}</div>'
        f'<div class="stat-chips">{stat_chips}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="essay">'
        f'{media}'
        f'{essay_md}'
        f'{sources}'
        f'</div>'
        f'</div>'
    )

    essay_title = f"{match['trademark']} ↔ {match['patent_no']}"
    note = (match.get("note") or "").strip()
    note_sentence = re.split(r'(?<=[.!?])\s', note)[0][:160] if note else \
        f"Confirmed patent-trademark pair: {match['trademark']} and {match['patent_no']}"
    og = {
        "title": essay_title,
        "description": note_sentence,
        "url": f"{base_url}/{project}/matches/{slug}.html",
    } if base_url else None
    (out_dir / "matches").mkdir(exist_ok=True)
    out_path = out_dir / "matches" / f"{slug}.html"
    out_path.write_text(_page(_page_title(essay_title, project), body, nav, depth=1, og=og), encoding="utf-8")
    return out_path


def render_thematic_essay(
    project: str,
    slug: str,
    out_dir: Path,
    entities: list[dict],
    base_url: str | None = None,
    link_index: dict[str, str] | None = None,
    extra_nav: dict[str, str] | None = None,
) -> Path:
    """Render a thematic essay from content/theme-<slug>.md → themes/<slug>.html."""
    proj = Project(project)
    src  = proj.content / f"theme-{slug}.md"
    nav  = _nav_links(project, entities, extra_nav)

    raw = _strip_frontmatter(src.read_text()) if src.exists() else ""
    title_match = re.search(r'^#\s+(.+)', raw, re.MULTILINE)
    essay_title = title_match.group(1).strip() if title_match else slug.replace("-", " ").title()

    essay_html = _render_markdown(raw, link_index=link_index, depth=1) if raw else (
        '<p style="color:#999;font-style:italic">Essay not yet written.</p>'
    )

    body = (
        f'<div class="page-header">'
        f'<h1>{_esc(essay_title)}</h1>'
        f'<div class="subtitle">Thematic essay · {_esc(project.replace("-", " ").title())}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="theme-essay">{essay_html}</div>'
        f'</div>'
    )

    og = {
        "title": essay_title,
        "description": _text_excerpt(src, 160),
        "url": f"{base_url}/{project}/themes/{slug}.html",
    } if base_url else None
    (out_dir / "themes").mkdir(exist_ok=True)
    out_path = out_dir / "themes" / f"{slug}.html"
    out_path.write_text(_page(_page_title(essay_title, project), body, nav, depth=1, og=og), encoding="utf-8")
    return out_path


