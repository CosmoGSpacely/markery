"""Annual design-mark review pages (Phase 24 P4).

A year landing page links twelve monthly galleries of USPTO *design* marks
(mark_draw_cd LIKE '3%') by filing month. Rendered in the site chrome and built
under ``site/reviews/<year>/`` so each annual review can be a card on the Markery
root portal. Replaces the earlier ad-hoc monthly cadence with an annual one.
"""
from __future__ import annotations

import calendar
from pathlib import Path

import duckdb

from markery.common import config
from markery.specialist.publisher import queries as q
from markery.specialist.publisher.render.components import _esc, _page, _page_title

_MONTHS = ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]


def design_marks(year: int, month: int) -> list[dict]:
    """Design marks (mark_draw_cd LIKE '3%') filed in the given year/month."""
    last = calendar.monthrange(year, month)[1]
    conn = duckdb.connect(str(config.DB["trademarks"]), read_only=True)
    rows = conn.execute(f"""
        SELECT cf.serial_no, cf.mark_id_char, cf.filing_dt,
               o.own_name, o.own_addr_state_cd,
               gs.goods,
               CASE WHEN mi.file IS NOT NULL THEN 1 ELSE 0 END AS has_img
        FROM case_file cf
        LEFT JOIN (
            SELECT serial_no, own_name, own_addr_state_cd FROM owner
            WHERE own_id IN (SELECT MIN(own_id) FROM owner GROUP BY serial_no)
        ) o ON cf.serial_no = o.serial_no
        LEFT JOIN (
            SELECT serial_no, string_agg(statement_text, ' ') AS goods
            FROM statement WHERE statement_type_cd LIKE 'GS%' GROUP BY serial_no
        ) gs ON cf.serial_no = gs.serial_no
        LEFT JOIN mark_images mi ON cf.serial_no = mi.serial_no
        WHERE cf.mark_draw_cd LIKE '3%'
          AND cf.filing_dt BETWEEN DATE '{year}-{month:02d}-01'
                               AND DATE '{year}-{month:02d}-{last:02d}'
        ORDER BY cf.filing_dt, cf.serial_no
    """).fetchall()
    conn.close()
    return [
        {"serial": str(r[0]), "mark": r[1] or "", "filing": r[2],
         "owner": r[3] or "", "state": r[4] or "", "goods": r[5] or "",
         "has_img": bool(r[6])}
        for r in rows
    ]


def _card(m: dict, img_rel: str | None) -> str:
    if img_rel:
        inner = f'<img class="card-image" loading="lazy" src="{img_rel}" alt="{_esc(m["mark"] or m["serial"])}">'
    else:
        inner = f'<div class="card-image-placeholder">{_esc(m["mark"] or m["serial"])}</div>'
    owner = m["owner"] + (f' · {m["state"]}' if m["state"] else "")
    filing = m.get("filing")
    filing_str = filing.strftime("%B %d, %Y") if hasattr(filing, "strftime") else (str(filing) if filing else "")
    goods_full = m.get("goods") or ""
    goods = goods_full[:120] + ("…" if len(goods_full) > 120 else "")
    goods_attr = f' title="{_esc(goods_full)}"' if goods_full else ""
    goods_html = f'<div class="card-goods"{goods_attr}>{_esc(goods)}</div>' if goods_full else ""
    return (
        f'<div class="card" id="sn-{m["serial"]}">{inner}'
        f'<div class="card-body">'
        f'<div class="card-name">{_esc(m["mark"] or "(design mark)")}</div>'
        f'<div class="card-meta">{_esc(owner)}</div>'
        f'<div class="card-meta">Filed {_esc(filing_str)}</div>'
        f'{goods_html}'
        f'<div class="card-footer">{_esc(m["serial"])}</div>'
        f'</div></div>'
    )


def render_review_month(
    year: int, month: int, year_dir: Path, base_url: str | None = None,
) -> tuple[Path, dict, list[Path]]:
    """Render one month's design-mark gallery → reviews/<year>/<mm>.html.

    Returns (path, summary, written_image_paths).
    """
    marks = design_marks(year, month)
    img_dir = year_dir / "img"
    written: list[Path] = []
    thumb: str | None = None
    cards: list[str] = []
    for m in marks:
        img_rel = None
        if m["has_img"]:
            data = q.get_mark_image_bytes(m["serial"])
            if data:
                img_dir.mkdir(parents=True, exist_ok=True)
                dest = img_dir / f"{m['serial']}.png"
                dest.write_bytes(data)
                written.append(dest.resolve())
                img_rel = f"img/{m['serial']}.png"
                if thumb is None:
                    thumb = m["serial"]
        cards.append(_card(m, img_rel))

    name = f"{_MONTHS[month]} {year}"
    grid = (f'<div class="card-grid">{"".join(cards)}</div>'
            if cards else '<p class="empty-state">No design marks filed this month.</p>')
    body = (
        f'<div class="page-header"><h1>{name}</h1>'
        f'<div class="subtitle">Design marks · {len(marks)} filed</div></div>'
        f'<div class="page-body">'
        f'<p class="breadcrumb-inline"><a href="index.html">← {year} review</a></p>'
        f'{grid}</div>'
    )
    out_path = year_dir / f"{month:02d}.html"
    out_path.write_text(
        _page(_page_title(name, "design-mark-review"), body, {}, depth=2,
              project=None),
        encoding="utf-8",
    )
    summary = {
        "month": month, "name": name, "count": len(marks),
        "with_images": sum(1 for m in marks if m["has_img"]),
        "href": f"{month:02d}.html", "thumb": thumb,
    }
    return out_path, summary, written


def render_review_year(
    year: int, site_root: Path, project_slug: str, base_url: str | None = None,
) -> tuple[Path, dict, list[Path]]:
    """Render a year's review (12 monthly galleries + landing) under the annual-review
    project's site dir: site/<project_slug>/<year>/.

    Returns (year_index_path, portal_summary, all_written_paths).
    """
    year_dir = site_root / project_slug / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    months: list[dict] = []
    for month in range(1, 13):
        _, summary, w = render_review_month(year, month, year_dir, base_url)
        months.append(summary)
        written += w

    total = sum(s["count"] for s in months)
    total_img = sum(s["with_images"] for s in months)
    # thumb path relative to the year landing (year_dir/index.html): img/<serial>.png
    year_thumb = next((f'img/{s["thumb"]}.png' for s in months if s["thumb"]), None)

    rows = "".join(
        f'<a class="review-month" href="{s["href"]}">'
        f'<span class="review-month-name">{_esc(s["name"].split()[0])}</span>'
        f'<span class="review-month-count">{s["count"]} marks · {s["with_images"]} imgs</span>'
        f'</a>'
        for s in months
    )
    body = (
        f'<div class="page-header"><h1>{year} Design-Mark Review</h1>'
        f'<div class="subtitle">USPTO design marks filed in {year} · '
        f'{total} marks · {total_img} with images</div></div>'
        f'<div class="page-body">'
        f'<p>Monthly galleries of design marks (drawing code 3·) filed during {year}.</p>'
        f'<div class="review-months">{rows}</div>'
        f'</div>'
    )
    out_path = year_dir / "index.html"
    out_path.write_text(
        _page(_page_title(f"{year} Design-Mark Review", "design-mark-review"),
              body, {}, depth=2, project=None),
        encoding="utf-8",
    )
    summary = {
        "year": year,
        "url": f"{project_slug}/{year}/index.html",
        "title": f"{year} Design-Mark Review",
        "count": total, "with_images": total_img,
        "thumb_src": f"{project_slug}/{year}/{year_thumb}" if year_thumb else None,
    }
    return out_path, summary, written
