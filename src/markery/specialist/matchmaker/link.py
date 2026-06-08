"""Generate patent-trademark candidate pairs via the entity registry.

For each entity, finds its patents (via entity_name_variant → patents.assignee_name)
and trademarks (via entity_name_variant → owner.own_name → case_file), then scores
every patent-trademark pair and returns candidates above the min_score threshold.

Cross-specialist ATTACH is used to join entities, patents, and trademarks in a
single query — permitted per Q19 for joins that cannot be expressed through
individual specialist APIs without multiple round trips.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from markery.common.config import DB
from markery.common.project import Project
from markery.specialist.matchmaker.queries import read_confirmed, read_rejected
from markery.specialist.matchmaker.score import (
    is_company_name_mark, total_score,
    date_score, class_score, semantic_score, SEMANTIC_CAP,
)

UNCERTAINTY_BAND: tuple[float, float] = (0.40, 0.60)


def _connect() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(DB["entities"]), read_only=True)
    # Cross-specialist ATTACH — permitted per Q19 for queries that cannot be
    # expressed through individual specialist APIs without multiple round trips.
    conn.execute(f"ATTACH '{DB['patents']}'    AS pat (READ_ONLY)")
    conn.execute(f"ATTACH '{DB['trademarks']}' AS tm  (READ_ONLY)")
    return conn


def entity_ids_for_project(project_entities_file: Path) -> list[int]:
    """Read entity IDs from a project's entities.txt (one integer per line).

    Lines starting with # and inline # comments are ignored.
    """
    if not project_entities_file.exists():
        return []
    ids = []
    for line in project_entities_file.read_text().splitlines():
        line = line.split("#")[0].strip()
        if line:
            ids.append(int(line))
    return ids


def patents_for_entity(conn: duckdb.DuckDBPyConnection, entity_id: int) -> list[dict]:
    rows = conn.execute("""
        SELECT DISTINCT p.patent_no, p.title, p.grant_dt, p.app_dt,
               p.assignee_name
        FROM entity_name_variant v
        JOIN pat.patents p ON p.assignee_name = v.variant_name
        WHERE v.entity_id = ? AND v.source = 'patent_assignee'
        ORDER BY p.grant_dt
    """, [entity_id]).fetchall()
    return [
        {"patent_no": r[0], "title": r[1], "grant_dt": r[2],
         "app_dt": r[3], "assignee_name": r[4]}
        for r in rows
    ]


def cpc_for_patents(
    conn: duckdb.DuckDBPyConnection,
    patent_nos: list[str],
) -> dict[str, list[str]]:
    """Return {patent_no: [cpc_class, ...]} for a batch of patent numbers."""
    if not patent_nos:
        return {}
    placeholders = ",".join("?" * len(patent_nos))
    rows = conn.execute(f"""
        SELECT patent_no, cpc_class
        FROM pat.patent_classes
        WHERE patent_no IN ({placeholders}) AND cpc_class IS NOT NULL
    """, patent_nos).fetchall()
    result: dict[str, list[str]] = {}
    for pno, cls in rows:
        result.setdefault(pno, []).append(cls)
    return result


def trademarks_for_entity(
    conn: duckdb.DuckDBPyConnection,
    entity_id: int,
) -> list[dict]:
    rows = conn.execute("""
        SELECT DISTINCT cf.serial_no, cf.mark_id_char, cf.filing_dt,
               cf.registration_dt, cf.registration_no, o.own_name
        FROM entity_name_variant v
        JOIN tm.owner o    ON o.own_name = v.variant_name
        JOIN tm.case_file cf ON cf.serial_no = o.serial_no
        WHERE v.entity_id = ? AND v.source = 'trademark_owner'
        ORDER BY cf.filing_dt
    """, [entity_id]).fetchall()
    return [
        {"serial_no": r[0], "mark": r[1], "filing_dt": r[2],
         "registration_dt": r[3], "registration_no": r[4], "owner_name": r[5]}
        for r in rows
    ]


def generate_candidates(
    entity_ids: list[int] | None = None,
    min_score: float = 0.0,
    class_hints: set[str] | None = None,
    prior_brand_serials: set[str] | None = None,
) -> list[dict]:
    """Generate all patent-trademark candidate pairs for the given entity IDs.

    If entity_ids is None, runs for all entities. Returns candidates sorted by
    entity_id then descending score.
    """
    conn = _connect()

    if entity_ids is None:
        entity_ids = [
            r[0] for r in conn.execute(
                "SELECT entity_id FROM company_entity ORDER BY entity_id"
            ).fetchall()
        ]

    entity_names = {
        r[0]: r[1] for r in conn.execute(
            "SELECT entity_id, canonical_name FROM company_entity"
        ).fetchall()
    }

    candidates = []
    for eid in entity_ids:
        patents    = patents_for_entity(conn, eid)
        trademarks = trademarks_for_entity(conn, eid)
        if not patents or not trademarks:
            continue

        cpc_map = cpc_for_patents(conn, [p["patent_no"] for p in patents])

        for tm in trademarks:
            if is_company_name_mark(entity_names[eid], tm["mark"]):
                continue
            tm_filing = tm["filing_dt"]
            for pat in patents:
                cpc_classes = cpc_map.get(pat["patent_no"], [])
                is_prior = (prior_brand_serials is not None
                            and str(tm["serial_no"]) in prior_brand_serials)
                score = total_score(pat["grant_dt"], tm_filing, cpc_classes,
                                   class_hints=class_hints, prior_brand=is_prior)
                if score < min_score:
                    continue
                candidates.append({
                    "entity_id":       eid,
                    "entity":          entity_names[eid],
                    "patent_no":       pat["patent_no"],
                    "patent_title":    pat["title"],
                    "patent_grant_dt": str(pat["grant_dt"]) if pat["grant_dt"] else None,
                    "patent_assignee": pat["assignee_name"],
                    "cpc_classes":     sorted(set(cpc_classes)),
                    "trademark_serial": tm["serial_no"],
                    "trademark":       tm["mark"],
                    "tm_filing_dt":    str(tm_filing) if tm_filing else None,
                    "tm_reg_no":       tm["registration_no"],
                    "tm_owner":        tm["owner_name"],
                    "score":           score,
                })

    conn.close()
    candidates.sort(key=lambda c: (c["entity_id"], -c["score"]))
    return candidates


def write_candidates(candidates: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")
    print(f"  {len(candidates):,} candidates → {path}")


# ---------------------------------------------------------------------------
# Entity forward report (Phase 6D)
# ---------------------------------------------------------------------------

def entity_forward_report(entity_name: str, after_year: int = 1939) -> list[dict]:
    """Return extended marks for entity_name filed after after_year.

    Joins entity_name_variant (entities.duckdb) with extended_marks
    (trademarks.duckdb) via cross-specialist ATTACH — permitted per Q19 for
    queries that cannot be expressed without multiple round trips.
    Returns [] if no matches found or if extended_marks is empty.
    """
    conn = duckdb.connect(str(DB["entities"]), read_only=True)
    conn.execute(f"ATTACH '{DB['trademarks']}' AS tm (READ_ONLY)")
    try:
        rows = conn.execute("""
            SELECT DISTINCT em.serial_no, em.mark_text, em.filing_dt,
                            em.owner_name, em.status_cd, em.goods_desc
            FROM entity_name_variant v
            JOIN company_entity e ON e.entity_id = v.entity_id
            JOIN tm.extended_marks em ON LOWER(em.owner_name) = LOWER(v.variant_name)
            WHERE LOWER(e.canonical_name) = LOWER(?)
              AND (em.filing_dt IS NULL OR em.filing_dt > ?)
            ORDER BY em.filing_dt
        """, [entity_name, f"{after_year}-12-31"]).fetchall()
    except Exception:
        rows = []
    finally:
        conn.close()
    return [
        {
            "serial_no":  str(r[0]),
            "mark_text":  r[1],
            "filing_dt":  str(r[2]) if r[2] else None,
            "owner_name": r[3],
            "status_cd":  r[4],
            "goods_desc": r[5],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Pass 3: rescore
# ---------------------------------------------------------------------------

def _parse_date(s: str | None):
    """Parse an ISO date string; return None on failure."""
    if not s:
        return None
    try:
        from datetime import date
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def rescore_candidates(
    path: Path,
    class_hints: set[str] | None = None,
    prior_brand_serials: set[str] | None = None,
) -> int:
    """Pass 3: rewrite the score field for every candidate using signal fields.

    Reads candidates.jsonl, recomputes score = structural + min(SEMANTIC_CAP,
    semantic_bonus), writes the file in-place. Returns count rescored.
    Candidates without signal fields are rescored with a zero semantic bonus
    (identical to their original structural score).
    class_hints overrides PRODUCT_CLASSES for the class bonus when supplied.
    """
    if not path.exists():
        print(f"No candidates file at {path}")
        return 0

    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    candidates = [json.loads(ln) for ln in lines]

    for c in candidates:
        grant_dt  = _parse_date(c.get("patent_grant_dt"))
        filing_dt = _parse_date(c.get("tm_filing_dt"))
        is_prior = (prior_brand_serials is not None
                    and str(c.get("trademark_serial", "")) in prior_brand_serials)
        structural = date_score(grant_dt, filing_dt, prior_brand=is_prior) + class_score(
            c.get("cpc_classes", []), class_hints
        )
        sem = min(SEMANTIC_CAP, semantic_score(
            title_name_hit=bool(c.get("title_name_hit", False)),
            abstract_name_hit=bool(c.get("abstract_name_hit", False)),
            goods_title_overlap=float(c.get("goods_title_overlap", 0.0)),
            goods_abstract_overlap=float(c.get("goods_abstract_overlap", 0.0)),
        ))
        c["score"] = round(structural + sem, 4)

    with open(path, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")

    print(f"  {len(candidates):,} candidates rescored → {path}")
    return len(candidates)


# ---------------------------------------------------------------------------
# Resolution report (used by --resolve flag)
# ---------------------------------------------------------------------------

def resolve_report(project: str) -> dict:
    """Analyse the structural uncertainty band for a project's current candidates.

    Returns a dict:
        band_count        int          pairs whose structural score ∈ UNCERTAINTY_BAND
        missing_abstracts list[str]    patent_nos without abstract text in patents.duckdb
        missing_goods     list[str]    serial_nos without G&S text in trademarks.duckdb
        resolvable        int          band pairs where BOTH abstract AND goods are present
    """
    from markery.specialist.patent.queries   import connect as pat_connect, has_abstract
    from markery.specialist.trademark.queries import connect as tm_connect, get_goods_desc

    proj = Project(project)
    low, high = UNCERTAINTY_BAND

    candidates_all: list[dict] = []
    if proj.candidates.exists():
        candidates_all = [
            json.loads(ln)
            for ln in proj.candidates.read_text().splitlines()
            if ln.strip()
        ]

    band = [
        c for c in candidates_all
        if low <= (
            date_score(_parse_date(c.get("patent_grant_dt")),
                       _parse_date(c.get("tm_filing_dt")))
            + class_score(c.get("cpc_classes", []))
        ) <= high
    ]

    if not band:
        return {"band_count": 0, "missing_abstracts": [], "missing_goods": [], "resolvable": 0}

    pat_nos    = list(dict.fromkeys(c["patent_no"]              for c in band))
    serial_nos = list(dict.fromkeys(str(c["trademark_serial"])  for c in band))

    pat_conn = pat_connect()
    tm_conn  = tm_connect()
    try:
        missing_abstracts = [p for p in pat_nos    if not has_abstract(pat_conn, p)]
        missing_goods     = [s for s in serial_nos if get_goods_desc(tm_conn, s) is None]
    finally:
        pat_conn.close()
        tm_conn.close()

    missing_pat = set(missing_abstracts)
    missing_sno = set(missing_goods)
    resolvable  = sum(
        1 for c in band
        if c["patent_no"] not in missing_pat
        and str(c["trademark_serial"]) not in missing_sno
    )

    return {
        "band_count":        len(band),
        "missing_abstracts": missing_abstracts,
        "missing_goods":     missing_goods,
        "resolvable":        resolvable,
    }
