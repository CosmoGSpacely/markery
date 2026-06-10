"""HTML page generators for the Markery research site."""

from __future__ import annotations

import base64
import re
from datetime import date
from pathlib import Path

from markery.common.project import Project
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
.site-header nav {
  overflow-x: auto;
  white-space: nowrap;
  -webkit-overflow-scrolling: touch;
  flex: 1;
  min-width: 0;
}
.site-header nav a {
  color: #b8a88a;
  text-decoration: none;
  font-size: .85em;
  margin-right: 16px;
}
.site-header nav a:hover { color: #f5f0e8; }

/* ── Breadcrumb ── */
.breadcrumb {
  padding: 8px 40px;
  background: #ede8de;
  border-bottom: 1px solid #ddd;
  font-size: .78em;
}
.breadcrumb ol { list-style: none; display: flex; flex-wrap: wrap; gap: 0; margin: 0; padding: 0; }
.breadcrumb li { color: #888; }
.breadcrumb li:not(:last-child)::after { content: "›"; margin: 0 8px; color: #b8a88a; }
.breadcrumb a { color: #5a3e28; text-decoration: none; }
.breadcrumb a:hover { text-decoration: underline; }

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
.card--focus {
  border: 2px solid #5a3e28;
  box-shadow: 0 2px 8px rgba(90,62,40,.18);
}
.focus-badge {
  display: inline-block;
  background: #5a3e28;
  color: #f5f0e8;
  font-size: .65em;
  padding: 1px 6px;
  border-radius: 10px;
  margin-top: 2px;
  font-family: monospace;
}
.research-question {
  background: #ede8de;
  border-left: 4px solid #8b5e3c;
  padding: 16px 20px;
  margin-bottom: 32px;
  max-width: 700px;
}
.research-question .rq-label {
  display: block;
  font-size: .72em;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #8b5e3c;
  margin-bottom: 8px;
}
.research-question p { margin-bottom: .7em; }
.research-question p:last-child { margin-bottom: 0; }
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

/* ── Timeline annotation page ── */
.timeline-entries { max-width: 700px; margin-top: 40px; }
.timeline-entries h3 {
  font-size: 1.05em;
  font-weight: bold;
  color: #3d2b1a;
  margin: 32px 0 6px;
  border-left: 3px solid #8b5e3c;
  padding-left: 10px;
}
.timeline-entries p { margin-bottom: .8em; }

/* ── Thematic essay ── */
.theme-essay { max-width: 700px; }
.theme-essay h2 { font-size: 1.2em; font-weight: normal; margin: 32px 0 10px; color: #3d2b1a; }
.theme-essay h3 { font-size: 1.05em; font-weight: normal; margin: 24px 0 8px; color: #5a3e28; }
.theme-essay p { margin-bottom: 1em; }
.theme-essay table { width: 100%; border-collapse: collapse; font-size: .88em; margin: 16px 0; }
.theme-essay th, .theme-essay td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #ddd; }
.theme-essay th { background: #ede8de; font-weight: normal; color: #555; }

/* ── Search page ── */
.search-form { display: flex; gap: 8px; margin-bottom: 32px; }
.search-form input[type=search] {
  flex: 1; padding: 8px 12px; border: 1px solid #ccc; border-radius: 3px;
  font-size: 1em; font-family: Georgia, serif; background: #fff;
}
.search-form button {
  padding: 8px 18px; background: #5a3e28; color: #f5f0e8;
  border: none; border-radius: 3px; cursor: pointer; font-size: .9em;
}
.search-results { list-style: none; }
.search-results li { margin-bottom: 20px; }
.search-results .result-title { font-size: 1.05em; font-weight: bold; }
.search-results .result-type { font-size: .75em; color: #888; font-family: monospace; margin-left: 6px; }
.search-results .result-excerpt { font-size: .88em; color: #444; margin-top: 4px; }

/* ── Search input in header ── */
.site-search { margin-left: auto; }
.site-search input[type=search] {
  padding: 3px 8px; border: 1px solid #555; border-radius: 3px;
  background: #1a1208; color: #e8dcc8; font-size: .8em; width: 140px;
}
.site-search input[type=search]::placeholder { color: #888; }

/* ── Patent figure (embedded via [[figure:patent_no]]) ── */
.patent-figure { margin: 24px auto; text-align: center; max-width: 600px; border: 1px solid #d4c9b0; border-radius: 4px; padding: 8px; }
.patent-figure img { max-width: 100%; background: #faf8f4; display: block; margin: 0 auto; }
.patent-figure figcaption { font-size: .78em; color: #888; margin-top: 6px; font-style: italic; font-family: Georgia, 'Times New Roman', serif; }

/* ── Blockquotes ── */
blockquote { border-left: 3px solid #b8a88a; margin: 16px 0; padding: 8px 16px; color: #555; font-style: italic; }
blockquote p { margin: 0; }

/* ── Small chip (inline stat tags) ── */
.chip-sm { font-size: .75em; background: #e8dcc8; border-radius: 3px; padding: 1px 6px; color: #5a3e28; white-space: nowrap; }

/* ── Site footer ── */
.site-footer {
  margin-top: 48px; padding: 20px 24px; border-top: 1px solid #ddd;
  font-size: .78em; color: #888; text-align: center;
}
.site-footer a { color: #8b5e3c; text-decoration: none; }
.site-footer a:hover { text-decoration: underline; }
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
) -> str:
    prefix = "../" * depth
    nav = "".join(
        f'<a href="{prefix}{href}">{_esc(label)}</a>'
        for label, href in nav_links.items()
    )
    og_tags = ""
    if og:
        og_tags = (
            f'<meta property="og:title"       content="{_esc(og.get("title", title))}">\n'
            f'<meta property="og:description" content="{_esc(og.get("description", ""))}">\n'
            f'<meta property="og:url"         content="{_esc(og.get("url", ""))}">\n'
            f'<meta property="og:type"        content="article">\n'
        )
    repo = site_repo or _MARKERY_REPO
    footer = (
        f'\n<footer class="site-footer">'
        f'Built with <a href="{_esc(repo)}">Markery</a>'
        f'</footer>\n'
    )
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{_esc(title)}</title>\n'
        + og_tags
        + f'<style>{_CSS}</style>\n'
        '</head>\n<body>\n'
        f'<header class="site-header">'
        f'<a class="site-title" href="{prefix}index.html">Markery Research</a>'
        f'<nav>{nav}</nav>'
        f'<form class="site-search" action="{prefix}search.html" method="get">'
        f'<input type="search" name="q" placeholder="Search…" aria-label="Search"></form>'
        '</header>\n'
        + body
        + footer
        + '</body>\n</html>\n'
    )


def _nav_links(
    project: str,
    entities: list[dict],
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    links: dict[str, str] = {
        "Trademarks": "trademarks.html",
        "Patents": "patents.html",
    }
    for e in entities:
        links[e["canonical_name"]] = f"entities/{e['slug']}.html"
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
            html_parts.append(f'<li>{_inline(re.sub(r"^\d+\.\s+", "", line))}</li>')
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
        src = _img_src("mark", str(m["trademark_serial"]), 0, images_dir) if m.get("has_image") else None
        if src:
            thumb = f'<img class="match-card-thumb" loading="lazy" src="{src}" alt="{_esc(m["trademark"])}">'
        else:
            thumb = f'<div class="match-card-thumb-placeholder">{_esc(m["trademark"][:3])}</div>'

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
            f'<div class="match-card-title">{_esc(m["trademark"])} ↔ {_esc(m["patent_no"])}</div>'
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
        f'<span class="chip">{len(entities)} entities</span>'
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
        + f'<p class="section-title">Entities</p>'
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
) -> Path:
    slug = entity["slug"]
    narrative = _read_narrative(Project(project).content / f"entity-{slug}.md",
                                link_index=link_index, depth=1)
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
    out_path.write_text(_page(_page_title(entity["canonical_name"], project), body, nav, depth=1, og=og), encoding="utf-8")
    return out_path


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
    trail: list[tuple[str, str | None]] = [("Home", "../index.html")]
    if entity_slug and match.get("entity"):
        trail.append((match["entity"], f'../entities/{entity_slug}.html'))
    trail.append((crumb_title, None))
    breadcrumb = _breadcrumb(trail)

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
    out_path.write_text(_page(_page_title("Sources", project), body, nav, og=og), encoding="utf-8")
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
    out_path.write_text(_page(_page_title("Timeline", project), body, nav, og=og), encoding="utf-8")
    return out_path


def render_search_page(
    project: str,
    out_dir: Path,
    entities: list[dict],
    extra_nav: dict[str, str] | None = None,
) -> Path:
    """Render a client-side search page backed by search.json."""
    nav  = _nav_links(project, entities, extra_nav)

    search_js = r"""
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
        f'<script>{search_js}</script>'
        f'</div>'
    )

    out_path = out_dir / "search.html"
    out_path.write_text(_page(_page_title("Search", project), body, nav), encoding="utf-8")
    return out_path
