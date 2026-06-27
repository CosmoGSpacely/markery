"""Phase 32 P1 — assignee-overlap richness signal, hermetic."""

from __future__ import annotations

import duckdb

from markery.specialist.matchmaker import richness as rich
from tests.fixtures.synthetic import build_synthetic_repo, REVIEW_YEAR, REVIEW_SERIAL


# ---------------------------------------------------------------------------
# pure helpers
# ---------------------------------------------------------------------------

def test_norm_strips_country_tag():
    # The [US] tag EPO assignees carry must not block a match.
    assert rich.norm("EASTMAN KODAK CO [US]") == rich.norm("Eastman Kodak Company")


def test_jaccard_and_summarise():
    rows = [
        {"is_tech": True,  "patents_exact": 6, "fuzzy_score": 0.0},   # tech ∩ match
        {"is_tech": True,  "patents_exact": 0, "fuzzy_score": 0.0},   # tech, no match
        {"is_tech": False, "patents_exact": 3, "fuzzy_score": 0.0},   # recovered (exact)
        {"is_tech": False, "patents_exact": 0, "fuzzy_score": 0.9},   # recovered (fuzzy)
        {"is_tech": False, "patents_exact": 0, "fuzzy_score": 0.0},   # nothing
    ]
    s = rich.summarise(rows, fuzzy_floor=0.8)
    assert s == {"marks": 5, "tech": 2, "exact": 2, "fuzzy": 1,
                 "any_match": 3, "tech_match": 1, "recovered": 2}


# ---------------------------------------------------------------------------
# matching core (pure, no DB)
# ---------------------------------------------------------------------------

def test_score_marks_exact_fuzzy_and_guard():
    counts = {
        "ACME WIDGET": 5,                     # exact target
        "GREAT LAKES VALVE WORKS DETROIT": 3,  # fuzzy target (4∩ of 5 = 0.8)
        "HALL": 9,                            # lone surname — must NOT carry a match
    }
    marks = [
        {"serial": "1", "mark": "A", "owner": "Acme Widget Co., Inc.", "us_classes": "021"},
        {"serial": "2", "mark": "B", "owner": "Great Lakes Valve Works", "us_classes": ""},
        {"serial": "3", "mark": "C", "owner": "E.C. Hall Company", "us_classes": ""},
        {"serial": "4", "mark": "D", "owner": "Unrelated Brand", "us_classes": ""},
    ]
    out = {r["serial"]: r for r in rich.score_marks(marks, counts, fuzzy_floor=0.8)}
    # exact normalised match, despite Co./Inc. suffixes; tech flag from US class 021
    assert out["1"]["patents_exact"] == 5 and out["1"]["is_tech"]
    # fuzzy match recovers a non-tech owner (4 shared of 5 tokens = 0.8 ≥ floor)
    assert out["2"]["patents_exact"] == 0 and out["2"]["fuzzy_score"] >= 0.8
    assert out["2"]["patents_fuzzy"] == 3 and not out["2"]["is_tech"]
    # lone shared surname is guarded out (needs ≥2 long tokens)
    assert out["3"]["patents_exact"] == 0 and out["3"]["fuzzy_score"] == 0.0
    # genuinely unrelated owner matches nothing
    assert out["4"]["patents_exact"] == 0 and out["4"]["fuzzy_score"] == 0.0


# ---------------------------------------------------------------------------
# DB-backed readers against the synthetic repo
# ---------------------------------------------------------------------------

def test_design_mark_owners_reads_review_year(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    conn = duckdb.connect(str(repo.db_tm), read_only=True)
    marks = rich.design_mark_owners(conn, REVIEW_YEAR)
    conn.close()
    by_serial = {m["serial"]: m for m in marks}
    m = by_serial[str(REVIEW_SERIAL)]
    assert m["owner"] == "ART DECO DESIGNS INC"
    assert "026" in m["us_classes"]          # tech US class present in fixture


def test_assignee_counts_normalises(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    conn = duckdb.connect(str(repo.db_pat), read_only=True)
    counts = rich.assignee_counts(conn)
    conn.close()
    # all fixture patents share one assignee → one normalised key with the full count
    assert sum(counts.values()) >= 3
    assert all(k == rich.norm(k) for k in counts)   # keys already normalised


def test_score_marks_end_to_end_on_fixture(tmp_path):
    """design_mark_owners → score_marks with an injected assignee map matching the owner."""
    repo = build_synthetic_repo(tmp_path)
    conn = duckdb.connect(str(repo.db_tm), read_only=True)
    marks = rich.design_mark_owners(conn, REVIEW_YEAR)
    conn.close()
    counts = {rich.norm("ART DECO DESIGNS INC"): 4}
    out = {r["serial"]: r for r in rich.score_marks(marks, counts)}
    r = out[str(REVIEW_SERIAL)]
    assert r["patents_exact"] == 4 and r["is_tech"]
