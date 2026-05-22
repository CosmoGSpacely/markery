"""Database queries for site builder."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from markery.common.config import DB
from markery.common.project import Project


def _connect() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(DB["entities"]), read_only=True)
    conn.execute(f"ATTACH '{DB['patents']}'    AS pat (READ_ONLY)")
    conn.execute(f"ATTACH '{DB['trademarks']}' AS tm  (READ_ONLY)")
    return conn


def get_project_entity_ids(project: str) -> list[int]:
    path = Project(project).entities_file
    if not path.exists():
        return []
    ids = []
    for line in path.read_text().splitlines():
        token = line.split("#")[0].strip()
        if token.isdigit():
            ids.append(int(token))
    return ids


def get_entities(entity_ids: list[int]) -> list[dict]:
    if not entity_ids:
        return []
    conn = _connect()
    placeholders = ",".join("?" * len(entity_ids))
    rows = conn.execute(f"""
        SELECT entity_id, canonical_name, entity_type, industry, notes
        FROM company_entity
        WHERE entity_id IN ({placeholders})
        ORDER BY entity_id
    """, entity_ids).fetchall()

    entities = []
    for eid, name, etype, industry, notes in rows:
        variants = conn.execute("""
            SELECT variant_name, source FROM entity_name_variant
            WHERE entity_id = ?
            ORDER BY source, variant_name
        """, [eid]).fetchall()
        entities.append({
            "entity_id": eid,
            "canonical_name": name,
            "entity_type": etype,
            "industry": industry,
            "notes": notes,
            "slug": name.lower().replace(" & ", "-and-").replace(" ", "-").replace(",", "").replace(".", ""),
            "name_variants": [{"name": v[0], "source": v[1]} for v in variants],
        })
    conn.close()
    return entities


def get_trademarks_for_project(entity_ids: list[int]) -> list[dict]:
    if not entity_ids:
        return []
    conn = _connect()
    placeholders = ",".join("?" * len(entity_ids))
    rows = conn.execute(f"""
        SELECT cf.serial_no::VARCHAR,
               cf.mark_id_char,
               cf.filing_dt,
               cf.mark_draw_cd,
               cf.registration_no,
               cf.cfh_status_cd,
               MIN(o.own_name)   AS owner_name,
               s.statement_text,
               c.first_use_com_dt,
               e.entity_id,
               e.canonical_name  AS entity_name,
               mi.serial_no IS NOT NULL AS image_available
        FROM tm.case_file cf
        JOIN tm.owner o ON cf.serial_no = o.serial_no
        JOIN entity_name_variant v ON UPPER(o.own_name) = UPPER(v.variant_name)
            AND v.source = 'trademark_owner'
        JOIN company_entity e ON v.entity_id = e.entity_id
        LEFT JOIN tm.statement s ON cf.serial_no = s.serial_no
            AND s.statement_type_cd LIKE 'GS%'
        LEFT JOIN tm.classification c ON cf.serial_no = c.serial_no
        LEFT JOIN tm.mark_images mi ON cf.serial_no = mi.serial_no
        WHERE e.entity_id IN ({placeholders})
        GROUP BY cf.serial_no, cf.mark_id_char, cf.filing_dt, cf.mark_draw_cd,
                 cf.registration_no, cf.cfh_status_cd, s.statement_text,
                 c.first_use_com_dt, e.entity_id, e.canonical_name, mi.serial_no
        ORDER BY cf.filing_dt, cf.serial_no
    """, entity_ids).fetchall()
    conn.close()

    return [
        {
            "serial_no": r[0],
            "mark_name": r[1],
            "filing_dt": r[2],
            "draw_cd": r[3],
            "registration_no": r[4],
            "status_cd": r[5],
            "owner_name": r[6],
            "goods": r[7],
            "first_use_dt": r[8],
            "entity_id": r[9],
            "entity_name": r[10],
            "image_available": bool(r[11]),
        }
        for r in rows
    ]


def get_patents_for_project(entity_ids: list[int]) -> list[dict]:
    if not entity_ids:
        return []
    conn = _connect()
    placeholders = ",".join("?" * len(entity_ids))
    rows = conn.execute(f"""
        SELECT p.patent_no,
               p.title,
               p.grant_dt,
               p.app_dt,
               p.assignee_name,
               LIST(DISTINCT pc.cpc_class) AS cpc_classes,
               LIST(DISTINCT pi.inventor_name) AS inventors,
               MAX(CASE WHEN pf.patent_no IS NOT NULL THEN 1 ELSE 0 END) AS figure_available,
               e.entity_id,
               e.canonical_name AS entity_name
        FROM pat.patents p
        LEFT JOIN pat.patent_classes pc ON p.patent_no = pc.patent_no
        LEFT JOIN pat.patent_inventors pi ON p.patent_no = pi.patent_no
        LEFT JOIN pat.patent_figures pf ON p.patent_no = pf.patent_no
        JOIN entity_name_variant v ON UPPER(p.assignee_name) = UPPER(v.variant_name)
            AND v.source = 'patent_assignee'
        JOIN company_entity e ON v.entity_id = e.entity_id
        WHERE e.entity_id IN ({placeholders})
        GROUP BY p.patent_no, p.title, p.grant_dt, p.app_dt, p.assignee_name,
                 e.entity_id, e.canonical_name
        ORDER BY p.grant_dt, p.patent_no
    """, entity_ids).fetchall()
    conn.close()

    return [
        {
            "patent_no": r[0],
            "title": r[1],
            "grant_dt": r[2],
            "application_dt": r[3],
            "assignee_name": r[4],
            "cpc_classes": r[5] or [],
            "inventors": r[6] or [],
            "figure_available": bool(r[7]),
            "entity_id": r[8],
            "entity_name": r[9],
        }
        for r in rows
    ]


def get_confirmed_matches(project: str) -> list[dict]:
    path = Project(project).confirmed
    if not path.exists():
        return []
    matches = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    conn = _connect()
    content_dir = Project(project).content
    for m in matches:
        sn = m["trademark_serial"]
        row = conn.execute("""
            SELECT cf.filing_dt, cf.mark_id_char, cf.mark_draw_cd,
                   MIN(o.own_name), s.statement_text,
                   mi.image_data IS NOT NULL AS has_image
            FROM tm.case_file cf
            LEFT JOIN tm.owner o ON cf.serial_no = o.serial_no
            LEFT JOIN tm.statement s ON cf.serial_no = s.serial_no
                AND s.statement_type_cd LIKE 'GS%'
            LEFT JOIN tm.mark_images mi ON cf.serial_no = mi.serial_no
            WHERE cf.serial_no = ?
            GROUP BY cf.filing_dt, cf.mark_id_char, cf.mark_draw_cd,
                     s.statement_text, mi.image_data
        """, [sn]).fetchone()
        if row:
            m["filing_dt"], m["mark_name"], m["draw_cd"] = row[0], row[1], row[2]
            m["owner_name"], m["goods"], m["has_image"] = row[3], row[4], bool(row[5])

        pat = conn.execute("""
            SELECT title, grant_dt, app_dt, assignee_name
            FROM pat.patents WHERE patent_no = ?
        """, [m["patent_no"]]).fetchone()
        if pat:
            m["patent_title"], m["grant_dt"], m["application_dt"], m["assignee"] = pat

        slug = m["trademark"].lower().replace(" ", "-")
        essay = content_dir / f"{slug}.md"
        m["essay_path"] = str(essay) if essay.exists() else None
        m["slug"] = slug

    conn.close()
    return matches


def get_mark_image_bytes(serial_no: str) -> bytes | None:
    conn = duckdb.connect(str(DB["trademarks"]), read_only=True)
    row = conn.execute(
        "SELECT image_data FROM mark_images WHERE serial_no = ?", [serial_no]
    ).fetchone()
    conn.close()
    return bytes(row[0]) if row else None


def get_patent_figure_bytes(patent_no: str) -> bytes | None:
    conn = duckdb.connect(str(DB["patents"]), read_only=True)
    try:
        row = conn.execute(
            "SELECT figure_data FROM patent_figures WHERE patent_no = ? LIMIT 1", [patent_no]
        ).fetchone()
    except Exception:
        row = None
    conn.close()
    return bytes(row[0]) if row else None


def get_mark_image_b64(serial_no: str) -> str | None:
    import base64
    conn = duckdb.connect(str(DB["trademarks"]), read_only=True)
    row = conn.execute(
        "SELECT image_data FROM mark_images WHERE serial_no = ?", [serial_no]
    ).fetchone()
    conn.close()
    if not row:
        return None
    return base64.b64encode(bytes(row[0])).decode()


def get_patent_figure_b64(patent_no: str) -> str | None:
    import base64
    conn = duckdb.connect(str(DB["patents"]), read_only=True)
    try:
        row = conn.execute(
            "SELECT figure_data FROM patent_figures WHERE patent_no = ? LIMIT 1", [patent_no]
        ).fetchone()
    except Exception:
        row = None
    conn.close()
    if not row:
        return None
    return base64.b64encode(bytes(row[0])).decode()


def get_content_gaps(project: str) -> list[dict]:
    """Return a prioritised list of missing content items for a project.

    Priority tiers:
      1 — match essays (one per confirmed pair)
      2 — entity summaries (one per project entity)
      3 — optional enrichment pages (sources, timeline)

    Each gap dict has: type, slug, priority, label, path.
    The list is sorted by (priority, slug) so the most critical gaps appear first.
    """
    proj        = Project(project)
    content_dir = proj.content
    matches     = get_confirmed_matches(project)
    entity_ids  = get_project_entity_ids(project)
    entities    = get_entities(entity_ids)

    gaps: list[dict] = []

    # Priority 1 — missing match essays
    seen_slugs: set[str] = set()
    for m in matches:
        slug = m.get("slug") or m["trademark"].lower().replace(" ", "-")
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        essay = content_dir / f"{slug}.md"
        if not essay.exists():
            gaps.append({
                "type":     "match_essay",
                "slug":     slug,
                "priority": 1,
                "label":    f"{m['trademark']} ↔ {m['patent_no']}",
                "path":     str(essay),
            })

    # Priority 2 — missing entity summaries
    for e in entities:
        slug    = e["slug"]
        summary = content_dir / f"entity-{slug}.md"
        if not summary.exists():
            gaps.append({
                "type":     "entity_summary",
                "slug":     slug,
                "priority": 2,
                "label":    e["canonical_name"],
                "path":     str(summary),
            })

    # Priority 3 — optional enrichment pages
    for fname, gtype, label in [
        ("sources.md",  "sources_page",  "Source bibliography"),
        ("timeline.md", "timeline_page", "Annotated timeline"),
    ]:
        if not (content_dir / fname).exists():
            gaps.append({
                "type":     gtype,
                "slug":     fname.replace(".md", ""),
                "priority": 3,
                "label":    label,
                "path":     str(content_dir / fname),
            })

    gaps.sort(key=lambda g: (g["priority"], g["slug"]))
    return gaps


def get_rendered_pages(project: str) -> list[str]:
    """Return relative paths of all rendered HTML pages in the project site."""
    site_dir = Project(project).site
    if not site_dir.exists():
        return []
    return sorted(
        str(p.relative_to(site_dir)) for p in site_dir.rglob("*.html")
    )


def get_entity_stats(entity_ids: list[int],
                     trademarks: list[dict],
                     patents: list[dict],
                     matches: list[dict]) -> dict[int, dict]:
    stats = {}
    for eid in entity_ids:
        tm  = [t for t in trademarks if t["entity_id"] == eid]
        pat = [p for p in patents    if p["entity_id"] == eid]
        mat = [m for m in matches    if m["entity_id"] == eid]
        tm_years  = [t["filing_dt"].year for t in tm  if t["filing_dt"]]
        pat_years = [p["grant_dt"].year  for p in pat if p["grant_dt"]]
        all_years = tm_years + pat_years
        stats[eid] = {
            "trademark_count": len(tm),
            "patent_count":    len(pat),
            "match_count":     len(mat),
            "active_from":     min(all_years) if all_years else None,
            "active_to":       max(all_years) if all_years else None,
        }
    return stats
