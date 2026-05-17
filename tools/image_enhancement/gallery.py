"""Generate self-contained HTML galleries from a set of serial numbers."""

from __future__ import annotations

import base64
from pathlib import Path

import duckdb

_STATUS_LABELS = {
    800: "Registered (live)",
    900: "Expired / cancelled",
    713: "Abandoned",
    710: "Abandoned",
}

_CSS = """
body {
  font-family: Georgia, serif;
  background: #f4f0e8;
  color: #2a2a2a;
  margin: 0;
  padding: 20px;
}
h1 { text-align: center; font-size: 1.6em; margin-bottom: 4px; }
.subtitle { text-align: center; color: #666; margin-bottom: 24px; font-size: 0.95em; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.card {
  background: white;
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
  display: flex;
  flex-direction: column;
}
.card img {
  width: 100%;
  height: 160px;
  object-fit: contain;
  border-bottom: 1px solid #eee;
  margin-bottom: 8px;
}
.info { display: flex; flex-direction: column; gap: 3px; }
.name { font-weight: bold; font-size: .85em; line-height: 1.3; }
.meta { font-size: .75em; color: #555; }
.owner { font-size: .75em; color: #444; font-style: italic; }
.gs {
  font-size: .73em;
  color: #333;
  margin-top: 5px;
  line-height: 1.4;
  border-top: 1px solid #eee;
  padding-top: 5px;
}
.codes { font-size: .7em; color: #888; font-family: monospace; margin-top: 4px; }
.status { font-size: .72em; color: #999; }
.svg-badge { font-size: .68em; color: #5a8a3a; font-family: monospace; margin-left: 6px; }
"""


def build_gallery(
    serial_nos: list[str],
    img_dir: Path,
    out_path: Path,
    *,
    title: str = "Trademark Marks",
    subtitle: str = "",
    db_path: str = "trademarks.duckdb",
    embed_images: bool = True,
) -> Path:
    """
    Write an HTML gallery to out_path.

    Reads PNG (and notes SVG presence) from img_dir/<serial_no>.{png,svg}.
    Pulls filing metadata and goods/services text from db_path.
    When embed_images=True the PNG bytes are base64-encoded inline so the
    file is fully self-contained; set False to reference files by path instead.
    """
    img_dir = Path(img_dir)
    out_path = Path(out_path)
    conn = duckdb.connect(db_path, read_only=True)

    sn_sql = ",".join(f"'{s}'" for s in serial_nos)

    marks: dict[str, tuple] = {
        str(row[0]): row
        for row in conn.execute(f"""
            SELECT cf.serial_no, cf.filing_dt, cf.mark_id_char, cf.mark_draw_cd,
                   cf.registration_no, cf.cfh_status_cd,
                   o.own_name, o.own_addr_city, o.own_addr_state_cd
            FROM case_file cf
            LEFT JOIN owner o ON cf.serial_no = o.serial_no AND o.own_entity_cd = 10
            WHERE cf.serial_no IN ({sn_sql})
        """).fetchall()
    }

    ds_map: dict[str, list[str]] = {}
    for sn, cd in conn.execute(f"""
        SELECT serial_no, design_search_cd FROM design_search
        WHERE serial_no IN ({sn_sql})
        ORDER BY serial_no, design_search_cd
    """).fetchall():
        ds_map.setdefault(str(sn), []).append(cd)

    gs_map: dict[str, list[str]] = {}
    for sn, text in conn.execute(f"""
        SELECT serial_no, statement_text FROM statement
        WHERE serial_no IN ({sn_sql}) AND statement_type_cd LIKE 'GS%'
        ORDER BY serial_no, statement_type_cd
    """).fetchall():
        gs_map.setdefault(str(sn), []).append(text)

    conn.close()

    cards: list[str] = []
    for sn in serial_nos:
        png = img_dir / f"{sn}.png"
        if not png.exists():
            continue

        row = marks.get(sn)
        if not row:
            continue

        _, filing_dt, mark_name, draw_cd, reg_no, status_cd, own_name, own_city, own_state = row

        if embed_images:
            img_src = f"data:image/png;base64,{base64.b64encode(png.read_bytes()).decode()}"
        else:
            img_src = f"{sn}.png"

        has_svg = (img_dir / f"{sn}.svg").exists()
        svg_badge = '<span class="svg-badge">[SVG]</span>' if has_svg else ""

        meta_parts = [f"Filed {filing_dt.strftime('%B %d, %Y')}"]
        if reg_no:
            meta_parts.append(f"Reg.&nbsp;{reg_no}")
        meta = " &bull; ".join(meta_parts)

        owner_parts = [p for p in [own_name, own_city, own_state] if p]
        owner_html = (
            f'<div class="owner">{", ".join(owner_parts)}</div>' if owner_parts else ""
        )

        gs_texts = gs_map.get(sn, [])
        gs_html = (
            f'<div class="gs">{" / ".join(gs_texts)}</div>' if gs_texts else ""
        )

        ds_codes = ", ".join(ds_map.get(sn, []))
        status_label = _STATUS_LABELS.get(status_cd, str(status_cd) if status_cd else "")

        cards.append(
            f'  <div class="card">\n'
            f'    <img src="{img_src}" alt="{mark_name}" loading="lazy" />\n'
            f'    <div class="info">\n'
            f'      <div class="name">{mark_name}{svg_badge}</div>\n'
            f'      <div class="meta">{meta}</div>\n'
            f'      {owner_html}\n'
            f'      {gs_html}\n'
            f'      <div class="codes">Draw: {draw_cd} &bull; Design: {ds_codes or "—"}</div>\n'
            f'      <div class="status">{status_label}</div>\n'
            f'    </div>\n'
            f'  </div>'
        )

    subtitle_line = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    html = (
        '<!DOCTYPE html>\n<html>\n<head>\n'
        '<meta charset="utf-8">\n'
        f'<title>{title}</title>\n'
        f'<style>{_CSS}</style>\n'
        '</head>\n<body>\n'
        f'<h1>{title}</h1>\n'
        f'{subtitle_line}\n'
        '<div class="grid">\n'
        + "\n".join(cards)
        + "\n</div>\n</body>\n</html>\n"
    )

    out_path.write_text(html, encoding="utf-8")
    return out_path
