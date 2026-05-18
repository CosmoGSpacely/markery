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
from markery.specialist.matchmaker.score import total_score


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
            tm_filing = tm["filing_dt"]
            for pat in patents:
                cpc_classes = cpc_map.get(pat["patent_no"], [])
                score = total_score(pat["grant_dt"], tm_filing, cpc_classes)
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


def read_confirmed(path: Path) -> list[dict]:
    """Load a confirmed.jsonl file. Returns [] if the file does not exist."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
