"""Database queries for site builder — implements the historian's tool interface."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb


def _connect(db_paths: dict[str, str]) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(db_paths["entities"], read_only=True)
    conn.execute(f"ATTACH '{db_paths['patents']}'    AS pat (READ_ONLY)")
    conn.execute(f"ATTACH '{db_paths['trademarks']}' AS tm  (READ_ONLY)")
    return conn


def get_project_entity_ids(project: str) -> list[int]:
    path = Path(f"projects/{project}/entities.txt")
    if not path.exists():
        return []
    return [int(line.strip()) for line in path.read_text().splitlines() if line.strip().isdigit()]


def get_entities(db_paths: dict[str, str], entity_ids: list[int]) -> list[dict]:
    if not entity_ids:
        return []
    conn = _connect(db_paths)
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
            "slug": name.lower().replace(" ", "-").replace(",", "").replace(".", ""),
            "name_variants": [{"name": v[0], "source": v[1]} for v in variants],
        })
    conn.close()
    return entities


def get_trademarks_for_project(db_paths: dict[str, str], entity_ids: list[int]) -> list[dict]:
    if not entity_ids:
        return []
    conn = _connect(db_paths)
    placeholders = ",".join("?" * len(entity_ids))
    rows = conn.execute(f"""
        SELECT cf.serial_no::VARCHAR,
               cf.mark_id_char,
               cf.filing_dt,
               cf.mark_draw_cd,
               cf.registration_no,
               cf.cfh_status_cd,
               o.own_name,
               s.statement_text,
               c.first_use_com_dt,
               e.entity_id,
               e.canonical_name  AS entity_name,
               mi.serial_no IS NOT NULL AS image_available
        FROM tm.case_file cf
        LEFT JOIN tm.owner o ON cf.serial_no = o.serial_no AND o.own_id = 1
        LEFT JOIN tm.statement s ON cf.serial_no = s.serial_no
            AND s.statement_type_cd LIKE 'GS%'
        LEFT JOIN tm.classification c ON cf.serial_no = c.serial_no
        LEFT JOIN tm.mark_images mi ON cf.serial_no = mi.serial_no
        JOIN entity_name_variant v ON UPPER(o.own_name) = UPPER(v.variant_name)
            AND v.source = 'trademark_owner'
        JOIN company_entity e ON v.entity_id = e.entity_id
        WHERE e.entity_id IN ({placeholders})
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


def get_patents_for_project(db_paths: dict[str, str], entity_ids: list[int]) -> list[dict]:
    if not entity_ids:
        return []
    conn = _connect(db_paths)
    placeholders = ",".join("?" * len(entity_ids))
    rows = conn.execute(f"""
        SELECT p.patent_no,
               p.title,
               p.grant_dt,
               p.application_dt,
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
        GROUP BY p.patent_no, p.title, p.grant_dt, p.application_dt, p.assignee_name,
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


def get_confirmed_matches(project: str, db_paths: dict[str, str]) -> list[dict]:
    path = Path(f"projects/{project}/matches/confirmed.jsonl")
    if not path.exists():
        return []
    matches = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    conn = _connect(db_paths)
    for m in matches:
        sn = m["trademark_serial"]
        row = conn.execute("""
            SELECT cf.filing_dt, cf.mark_id_char, cf.mark_draw_cd,
                   o.own_name, s.statement_text,
                   mi.image_data IS NOT NULL AS has_image
            FROM tm.case_file cf
            LEFT JOIN tm.owner o ON cf.serial_no = o.serial_no AND o.own_id = 1
            LEFT JOIN tm.statement s ON cf.serial_no = s.serial_no
                AND s.statement_type_cd LIKE 'GS%'
            LEFT JOIN tm.mark_images mi ON cf.serial_no = mi.serial_no
            WHERE cf.serial_no = ?
        """, [sn]).fetchone()
        if row:
            m["filing_dt"], m["mark_name"], m["draw_cd"] = row[0], row[1], row[2]
            m["owner_name"], m["goods"], m["has_image"] = row[3], row[4], bool(row[5])

        pat = conn.execute("""
            SELECT title, grant_dt, application_dt, assignee_name
            FROM pat.patents WHERE patent_no = ?
        """, [m["patent_no"]]).fetchone()
        if pat:
            m["patent_title"], m["grant_dt"], m["application_dt"], m["assignee"] = pat

        slug = m["trademark"].lower().replace(" ", "-")
        essay = Path(f"projects/{project}/content/{slug}.md")
        m["essay_path"] = str(essay) if essay.exists() else None
        m["slug"] = slug

    conn.close()
    return matches


def get_mark_image_b64(db_paths: dict[str, str], serial_no: str) -> str | None:
    import base64
    conn = duckdb.connect(db_paths["trademarks"], read_only=True)
    row = conn.execute(
        "SELECT image_data FROM mark_images WHERE serial_no = ?", [serial_no]
    ).fetchone()
    conn.close()
    if not row:
        return None
    return base64.b64encode(bytes(row[0])).decode()


def get_patent_figure_b64(db_paths: dict[str, str], patent_no: str) -> str | None:
    import base64
    conn = duckdb.connect(db_paths["patents"], read_only=True)
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


def get_entity_stats(db_paths: dict[str, str], entity_ids: list[int],
                     trademarks: list[dict], patents: list[dict],
                     matches: list[dict]) -> dict[int, dict]:
    stats = {}
    for eid in entity_ids:
        tm = [t for t in trademarks if t["entity_id"] == eid]
        pat = [p for p in patents if p["entity_id"] == eid]
        mat = [m for m in matches if m["entity_id"] == eid]
        tm_years = [t["filing_dt"].year for t in tm if t["filing_dt"]]
        pat_years = [p["grant_dt"].year for p in pat if p["grant_dt"]]
        all_years = tm_years + pat_years
        stats[eid] = {
            "trademark_count": len(tm),
            "patent_count": len(pat),
            "match_count": len(mat),
            "active_from": min(all_years) if all_years else None,
            "active_to": max(all_years) if all_years else None,
        }
    return stats
