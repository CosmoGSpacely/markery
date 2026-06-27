"""Phase 32 P2a — local mark↔patent seed pairs, hermetic."""

from __future__ import annotations

from datetime import date

import duckdb

from markery.specialist.matchmaker import seed as sd
from tests.fixtures.synthetic import build_synthetic_repo, REVIEW_YEAR, REVIEW_SERIAL


def _marks(owner="Acme Widget Co.", filing=date(1921, 6, 1), us="021"):
    return [{"serial": "1", "mark": "A", "owner": owner, "us_classes": us, "filing": filing}]


def test_window_filters_distant_patents_and_scores():
    patents = {"ACME WIDGET": [
        {"patent_no": "US1", "app_dt": date(1918, 1, 1), "grant_dt": date(1920, 1, 1), "cpc": ["H01J"]},
        {"patent_no": "US2", "app_dt": date(1900, 1, 1), "grant_dt": date(1902, 1, 1), "cpc": ["B42F"]},
    ]}
    pairs = sd.build_seed_pairs(_marks(), patents, window=12)
    # US2 (granted 1902, ~19y before the 1921 filing) is outside the ±12y window
    assert [p["patent_no"] for p in pairs] == ["US1"]
    p = pairs[0]
    assert p["match"] == "exact" and p["owner_conf"] == 1.0 and p["is_tech"]
    # exact owner + patent granted ~1y before filing → high score
    assert p["score"] > 0.9 and p["cpc"] == ["H01J"]


def test_min_score_drops_low_pairs():
    patents = {"ACME WIDGET": [
        {"patent_no": "US1", "app_dt": None, "grant_dt": date(1920, 1, 1), "cpc": []},
    ]}
    assert sd.build_seed_pairs(_marks(), patents, min_score=0.0)
    assert sd.build_seed_pairs(_marks(), patents, min_score=0.99) == []


def test_no_match_yields_no_pairs():
    patents = {"SOMEONE ELSE": [
        {"patent_no": "US9", "app_dt": None, "grant_dt": date(1920, 1, 1), "cpc": []},
    ]}
    assert sd.build_seed_pairs(_marks(), patents) == []


def test_pairs_sorted_by_score_desc():
    patents = {"ACME WIDGET": [
        {"patent_no": "US_far", "app_dt": None, "grant_dt": date(1912, 1, 1), "cpc": []},
        {"patent_no": "US_near", "app_dt": None, "grant_dt": date(1921, 1, 1), "cpc": []},
    ]}
    pairs = sd.build_seed_pairs(_marks(), patents, window=12)
    assert [p["patent_no"] for p in pairs] == ["US_near", "US_far"]
    assert pairs[0]["score"] >= pairs[1]["score"]


def test_summarise_counts_and_cpc():
    patents = {"ACME WIDGET": [
        {"patent_no": "US1", "app_dt": None, "grant_dt": date(1920, 1, 1), "cpc": ["H01J", "B42F"]},
        {"patent_no": "US2", "app_dt": None, "grant_dt": date(1922, 1, 1), "cpc": ["H01J"]},
    ]}
    s = sd.summarise(sd.build_seed_pairs(_marks(), patents, window=12))
    assert s["pairs"] == 2 and s["marks"] == 1 and s["tech_marks"] == 1
    assert s["exact"] == 2 and s["fuzzy"] == 0
    assert list(s["cpc_subclasses"].items())[0] == ("H01J", 2)   # most productive first


def test_seed_pairs_end_to_end_on_fixture(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    conn = duckdb.connect(str(repo.db_tm), read_only=True)
    from markery.specialist.matchmaker import richness as rich
    marks = rich.design_mark_owners(conn, REVIEW_YEAR)
    conn.close()
    patents = {rich.norm("ART DECO DESIGNS INC"): [
        {"patent_no": "US7", "app_dt": date(1934, 1, 1), "grant_dt": date(1935, 1, 1), "cpc": ["B44F"]},
    ]}
    pairs = sd.build_seed_pairs(marks, patents, window=12)
    by_serial = {p["serial"]: p for p in pairs}
    p = by_serial[str(REVIEW_SERIAL)]
    assert p["patent_no"] == "US7" and p["match"] == "exact" and p["is_tech"]
