"""HTML page generators for the Markery research site."""

from __future__ import annotations

import base64
import re
from datetime import date
from pathlib import Path

from markery.common.config import Project
from markery.specialist.publisher.queries import get_mark_image_b64, get_patent_figure_b64

# ---------------------------------------------------------------------------
# Shared CSS
# ---------------------------------------------------------------------------

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: Georgia, 'Times New Roman', serif;
  background: #f5f0e8;
  color: #1a1a1a;
  line-height: 1.65;
  font-size: 16px;
}

a { color: #5a3e28; text-decoration: underline; }
a:hover { color: #8b5e3c; }

/* ── Site header ── */
.site-header {
  background: #2a1f14;
  color: #f5f0e8;
  padding: 18px 40px;
  display: flex;
  align-items: baseline;
  gap: 24px;
}
.site-header .site-title {
  font-size: 1.1em;
  font-weight: normal;
  letter-spacing: .04em;
  color: #e8dcc8;
  text-decoration: none;
}
.site-header nav a {
  color: #b8a88a;
  text-decoration: none;
  font-size: .85em;
  margin-right: 16px;
}
.site-header nav a:hover { color: #f5f0e8; }

/* ── Page header ── */
.page-header {
  background: #3d2b1a;
  color: #f5f0e8;
  padding: 40px;
}
.page-header h1 {
  font-size: 2em;
  font-weight: normal;
  margin-bottom: 6px;
}
.page-header .subtitle {
  color: #b8a88a;
  font-size: .95em;
}
.page-header .stat-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}
.chip {
  background: rgba(255,255,255,.1);
  border: 1px solid rgba(255,255,255,.2);
  color: #e8dcc8;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: .8em;
  font-family: monospace;
}

/* ── Page body ── */
.page-body { max-width: 960px; margin: 0 auto; padding: 48px 40px; }

.narrative {
  max-width: 700px;
  margin-bottom: 40px;
}
.narrative h2 {
  font-size: 1.2em;
  font-weight: normal;
  margin: 32px 0 10px;
  color: #3d2b1a;
}
.narrative p { margin-bottom: 1em; }
.narrative table {
  width: 100%;
  border-collapse: collapse;
  font-size: .88em;
  margin: 16px 0;
}
.narrative th, .narrative td {
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid #ddd;
}
.narrative th { background: #ede8de; font-weight: normal; color: #555; }
.narrative code {
  font-family: monospace;
  font-size: .88em;
  background: #ede8de;
  padding: 1px 4px;
  border-radius: 2px;
}
.narrative pre {
  background: #ede8de;
  padding: 14px;
  overflow-x: auto;
  margin: 12px 0;
  font-size: .83em;
}

/* ── Timeline ── */
.timeline-section { margin-bottom: 40px; }
.timeline-section h2 {
  font-size: 1em;
  font-weight: normal;
  color: #555;
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-bottom: 12px;
}
.timeline-svg { width: 100%; overflow: visible; }

/* ── Card grid ── */
.section-title {
  font-size: 1em;
  font-weight: normal;
  color: #555;
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-bottom: 16px;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.card {
  background: white;
  border-radius: 5px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.card-image {
  width: 100%;
  height: 140px;
  object-fit: contain;
  background: #faf8f4;
  border-bottom: 1px solid #eee;
  display: block;
}
.card-image-placeholder {
  width: 100%;
  height: 140px;
  background: #ede8de;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: .75em;
  font-family: monospace;
  border-bottom: 1px solid #eee;
}
.card-body { padding: 10px 12px; flex: 1; display: flex; flex-direction: column; gap: 4px; }
.card-name { font-weight: bold; font-size: .88em; line-height: 1.3; }
.card-meta { font-size: .75em; color: #666; }
.card-goods { font-size: .73em; color: #444; margin-top: 4px; line-height: 1.4;
  border-top: 1px solid #eee; padding-top: 4px; }
.card-footer { font-size: .7em; color: #999; font-family: monospace; margin-top: auto; padding-top: 4px; }
.entity-badge {
  display: inline-block;
  background: #e8dcc8;
  color: #5a3e28;
  font-size: .68em;
  padding: 1px 6px;
  border-radius: 10px;
  margin-top: 2px;
  font-family: monospace;
}
.match-link {
  display: inline-block;
  background: #5a3e28;
  color: #f5f0e8;
  font-size: .68em;
  padding: 2px 8px;
  border-radius: 3px;
  text-decoration: none;
  margin-top: 4px;
}
.match-link:hover { background: #8b5e3c; color: #f5f0e8; }

/* ── Entity grid ── */
.entity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.entity-card {
  background: white;
  border-radius: 5px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
  padding: 20px;
}
.entity-card h3 { font-size: 1.1em; font-weight: normal; margin-bottom: 8px; }
.entity-card .entity-meta { font-size: .8em; color: #666; margin-bottom: 12px; }
.entity-card .entity-stats {
  display: flex;
  gap: 16px;
  font-size: .78em;
  color: #444;
  margin-bottom: 12px;
}
.entity-card .stat-val { font-weight: bold; color: #2a1f14; }
.entity-card .links a { font-size: .82em; margin-right: 12px; }

/* ── Match cards (landing page) ── */
.match-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.match-card {
  background: white;
  border-radius: 5px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
  display: flex;
  gap: 16px;
  padding: 16px;
}
.match-card-thumb {
  width: 80px;
  min-width: 80px;
  height: 80px;
  object-fit: contain;
  background: #faf8f4;
  border: 1px solid #eee;
  border-radius: 3px;
}
.match-card-thumb-placeholder {
  width: 80px;
  min-width: 80px;
  height: 80px;
  background: #ede8de;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  font-size: .7em;
}
.match-card-body { flex: 1; }
.match-card-title { font-weight: bold; font-size: .95em; margin-bottom: 4px; }
.match-card-meta { font-size: .78em; color: #666; margin-bottom: 8px; }
.match-card-note { font-size: .8em; color: #444; line-height: 1.4; margin-bottom: 8px; }

/* ── Essay page ── */
.essay { max-width: 700px; }
.essay h2 { font-size: 1.2em; font-weight: normal; margin: 36px 0 10px; color: #3d2b1a; }
.essay p { margin-bottom: 1em; }
.essay table { width: 100%; border-collapse: collapse; font-size: .88em; margin: 16px 0; }
.essay th, .essay td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #ddd; }
.essay th { background: #ede8de; font-weight: normal; color: #555; }
.essay pre { background: #ede8de; padding: 14px; overflow-x: auto; margin: 12px 0; font-size: .83em; }
.essay code { font-family: monospace; font-size: .88em; background: #ede8de; padding: 1px 4px; border-radius: 2px; }
.essay-media {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 24px 0;
}
.essay-media img {
  width: 100%;
  object-fit: contain;
  border: 1px solid #ddd;
  background: #faf8f4;
}
.essay-media .media-label { font-size: .75em; color: #888; margin-top: 4px; text-align: center; }
.sources {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid #ddd;
  font-size: .82em;
  color: #555;
}
.sources h2 { font-size: .95em; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 12px; }
.sources dt { font-weight: bold; margin-top: 8px; }
.sources dd { margin-left: 16px; }
"""

# ---------------------------------------------------------------------------
# Shared components
# ---------------------------------------------------------------------------

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


def _page(title: str, body: str, nav_links: dict[str, str], depth: int = 0) -> str:
    prefix = "../" * depth
    nav = "".join(
        f'<a href="{prefix}{href}">{_esc(label)}</a>'
        for label, href in nav_links.items()
    )
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{_esc(title)}</title>\n'
        f'<style>{_CSS}</style>\n'
        '</head>\n<body>\n'
        f'<header class="site-header">'
        f'<a class="site-title" href="{prefix}index.html">Markery Research</a>'
        f'<nav>{nav}</nav>'
        '</header>\n'
        + body
        + '\n</body>\n</html>\n'
    )


def _nav_links(project: str, entities: list[dict]) -> dict[str, str]:
    links: dict[str, str] = {
        "Trademarks": "trademarks.html",
        "Patents": "patents.html",
    }
    for e in entities:
        links[e["canonical_name"]] = f"entities/{e['slug']}.html"
    return links


def _render_markdown(text: str) -> str:
    """Minimal Markdown → HTML: headings, paragraphs, bold, inline code, fenced blocks."""
    # Extract fenced blocks before line processing so they don't get _esc()'d.
    blocks: dict[str, str] = {}

    def _stash(m: re.Match) -> str:
        key = f"\x00BLOCK{len(blocks)}\x00"
        blocks[key] = f'<pre><code>{_esc(m.group(1))}</code></pre>'
        return key

    text = re.sub(r'```[^\n]*\n(.*?)```', _stash, text, flags=re.DOTALL)

    lines = text.split("\n")
    html_parts: list[str] = []
    in_para = False

    for line in lines:
        if line.startswith("## "):
            if in_para:
                html_parts.append("</p>")
                in_para = False
            html_parts.append(f'<h2>{_esc(line[3:])}</h2>')
        elif line.startswith("### "):
            if in_para:
                html_parts.append("</p>")
                in_para = False
            html_parts.append(f'<h3>{_esc(line[4:])}</h3>')
        elif line.startswith("# "):
            if in_para:
                html_parts.append("</p>")
                in_para = False
            html_parts.append(f'<h2>{_esc(line[2:])}</h2>')
        elif line.strip() == "":
            if in_para:
                html_parts.append("</p>")
                in_para = False
        elif line.startswith("\x00BLOCK"):
            if in_para:
                html_parts.append("</p>")
                in_para = False
            html_parts.append(blocks[line])
        else:
            processed = _esc(line)
            processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', processed)
            processed = re.sub(r'`(.+?)`', r'<code>\1</code>', processed)
            if not in_para:
                html_parts.append("<p>")
                in_para = True
            html_parts.append(processed + " ")

    if in_para:
        html_parts.append("</p>")

    return "\n".join(html_parts)


def _read_narrative(path: Path) -> str:
    if path.exists():
        return _render_markdown(path.read_text())
    return (
        f'<p style="color:#999;font-style:italic">'
        f'Narrative not yet written. See <code>{path}</code> for the content schema.</p>'
    )


def _timeline_svg(records: list[dict], date_field: str, label_field: str,
                  entity_field: str, entity_colors: dict[int, str],
                  year_start: int = 1900, year_end: int = 1940) -> str:
    width, height = 880, 90
    pad_l, pad_r, pad_t, pad_b = 40, 20, 20, 30
    span = year_end - year_start

    def x(dt: date | None) -> float:
        if not dt:
            return -99
        return pad_l + (dt.year + dt.month / 12 - year_start) / span * (width - pad_l - pad_r)

    axis_y = pad_t + 36
    svg = [f'<svg viewBox="0 0 {width} {height}" class="timeline-svg">']
    svg.append(f'<line x1="{pad_l}" y1="{axis_y}" x2="{width - pad_r}" y2="{axis_y}" '
               f'stroke="#bbb" stroke-width="1"/>')

    for y in range(year_start, year_end + 1, 5):
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


def _entity_color_map(entity_ids: list[int]) -> dict[int, str]:
    palette = ["#8b5e3c", "#5a7a3e", "#3e5a8b", "#7a3e5a", "#3e7a6b", "#7a6b3e"]
    return {eid: palette[i % len(palette)] for i, eid in enumerate(entity_ids)}


# ---------------------------------------------------------------------------
# Page generators
# ---------------------------------------------------------------------------

def render_landing(
    project: str,
    entities: list[dict],
    trademarks: list[dict],
    patents: list[dict],
    matches: list[dict],
    entity_stats: dict[int, dict],
    out_dir: Path,
) -> Path:
    narrative = _read_narrative(Project(project).content / "index-narrative.md")
    nav = _nav_links(project, entities)

    match_cards = []
    for m in matches:
        img_b64 = get_mark_image_b64(str(m["trademark_serial"])) if m.get("has_image") else None
        if img_b64:
            thumb = f'<img class="match-card-thumb" src="data:image/png;base64,{img_b64}" alt="{_esc(m["trademark"])}">'
        else:
            thumb = f'<div class="match-card-thumb-placeholder">{_esc(m["trademark"][:3])}</div>'

        essay_link = ""
        if m.get("essay_path"):
            essay_link = f'<a href="matches/{m["slug"]}.html">Read essay →</a>'

        grant = m.get("grant_dt", "")
        filed = m.get("filing_dt", "")
        match_cards.append(
            f'<div class="match-card">'
            f'{thumb}'
            f'<div class="match-card-body">'
            f'<div class="match-card-title">{_esc(m["trademark"])} ↔ {_esc(m["patent_no"])}</div>'
            f'<div class="match-card-meta">{_esc(m.get("entity", ""))} · '
            f'Patent {grant} · Mark filed {filed}</div>'
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
        f'<span class="chip">{len(entities)} entities</span>'
        f'<span class="chip">{len(trademarks)} marks</span>'
        f'<span class="chip">{len(patents)} patents</span>'
        f'<span class="chip">{len(matches)} confirmed pairs</span>'
    )

    body = (
        f'<div class="page-header">'
        f'<h1>{_esc(project.replace("-", " ").title())}</h1>'
        f'<div class="subtitle">USPTO Patent-Trademark Research Project · 1900–1939</div>'
        f'<div class="stat-chips">{stat_chips}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="narrative">{narrative}</div>'
        + (f'<p class="section-title">Confirmed Pairs</p>'
           f'<div class="match-cards">{"".join(match_cards)}</div>' if match_cards else '')
        + f'<p class="section-title">Entities</p>'
        f'<div class="entity-grid">{"".join(entity_cards)}</div>'
        f'</div>'
    )

    out_path = out_dir / "index.html"
    out_path.write_text(_page(f"{project.replace('-', ' ').title()} — Markery", body, nav), encoding="utf-8")
    return out_path


def render_trademark_gallery(
    project: str,
    entities: list[dict],
    trademarks: list[dict],
    matches: list[dict],
    entity_colors: dict[int, str],
    out_dir: Path,
) -> Path:
    narrative = _read_narrative(Project(project).content / "trademarks-narrative.md")
    nav = _nav_links(project, entities)
    match_serials = {str(m["trademark_serial"]): m["slug"] for m in matches if m.get("essay_path")}

    timeline = _timeline_svg(trademarks, "filing_dt", "mark_name", "entity_id", entity_colors)

    cards = []
    for tm in trademarks:
        sn = tm["serial_no"]
        img_b64 = get_mark_image_b64(sn) if tm.get("image_available") else None
        if img_b64:
            img_html = f'<img class="card-image" src="data:image/png;base64,{img_b64}" alt="{_esc(tm["mark_name"])}">'
        else:
            img_html = f'<div class="card-image-placeholder">{_esc(sn)}</div>'

        match_slug = match_serials.get(sn)
        match_html = (f'<a class="match-link" href="matches/{match_slug}.html">Confirmed pair →</a>'
                      if match_slug else "")

        filing = tm["filing_dt"].strftime("%B %d, %Y") if tm["filing_dt"] else ""
        status = _STATUS_LABELS.get(tm["status_cd"], str(tm["status_cd"]) if tm["status_cd"] else "")
        goods = (tm.get("goods") or "")[:120] + ("…" if (tm.get("goods") or "") and len(tm.get("goods", "")) > 120 else "")

        cards.append(
            f'<div class="card" id="sn-{sn}">'
            f'{img_html}'
            f'<div class="card-body">'
            f'<div class="card-name">{_esc(tm["mark_name"] or "(design mark)")}</div>'
            f'<div class="card-meta">Filed {_esc(filing)} · {_esc(status)}</div>'
            f'<span class="entity-badge">{_esc(tm["entity_name"])}</span>'
            f'<div class="card-goods">{_esc(goods)}</div>'
            f'{match_html}'
            f'<div class="card-footer">{_esc(sn)} · Draw {_esc(tm["draw_cd"])}</div>'
            f'</div></div>'
        )

    stat_chips = (
        f'<span class="chip">{len(trademarks)} marks</span>'
        f'<span class="chip">{sum(1 for t in trademarks if t["image_available"])} with images</span>'
        f'<span class="chip">{len(match_serials)} confirmed pairs</span>'
    )

    body = (
        f'<div class="page-header">'
        f'<h1>Trademark Gallery</h1>'
        f'<div class="subtitle">{_esc(project.replace("-", " ").title())}</div>'
        f'<div class="stat-chips">{stat_chips}</div>'
        f'</div>'
        f'<div class="page-body">'
        f'<div class="narrative">{narrative}</div>'
        f'<div class="timeline-section"><p class="section-title">Filing Timeline</p>{timeline}</div>'
        f'<p class="section-title">All Marks</p>'
        f'<div class="card-grid">{"".join(cards)}</div>'
        f'</div>'
    )

    out_path = out_dir / "trademarks.html"
    out_path.write_text(_page("Trademark Gallery", body, nav), encoding="utf-8")
    return out_path


def render_patent_gallery(
    project: str,
    entities: list[dict],
    patents: list[dict],
    matches: list[dict],
    entity_colors: dict[int, str],
    out_dir: Path,
) -> Path:
    narrative = _read_narrative(Project(project).content / "patents-narrative.md")
    nav = _nav_links(project, entities)
    match_patents = {m["patent_no"]: m["slug"] for m in matches if m.get("essay_path")}

    timeline = _timeline_svg(patents, "grant_dt", "title", "entity_id", entity_colors)

    cards = []
    for pat in patents:
        pn = pat["patent_no"]
        fig_b64 = get_patent_figure_b64(pn) if pat.get("figure_available") else None
        if fig_b64:
            img_html = f'<img class="card-image" src="data:image/png;base64,{fig_b64}" alt="{_esc(pn)}">'
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
        f'<div class="narrative">{narrative}</div>'
        f'<div class="timeline-section"><p class="section-title">Grant Timeline</p>{timeline}</div>'
        f'<p class="section-title">All Patents</p>'
        f'<div class="card-grid">{"".join(cards)}</div>'
        f'</div>'
    )

    out_path = out_dir / "patents.html"
    out_path.write_text(_page("Patent Gallery", body, nav), encoding="utf-8")
    return out_path


def render_entity_page(
    project: str,
    entity: dict,
    entities: list[dict],
    trademarks: list[dict],
    patents: list[dict],
    matches: list[dict],
    stats: dict,
    out_dir: Path,
) -> Path:
    slug = entity["slug"]
    narrative = _read_narrative(Project(project).content / f"entity-{slug}.md")
    nav = _nav_links(project, entities)

    variants_rows = "".join(
        f'<tr><td>{_esc(v["name"])}</td><td>{_esc(v["source"])}</td></tr>'
        for v in entity.get("name_variants", [])
    )
    variants_table = (
        f'<table><thead><tr><th>Name variant</th><th>Source</th></tr></thead>'
        f'<tbody>{variants_rows}</tbody></table>'
    ) if variants_rows else ""

    match_links = "".join(
        f'<li><a href="../matches/{m["slug"]}.html">'
        f'{_esc(m["trademark"])} ↔ {_esc(m["patent_no"])}</a></li>'
        for m in matches if m.get("essay_path")
    )
    match_section = (
        f'<h2>Confirmed Pairs</h2><ul>{match_links}</ul>'
    ) if match_links else ""

    stat_chips = (
        f'<span class="chip">{stats.get("trademark_count", 0)} marks</span>'
        f'<span class="chip">{stats.get("patent_count", 0)} patents</span>'
        f'<span class="chip">{stats.get("match_count", 0)} confirmed</span>'
        + (f'<span class="chip">{stats["active_from"]}–{stats["active_to"]}</span>'
           if stats.get("active_from") else '')
    )

    body = (
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

    (out_dir / "entities").mkdir(exist_ok=True)
    out_path = out_dir / "entities" / f"{slug}.html"
    out_path.write_text(_page(_esc(entity["canonical_name"]), body, nav, depth=1), encoding="utf-8")
    return out_path


def render_match_essay(
    project: str,
    match: dict,
    entities: list[dict],
    out_dir: Path,
) -> Path:
    slug = match["slug"]
    nav = _nav_links(project, entities)

    if match.get("essay_path") and Path(match["essay_path"]).exists():
        essay_md = _render_markdown(Path(match["essay_path"]).read_text())
    else:
        essay_md = (
            f'<p style="color:#999;font-style:italic">'
            f'Essay not yet written. See <code>content-schemas/match-narrative.md</code>.</p>'
        )

    mark_img = get_mark_image_b64(str(match["trademark_serial"]))
    fig_img  = get_patent_figure_b64(match["patent_no"])

    media = ""
    if mark_img or fig_img:
        media_parts = []
        if mark_img:
            media_parts.append(
                f'<div><img src="data:image/png;base64,{mark_img}" alt="{_esc(match["trademark"])}">'
                f'<div class="media-label">{_esc(match["trademark"])} · Serial {_esc(str(match["trademark_serial"]))}</div>'
                f'</div>'
            )
        if fig_img:
            media_parts.append(
                f'<div><img src="data:image/png;base64,{fig_img}" alt="{_esc(match["patent_no"])}">'
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

    stat_chips = (
        f'<span class="chip">{_esc(match.get("entity", ""))}</span>'
        f'<span class="chip">Patent {match.get("grant_dt", "")}</span>'
        f'<span class="chip">Mark filed {match.get("filing_dt", "")}</span>'
    )

    body = (
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

    (out_dir / "matches").mkdir(exist_ok=True)
    out_path = out_dir / "matches" / f"{slug}.html"
    out_path.write_text(_page(f"{match['trademark']} ↔ {match['patent_no']}", body, nav, depth=1), encoding="utf-8")
    return out_path
