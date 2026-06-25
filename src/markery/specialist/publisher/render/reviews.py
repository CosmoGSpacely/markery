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

# Technology design marks by the old US class schedule (PUBLISHER_REVIEW §5):
# apparatus auto-pass classes + the borderline hardware/filter/belting classes.
# Pre-Nice marks carry US classes (zero-padded 3-digit). This is the deterministic
# class gate; Phase 32's free-model goods judgment refines it for patent matching.
_TECH_US_CLASSES = {"013", "019", "021", "023", "026", "031", "034", "035", "044"}


def design_marks(year: int, month: int) -> list[dict]:
    """Design marks (mark_draw_cd LIKE '3%') filed in the given year/month."""
    last = calendar.monthrange(year, month)[1]
    conn = duckdb.connect(str(config.DB["trademarks"]), read_only=True)
    rows = conn.execute(f"""
        SELECT cf.serial_no, cf.mark_id_char, cf.filing_dt,
               o.own_name, o.own_addr_state_cd,
               gs.goods,
               CASE WHEN mi.file IS NOT NULL THEN 1 ELSE 0 END AS has_img,
               uc.us_classes
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
        LEFT JOIN (
            SELECT serial_no, string_agg(DISTINCT us_class_cd, ',') AS us_classes
            FROM us_class GROUP BY serial_no
        ) uc ON cf.serial_no = uc.serial_no
        WHERE cf.mark_draw_cd LIKE '3%'
          AND cf.filing_dt BETWEEN DATE '{year}-{month:02d}-01'
                               AND DATE '{year}-{month:02d}-{last:02d}'
        ORDER BY cf.filing_dt, cf.serial_no
    """).fetchall()
    conn.close()
    out = []
    for r in rows:
        classes = set((r[7] or "").split(",")) if r[7] else set()
        out.append({
            "serial": str(r[0]), "mark": r[1] or "", "filing": r[2],
            "owner": r[3] or "", "state": r[4] or "", "goods": r[5] or "",
            "has_img": bool(r[6]),
            "is_tech": bool(classes & _TECH_US_CLASSES),
        })
    return out


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
    tech = m.get("is_tech")
    badge = '<span class="tech-badge" title="Technology mark (US apparatus class)">⚙ Technology</span>' if tech else ""
    card_cls = "card tech-mark" if tech else "card"
    return (
        f'<div class="{card_cls}" id="sn-{m["serial"]}">{inner}'
        f'<div class="card-body">'
        f'<div class="card-name">{_esc(m["mark"] or "(design mark)")}{badge}</div>'
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
    tech_thumb: str | None = None
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
                if m.get("is_tech") and tech_thumb is None:
                    tech_thumb = m["serial"]   # prefer a technology mark as the sample
        cards.append(_card(m, img_rel))

    tech_count = sum(1 for m in marks if m.get("is_tech"))
    name = f"{_MONTHS[month]} {year}"
    tech_sub = f' · {tech_count} technology' if tech_count else ""
    grid = (f'<div class="card-grid">{"".join(cards)}</div>'
            if cards else '<p class="empty-state">No design marks filed this month.</p>')
    # Month-to-month navigation (prev · year · next).
    prev_link = (f'<a href="{month-1:02d}.html">← {_MONTHS[month-1]}</a>'
                 if month > 1 else '<span class="nav-disabled">←</span>')
    next_link = (f'<a href="{month+1:02d}.html">{_MONTHS[month+1]} →</a>'
                 if month < 12 else '<span class="nav-disabled">→</span>')
    month_nav = (
        f'<nav class="review-monthnav">{prev_link}'
        f'<a href="index.html">{year} review</a>{next_link}</nav>'
    )
    body = (
        f'<div class="page-header"><h1>{name}</h1>'
        f'<div class="subtitle">Design marks · {len(marks)} filed{tech_sub}</div></div>'
        f'<div class="page-body">{month_nav}{grid}{month_nav}</div>'
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
        "tech_count": tech_count,
        "href": f"{month:02d}.html", "thumb": thumb,
        "tech_thumb": tech_thumb or thumb,
    }
    return out_path, summary, written


def render_review_year(
    year: int, site_root: Path, project_slug: str, base_url: str | None = None,
    sibling_years: list[int] | None = None,
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
    total_tech = sum(s.get("tech_count", 0) for s in months)
    # thumb path relative to the year landing (year_dir/index.html): img/<serial>.png.
    # Prefer a technology-mark sample for the year thumbnail.
    year_thumb = (next((f'img/{s["tech_thumb"]}.png' for s in months if s.get("tech_thumb")), None)
                  or next((f'img/{s["thumb"]}.png' for s in months if s["thumb"]), None))

    rows = "".join(
        f'<a class="review-month" href="{s["href"]}">'
        f'<span class="review-month-name">{_esc(s["name"].split()[0])}</span>'
        f'<span class="review-month-count">{s["count"]} marks'
        + (f' · <span class="tech-count">{s["tech_count"]} tech</span>' if s.get("tech_count") else "")
        + '</span>'
        f'</a>'
        for s in months
    )
    # Cross-year switcher (sibling review years).
    year_switch = ""
    siblings = sorted(sibling_years or [year])
    if len(siblings) > 1:
        links = "".join(
            (f'<span class="review-year-current">{y}</span>' if y == year
             else f'<a href="../{y}/index.html">{y}</a>')
            for y in siblings
        )
        year_switch = f'<nav class="review-yearnav">Years: {links}</nav>'
    body = (
        f'<div class="page-header"><h1>{year} Design-Mark Review</h1>'
        f'<div class="subtitle">USPTO design marks filed in {year} · '
        f'{total} marks · {total_img} with images'
        + (f' · {total_tech} technology' if total_tech else "")
        + '</div></div>'
        f'<div class="page-body">{year_switch}'
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
        "count": total, "with_images": total_img, "tech_count": total_tech,
        "thumb_src": f"{project_slug}/{year}/{year_thumb}" if year_thumb else None,
    }
    return out_path, summary, written
