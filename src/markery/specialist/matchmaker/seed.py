"""Local mark↔patent seed pairs (Phase 32 P2a).

Deterministic, model-free, offline. For each design mark of a filing year, find
the original applicant's patents (via the richness signal) and emit scored seed
pairs for the spawn pipeline. No EPO, no LLM — reuses ``score.date_score`` so
date scoring is consistent with the rest of the matchmaker.

Pair score = owner_conf × (0.5 + date_score), in [0, 1]:
  owner_conf  exact owner→assignee match = 1.0; fuzzy = the token-Jaccard score.
  date_score  [-0.4, 0.5], patent grant before mark filing is the expected order.
A good seed = patent grant within ``window`` years of the mark filing.
"""
from __future__ import annotations

from collections import defaultdict

import duckdb

from markery.common import config
from markery.specialist.matchmaker import richness as rich
from markery.specialist.matchmaker.score import date_score

DEFAULT_WINDOW = 12


def assignee_patents(conn: duckdb.DuckDBPyConnection) -> dict[str, list[dict]]:
    """normalised assignee → [{patent_no, app_dt, grant_dt, cpc[]}] (CPC subclasses)."""
    rows = conn.execute("""
        SELECT p.assignee_name, p.patent_no, p.app_dt, p.grant_dt,
               string_agg(DISTINCT pc.cpc_class, ',') AS subs
        FROM patents p
        LEFT JOIN patent_classes pc ON p.patent_no = pc.patent_no
        WHERE p.assignee_name IS NOT NULL AND p.assignee_name <> ''
        GROUP BY p.assignee_name, p.patent_no, p.app_dt, p.grant_dt
    """).fetchall()
    out: dict[str, list[dict]] = defaultdict(list)
    for aname, pno, app, grant, subs in rows:
        out[rich.norm(aname)].append({
            "patent_no": pno, "app_dt": app, "grant_dt": grant,
            "cpc": sorted(s for s in (subs or "").split(",") if s),
        })
    return out


def _delta_years(filing, grant) -> float | None:
    if not filing or not grant:
        return None
    return abs((filing - grant).days) / 365.25


def build_seed_pairs(marks: list[dict], patents: dict[str, list[dict]], *,
                     window: int = DEFAULT_WINDOW,
                     fuzzy_floor: float = rich.DEFAULT_FUZZY_FLOOR,
                     min_score: float = 0.0) -> list[dict]:
    """Pure core: score `design_mark_owners` rows against an assignee→patents map.

    Returns scored pairs sorted by descending score. No I/O.
    """
    counts = {k: len(v) for k, v in patents.items()}
    scored = {r["serial"]: r for r in rich.score_marks(marks, counts, fuzzy_floor=fuzzy_floor)}
    pairs: list[dict] = []
    for m in marks:
        r = scored[m["serial"]]
        if r["patents_exact"] > 0:
            key, conf, match = r["norm"], 1.0, "exact"
        elif r["fuzzy_score"] >= fuzzy_floor:
            key, conf, match = r["fuzzy_assignee"], r["fuzzy_score"], "fuzzy"
        else:
            continue
        filing = m.get("filing")
        for p in patents.get(key, []):
            delta = _delta_years(filing, p["grant_dt"])
            if delta is not None and delta > window:
                continue
            score = round(conf * (0.5 + date_score(p["grant_dt"], filing)), 3)
            if score < min_score:
                continue
            pairs.append({
                "serial": m["serial"], "mark": m["mark"], "applicant": m["owner"],
                "is_tech": r["is_tech"], "match": match,
                "owner_conf": round(conf, 2), "assignee": key,
                "patent_no": p["patent_no"],
                "app_dt": p["app_dt"].isoformat() if p["app_dt"] else None,
                "grant_dt": p["grant_dt"].isoformat() if p["grant_dt"] else None,
                "cpc": p["cpc"],
                "delta_years": round(delta, 1) if delta is not None else None,
                "score": score,
            })
    pairs.sort(key=lambda x: (-x["score"], x["serial"], x["patent_no"]))
    return pairs


def seed_pairs(year: int, *, window: int = DEFAULT_WINDOW,
               fuzzy_floor: float = rich.DEFAULT_FUZZY_FLOOR,
               min_score: float = 0.0,
               patents: dict[str, list[dict]] | None = None) -> list[dict]:
    """Scored seed pairs for a year's design marks (reads patents + trademarks).

    Pass `patents` to reuse a prebuilt assignee→patents map across years.
    """
    if patents is None:
        pc = duckdb.connect(str(config.DB["patents"]), read_only=True)
        patents = assignee_patents(pc)
        pc.close()
    tc = duckdb.connect(str(config.DB["trademarks"]), read_only=True)
    marks = rich.design_mark_owners(tc, year)
    tc.close()
    return build_seed_pairs(marks, patents, window=window,
                            fuzzy_floor=fuzzy_floor, min_score=min_score)


def summarise(pairs: list[dict]) -> dict:
    """Aggregate a year's seed pairs."""
    marks = {p["serial"] for p in pairs}
    tech = {p["serial"] for p in pairs if p["is_tech"]}
    cpc: dict[str, int] = defaultdict(int)
    for p in pairs:
        for sub in p["cpc"]:
            cpc[sub] += 1
    return {
        "pairs": len(pairs), "marks": len(marks), "tech_marks": len(tech),
        "exact": sum(1 for p in pairs if p["match"] == "exact"),
        "fuzzy": sum(1 for p in pairs if p["match"] == "fuzzy"),
        "cpc_subclasses": dict(sorted(cpc.items(), key=lambda x: -x[1])),
    }
