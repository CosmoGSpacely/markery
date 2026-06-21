"""Shared rendering primitives: escaping, page chrome, Markdown, timeline, helpers."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from markery.common.project import Project
from markery.specialist.publisher.queries import get_mark_image_b64, get_patent_figure_b64
from markery.specialist.publisher.render.css import _CSS


_STATUS_LABELS = {
    800: "Registered",
    900: "Expired",
    713: "Abandoned",
    710: "Abandoned",
    626: "Backfile cancelled",
}


def _esc(s: str | None) -> str:
    if not s:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _img_src(
    kind: str,
    key: str,
    depth: int,
    images_dir: Path | None,
) -> str | None:
    """Return an img src value: file-relative path if available on disk, else base64 data URL."""
    if images_dir is not None:
        subdir = "marks" if kind == "mark" else "patents"
        fpath  = images_dir / subdir / f"{key}.png"
        if fpath.exists():
            prefix = "../" * depth
            return f"{prefix}images/{subdir}/{key}.png"
    if kind == "mark":
        b64 = get_mark_image_b64(key)
    else:
        b64 = get_patent_figure_b64(key)
    return f"data:image/png;base64,{b64}" if b64 else None


_MARKERY_REPO = "https://github.com/CosmoGSpacely/markery"


def _page(
    title: str,
    body: str,
    nav_links: dict[str, str],
    depth: int = 0,
    og: dict | None = None,
    site_repo: str | None = None,
    active: str | None = None,
    project: str | None = None,
    project_title: str | None = None,
) -> str:
    # `depth` is the page's depth within its project. When the page belongs to a
    # project (project is not None) the site root is one further level up, since
    # projects nest under site/<project>/.
    proj_prefix = "../" * depth
    root_prefix = "../" * (depth + (1 if project else 0))

    def _nav_anchor(label: str, href: str) -> str:
        is_active = active is not None and href == active
        attrs = ' class="active" aria-current="page"' if is_active else ""
        return f'<a href="{proj_prefix}{href}"{attrs}>{_esc(label)}</a>'

    nav = "".join(_nav_anchor(label, href) for label, href in nav_links.items())
    project_bar = ""
    if project is not None:
        title_html = (
            f'<a class="project-bar-title" href="{proj_prefix}index.html">{_esc(project_title or "")}</a>'
        )
        project_bar = (
            f'<div class="project-bar">'
            f'{title_html}'
            f'<nav class="project-nav" aria-label="Project sections">{nav}</nav>'
            f'</div>\n'
        )
    head_meta = ""
    if og:
        desc = og.get("description", "")
        url  = og.get("url", "")
        if desc:
            head_meta += f'<meta name="description" content="{_esc(desc)}">\n'
        if url:
            head_meta += f'<link rel="canonical" href="{_esc(url)}">\n'
        head_meta += (
            f'<meta property="og:title"       content="{_esc(og.get("title", title))}">\n'
            f'<meta property="og:description" content="{_esc(desc)}">\n'
            f'<meta property="og:url"         content="{_esc(url)}">\n'
            f'<meta property="og:type"        content="article">\n'
        )
    repo = site_repo or _MARKERY_REPO
    footer = (
        f'\n<footer class="site-footer">'
        f'History of commerce and technology is built by '
        f'<a href="{_esc(repo)}">Markery</a>. '
        f'Copyright {date.today().year} '
        f'<a href="https://guildproducts.com">Guild Products</a>.'
        f'</footer>\n'
    )
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{_esc(title)}</title>\n'
        + head_meta
        + f'<style>{_CSS}</style>\n'
        '</head>\n<body>\n'
        '<a class="skip-link" href="#main">Skip to content</a>\n'
        f'<header class="global-bar">'
        f'<a class="site-title" href="{root_prefix}index.html">Markery Research</a>'
        f'<form class="site-search" action="{root_prefix}search.html" method="get">'
        f'<input type="search" name="q" placeholder="Search Markery…" aria-label="Search Markery"></form>'
        '</header>\n'
        + project_bar
        + '<main id="main">\n'
        + body
        + '</main>\n'
        + footer
        + '</body>\n</html>\n'
    )


def _nav_links(
    project: str,
    entities: list[dict],
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    """Top-level nav: section indexes, not per-entity links.

    Entities are reached through the Entities index page (entities/index.html)
    rather than being enumerated in the header — this keeps the nav bounded
    regardless of entity count.
    """
    links: dict[str, str] = {
        "Trademarks": "trademarks.html",
        "Patents": "patents.html",
        "Companies": "entities/index.html",
        "Matches": "matches/index.html",
    }
    if extra:
        links.update(extra)
    return links


def _render_markdown(
    text: str,
    link_index: dict[str, str] | None = None,
    depth: int = 0,
    figure_index: dict[str, str] | None = None,
) -> str:
    """Minimal Markdown → HTML: headings, paragraphs, bold, inline code, fenced blocks,
    unordered/ordered lists, blockquotes, and external links.

    link_index maps slug → root-relative URL; [[Slug]] resolves to <a>.
    figure_index maps patent_no → root-relative image path; [[figure:patent_no]] renders <figure>.
    depth controls how many ../ prefixes to prepend to root-relative URLs.
    """
    stash: dict[str, str] = {}

    def _stash_block(m: re.Match) -> str:
        key = f"\x00BLOCK{len(stash)}\x00"
        stash[key] = f'<pre><code>{_esc(m.group(1))}</code></pre>'
        return key

    text = re.sub(r'```[^\n]*\n(.*?)```', _stash_block, text, flags=re.DOTALL)

    # Stash external links [text](url) — only http/https schemes accepted.
    def _stash_ext_link(m: re.Match) -> str:
        label, url = m.group(1), m.group(2)
        key = f"\x00LINK{len(stash)}\x00"
        if re.match(r'^https?://', url):
            stash[key] = f'<a href="{url}" target="_blank" rel="noopener">{_esc(label)}</a>'
        else:
            stash[key] = _esc(label)
        return key

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _stash_ext_link, text)

    if link_index or figure_index:
        prefix = "../" * depth

        def _stash_link(m: re.Match) -> str:
            raw = m.group(1)
            key = f"\x00LINK{len(stash)}\x00"
            if figure_index is not None and raw.startswith("figure:"):
                pno      = raw[7:]
                img_path = figure_index.get(pno)
                if img_path:
                    stash[key] = (
                        f'<figure class="patent-figure">'
                        f'<img src="{prefix}{img_path}" alt="Patent drawing: {_esc(pno)}">'
                        f'<figcaption>Patent drawing: {_esc(pno)}</figcaption>'
                        f'</figure>'
                    )
                else:
                    stash[key] = f'<em>[Figure: {_esc(pno)}]</em>'
                return key
            if link_index:
                url = link_index.get(raw.lower().replace(" ", "-"))
                if url:
                    stash[key] = f'<a href="{prefix}{url}">{_esc(raw)}</a>'
                    return key
            stash[key] = _esc(raw)
            return key

        text = re.sub(r'\[\[([^\]]+)\]\]', _stash_link, text)

    def _inline(s: str) -> str:
        out = _esc(s)
        out = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', out)
        out = re.sub(r'`(.+?)`', r'<code>\1</code>', out)
        for k, v in stash.items():
            if k in out:
                out = out.replace(k, v)
        return out

    lines = text.split("\n")
    html_parts: list[str] = []
    in_para = False
    in_ul   = False
    in_ol   = False
    in_bq   = False

    def _close_blocks() -> None:
        nonlocal in_para, in_ul, in_ol, in_bq
        if in_para: html_parts.append("</p>"); in_para = False
        if in_ul:   html_parts.append("</ul>");  in_ul   = False
        if in_ol:   html_parts.append("</ol>");  in_ol   = False
        if in_bq:   html_parts.append("</blockquote>"); in_bq = False

    for line in lines:
        if line.startswith("## "):
            _close_blocks()
            html_parts.append(f'<h2>{_esc(line[3:])}</h2>')
        elif line.startswith("### "):
            _close_blocks()
            html_parts.append(f'<h3>{_esc(line[4:])}</h3>')
        elif line.startswith("# "):
            _close_blocks()
            html_parts.append(f'<h2>{_esc(line[2:])}</h2>')
        elif line.strip() == "":
            _close_blocks()
        elif line.startswith("\x00BLOCK") and line.rstrip() in stash:
            _close_blocks()
            html_parts.append(stash[line.rstrip()])
        elif line.startswith("- ") or line.startswith("* "):
            if in_para: html_parts.append("</p>"); in_para = False
            if in_bq:   html_parts.append("</blockquote>"); in_bq = False
            if in_ol:   html_parts.append("</ol>"); in_ol = False
            if not in_ul: html_parts.append("<ul>"); in_ul = True
            html_parts.append(f'<li>{_inline(line[2:])}</li>')
        elif re.match(r'^\d+\.\s', line):
            if in_para: html_parts.append("</p>"); in_para = False
            if in_bq:   html_parts.append("</blockquote>"); in_bq = False
            if in_ul:   html_parts.append("</ul>"); in_ul = False
            if not in_ol: html_parts.append("<ol>"); in_ol = True
            item = re.sub(r"^\d+\.\s+", "", line)  # backslash regex kept out of the f-string (3.11 compat)
            html_parts.append(f'<li>{_inline(item)}</li>')
        elif line.startswith("> "):
            if in_para: html_parts.append("</p>"); in_para = False
            if in_ul:   html_parts.append("</ul>"); in_ul = False
            if in_ol:   html_parts.append("</ol>"); in_ol = False
            if not in_bq: html_parts.append("<blockquote>"); in_bq = True
            html_parts.append(f'<p>{_inline(line[2:])}</p>')
        else:
            if in_ul: html_parts.append("</ul>"); in_ul = False
            if in_ol: html_parts.append("</ol>"); in_ol = False
            if in_bq: html_parts.append("</blockquote>"); in_bq = False
            if not in_para:
                html_parts.append("<p>")
                in_para = True
            html_parts.append(_inline(line) + " ")

    if in_para: html_parts.append("</p>")
    if in_ul:   html_parts.append("</ul>")
    if in_ol:   html_parts.append("</ol>")
    if in_bq:   html_parts.append("</blockquote>")

    return "\n".join(html_parts)


def _read_narrative(
    path: Path,
    link_index: dict[str, str] | None = None,
    depth: int = 0,
    figure_index: dict[str, str] | None = None,
) -> str:
    if path.exists():
        return _render_markdown(path.read_text(), link_index=link_index,
                                depth=depth, figure_index=figure_index)
    # Missing narrative source: suppress the section entirely (no placeholder prose).
    return ""


def _narrative_block(narrative: str) -> str:
    """Wrap narrative HTML in its section div, or return '' to suppress the section."""
    return f'<div class="narrative">{narrative}</div>' if narrative else ''


def _page_title(page: str, project: str) -> str:
    """Format a page <title> as '[Page] — [Project Display] — Markery'."""
    return f"{page} — {project.replace('-', ' ').title()} — Markery"


def _breadcrumb(trail: list[tuple[str, str | None]]) -> str:
    """Render an accessible breadcrumb. Each item is (label, href|None);
    href=None renders the current (final) page as plain text."""
    items = []
    for label, href in trail:
        if href:
            items.append(f'<li><a href="{href}">{_esc(label)}</a></li>')
        else:
            items.append(f'<li aria-current="page">{_esc(label)}</li>')
    return (
        f'<nav class="breadcrumb" aria-label="Breadcrumb">'
        f'<ol>{"".join(items)}</ol></nav>'
    )


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (--- ... ---) from the start of a file."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4:].lstrip("\n")


def _parse_site_mode(proj: Project) -> str:
    """Return site_mode from OBJECTIVES.md frontmatter; default 'narrative'."""
    if not proj.objectives.exists():
        return "narrative"
    m = re.search(r'^site_mode:\s*(\w+)', proj.objectives.read_text(), re.MULTILINE)
    return m.group(1) if m else "narrative"


def _text_excerpt(path: Path, max_chars: int = 200) -> str:
    """Return a plain-text excerpt from a markdown file (frontmatter stripped)."""
    if not path.exists():
        return ""
    text = _strip_frontmatter(path.read_text())
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\[\[(.+?)\]\]', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]


def _year_from_dt(dt: object) -> int | None:
    """Extract a year integer from a date object, datetime, or YYYY-... string."""
    if dt is None:
        return None
    if hasattr(dt, "year"):
        return int(dt.year)
    try:
        return int(str(dt)[:4])
    except (ValueError, TypeError):
        return None


def build_link_index(
    entities: list[dict],
    matches: list[dict],
    theme_slugs: list[str],
) -> dict[str, str]:
    """Build slug → root-relative-URL mapping for [[cross-link]] resolution."""
    index: dict[str, str] = {}
    for e in entities:
        index[e["slug"]] = f"entities/{e['slug']}.html"
    for m in matches:
        if m.get("slug"):
            index[m["slug"]] = f"matches/{m['slug']}.html"
    for slug in theme_slugs:
        index[slug] = f"themes/{slug}.html"
    return index


def _timeline_range(records: list[dict], date_field: str,
                    pad: int = 2) -> tuple[int, int]:
    """Derive a [start, end] year range from the records' dates, padded by ±pad.

    Falls back to 1900–1940 when no dated records are present.
    """
    years = [y for y in (_year_from_dt(r.get(date_field)) for r in records) if y]
    if not years:
        return 1900, 1940
    return min(years) - pad, max(years) + pad


def _timeline_svg(records: list[dict], date_field: str, label_field: str,
                  entity_field: str, entity_colors: dict[int, str],
                  year_start: int | None = None, year_end: int | None = None) -> str:
    if year_start is None or year_end is None:
        year_start, year_end = _timeline_range(records, date_field)
    width, height = 880, 90
    pad_l, pad_r, pad_t, pad_b = 40, 20, 20, 30
    span = year_end - year_start or 1

    def x(dt: date | None) -> float:
        if not dt:
            return -99
        return pad_l + (dt.year + dt.month / 12 - year_start) / span * (width - pad_l - pad_r)

    axis_y = pad_t + 36
    svg = [f'<svg viewBox="0 0 {width} {height}" class="timeline-svg">']
    svg.append(f'<line x1="{pad_l}" y1="{axis_y}" x2="{width - pad_r}" y2="{axis_y}" '
               f'stroke="#bbb" stroke-width="1"/>')

    first_tick = year_start + (-year_start % 5)  # first multiple of 5 within range
    for y in range(first_tick, year_end + 1, 5):
        tx = pad_l + (y - year_start) / span * (width - pad_l - pad_r)
        svg.append(f'<line x1="{tx:.1f}" y1="{axis_y}" x2="{tx:.1f}" y2="{axis_y + 5}" '
                   f'stroke="#bbb" stroke-width="1"/>')
        svg.append(f'<text x="{tx:.1f}" y="{axis_y + 16}" '
                   f'text-anchor="middle" font-size="9" fill="#888">{y}</text>')

    for rec in records:
        dt = rec.get(date_field)
        if not dt:
            continue
        rx = x(dt)
        color = entity_colors.get(rec.get(entity_field, 0), "#8b5e3c")
        label = _esc(str(rec.get(label_field) or rec.get("serial_no") or rec.get("patent_no", "")))
        svg.append(
            f'<circle cx="{rx:.1f}" cy="{axis_y - 8}" r="4" fill="{color}" opacity="0.75">'
            f'<title>{label} ({dt})</title></circle>'
        )

    svg.append('</svg>')
    return "\n".join(svg)


def _timeline_layout(records: list[dict], date_field: str,
                     card_fn: "callable") -> str:
    """Vertical scroll timeline: records grouped by year (oldest→newest) in a
    left-rail layout, each year's cards in a grid to its right. Time advances as
    the reader scrolls down. `card_fn(rec) -> str` renders one card.

    Returns '' when there are no records (caller supplies the empty state).
    """
    from itertools import groupby

    def _yr(r: dict) -> int | None:
        return _year_from_dt(r.get(date_field))

    dated   = sorted((r for r in records if _yr(r) is not None), key=_yr)
    undated = [r for r in records if _yr(r) is None]

    rows: list[str] = []
    for year, group in groupby(dated, key=_yr):
        cards = "".join(card_fn(r) for r in group)
        rows.append(
            f'<div class="tl-row"><div class="tl-year">{year}</div>'
            f'<div class="tl-cards card-grid">{cards}</div></div>'
        )
    if undated:
        cards = "".join(card_fn(r) for r in undated)
        rows.append(
            f'<div class="tl-row"><div class="tl-year tl-year--undated">undated</div>'
            f'<div class="tl-cards card-grid">{cards}</div></div>'
        )
    if not rows:
        return ""
    return f'<div class="timeline-layout">{"".join(rows)}</div>'


def _entity_color_map(entity_ids: list[int]) -> dict[int, str]:
    palette = ["#8b5e3c", "#5a7a3e", "#3e5a8b", "#7a3e5a", "#3e7a6b", "#7a6b3e"]
    return {eid: palette[i % len(palette)] for i, eid in enumerate(entity_ids)}

