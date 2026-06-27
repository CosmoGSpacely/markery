"""Assignee-overlap richness signal (Phase 32 P1).

For each design mark of a given filing year, count how many patents share the
mark owner's name as their assignee. This is an *independent* richness/relevance
signal: it asks "does this brand's owner also hold patents?", which the US-class
tech gate (PUBLISHER_REVIEW §5) cannot answer. The two signals are complementary
— assignee overlap recovers class-gate false negatives (e.g. pencils, aluminium,
hosiery owners who patented) and demotes class-tech logos whose owner never did.

Read-only across patents.duckdb + trademarks.duckdb (MATCHMAKER cross-DB scope).
Names are reduced with ``normalise_name`` *after* stripping ``[CC]`` country tags
that EPO assignees carry (``EASTMAN KODAK CO [US]`` → matches ``EASTMAN KODAK CO``).
Exact normalised equality is the primary signal; a guarded token-Jaccard fuzzy
tier (floor 0.8, tokens of length ≥3 only) is reported separately, since short
two-token names produce spurious overlaps (``E.C. HALL CO ~ C E``).
"""
from __future__ import annotations

import calendar
import re
from collections import defaultdict

import duckdb

from markery.common import config
from markery.specialist.matchmaker.autoregister import normalise_name

# Technology design marks by the old US class schedule — kept in sync with
# publisher/render/reviews.py::_TECH_US_CLASSES.
TECH_US_CLASSES = {"013", "019", "021", "023", "026", "031", "034", "035", "044"}

_BRACKET = re.compile(r"\[[^\]]*\]")           # [US] / [GB] country tags
DEFAULT_FUZZY_FLOOR = 0.8
_MIN_TOKEN_LEN = 3                              # ignore initials when fuzzy-matching


def norm(s: str) -> str:
    """Normalise an owner/assignee string for cross-DB comparison."""
    return normalise_name(_BRACKET.sub(" ", s or ""))


def _long_tokens(k: str) -> set[str]:
    return {t for t in k.split() if len(t) >= _MIN_TOKEN_LEN}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def assignee_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Map normalised assignee_name → total patent count (summing country-tag variants)."""
    rows = conn.execute(
        "SELECT assignee_name, COUNT(*) FROM patents "
        "WHERE assignee_name IS NOT NULL AND assignee_name <> '' "
        "GROUP BY assignee_name"
    ).fetchall()
    out: dict[str, int] = {}
    for name, n in rows:
        k = norm(name)
        if k:
            out[k] = out.get(k, 0) + n
    return out


def design_mark_owners(conn: duckdb.DuckDBPyConnection, year: int) -> list[dict]:
    """Design marks (mark_draw_cd LIKE '3%') filed in `year`, with original applicant + US classes.

    Uses the *original applicant* (lowest ``own_type_cd`` — code 30 is the original
    registrant; 40+ are assignment-chain successors), not the current owner. The
    ``owner`` rows are ordered newest-first, so ``MIN(own_id)`` would pick a modern
    successor name (e.g. KENNAMETAL on a 1921 mark) and never match a 1921-era
    patent assignee. Matching on the original applicant both recovers genuine
    matches (Brown Shoe → not "Brown Group") and drops spurious successor matches.
    """
    rows = conn.execute(f"""
        SELECT cf.serial_no, cf.mark_id_char, o.own_name, uc.us_classes
        FROM case_file cf
        LEFT JOIN (
            SELECT serial_no, own_name FROM (
                SELECT serial_no, own_name,
                       ROW_NUMBER() OVER (PARTITION BY serial_no
                           ORDER BY TRY_CAST(own_type_cd AS INTEGER) NULLS LAST, own_id) AS rn
                FROM owner
            ) WHERE rn = 1
        ) o ON cf.serial_no = o.serial_no
        LEFT JOIN (
            SELECT serial_no, string_agg(DISTINCT us_class_cd, ',') AS us_classes
            FROM us_class GROUP BY serial_no
        ) uc ON cf.serial_no = uc.serial_no
        WHERE cf.mark_draw_cd LIKE '3%'
          AND cf.filing_dt BETWEEN DATE '{year}-01-01' AND DATE '{year}-12-31'
        ORDER BY cf.serial_no
    """).fetchall()
    out = []
    for serial, mark, owner, classes in rows:
        out.append({
            "serial": str(serial), "mark": mark or "", "owner": owner or "",
            "us_classes": classes or "",
        })
    return out


def score_marks(marks: list[dict], counts: dict[str, int], *,
                fuzzy_floor: float = DEFAULT_FUZZY_FLOOR) -> list[dict]:
    """Pure matching core: score `design_mark_owners` rows against an assignee map.

    Each result: serial, mark, owner, norm, is_tech, patents_exact, fuzzy_score,
    patents_fuzzy, fuzzy_assignee. Exact == 0 with fuzzy_score ≥ floor is the
    review tier. No I/O — testable in isolation.
    """
    # token → assignees containing it (long tokens only), for fuzzy candidate lookup
    tok_index: dict[str, set[str]] = defaultdict(set)
    for k in counts:
        for t in _long_tokens(k):
            tok_index[t].add(k)

    results = []
    for m in marks:
        k = norm(m["owner"])
        cls = set(re.split(r"[,\s]+", m["us_classes"].strip())) if m["us_classes"] else set()
        is_tech = bool(cls & TECH_US_CLASSES)
        exact = counts.get(k, 0)
        fuzzy_score, fuzzy_assignee, fuzzy_pat = 0.0, "", 0
        qtok = _long_tokens(k)
        # Require ≥2 long tokens so a lone shared surname can't carry a match.
        if not exact and len(qtok) >= 2:
            cands: set[str] = set()
            for t in qtok:
                cands |= tok_index.get(t, set())
            for c in cands:
                sc = _jaccard(qtok, _long_tokens(c))
                if sc > fuzzy_score:
                    fuzzy_score, fuzzy_assignee, fuzzy_pat = sc, c, counts[c]
            if fuzzy_score < fuzzy_floor:
                fuzzy_score, fuzzy_assignee, fuzzy_pat = 0.0, "", 0
        results.append({
            "serial": m["serial"], "mark": m["mark"], "owner": m["owner"],
            "norm": k, "is_tech": is_tech,
            "patents_exact": exact,
            "fuzzy_score": round(fuzzy_score, 2),
            "patents_fuzzy": fuzzy_pat,
            "fuzzy_assignee": fuzzy_assignee,
        })
    return results


def compute_richness(year: int, *, fuzzy_floor: float = DEFAULT_FUZZY_FLOOR,
                     counts: dict[str, int] | None = None) -> list[dict]:
    """Per-mark richness for a year's design marks (reads patents + trademarks).

    Pass `counts` to reuse a prebuilt assignee map across years.
    """
    if counts is None:
        pc = duckdb.connect(str(config.DB["patents"]), read_only=True)
        counts = assignee_counts(pc)
        pc.close()
    tc = duckdb.connect(str(config.DB["trademarks"]), read_only=True)
    marks = design_mark_owners(tc, year)
    tc.close()
    return score_marks(marks, counts, fuzzy_floor=fuzzy_floor)


def summarise(results: list[dict], fuzzy_floor: float = DEFAULT_FUZZY_FLOOR) -> dict:
    """Aggregate counts for a year's richness results."""
    n = len(results)
    n_exact = sum(1 for r in results if r["patents_exact"] > 0)
    n_fuzzy = sum(1 for r in results
                  if r["patents_exact"] == 0 and r["fuzzy_score"] >= fuzzy_floor)
    n_tech = sum(1 for r in results if r["is_tech"])
    n_match = n_exact + n_fuzzy
    n_tech_match = sum(1 for r in results
                       if r["is_tech"] and (r["patents_exact"] > 0
                                            or r["fuzzy_score"] >= fuzzy_floor))
    n_recovered = sum(1 for r in results
                      if not r["is_tech"] and (r["patents_exact"] > 0
                                               or r["fuzzy_score"] >= fuzzy_floor))
    return {
        "marks": n, "tech": n_tech, "exact": n_exact, "fuzzy": n_fuzzy,
        "any_match": n_match, "tech_match": n_tech_match, "recovered": n_recovered,
    }
