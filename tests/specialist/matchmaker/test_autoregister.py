"""Phase 28 P2 — auto entity registration (companies + people), hermetic."""

from __future__ import annotations

import duckdb

from markery.specialist.matchmaker import autoregister as ar
from markery.specialist.matchmaker.entities import open_db as ent_open_db
from tests.fixtures.synthetic import build_synthetic_repo, ENTITY_VARIANT


def _conns(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    conn_pat = duckdb.connect(str(repo.db_pat), read_only=True)
    conn_tm = duckdb.connect(str(repo.db_tm), read_only=True)
    conn_ent = ent_open_db(repo.db_ent)
    return repo, conn_pat, conn_tm, conn_ent


# ---------------------------------------------------------------------------
# pure helpers
# ---------------------------------------------------------------------------

def test_normalise_and_slug():
    assert ar.normalise_name("Eastman Kodak Company, Inc.") == "EASTMAN KODAK"
    assert ar.slugify("Jane Q. Synthex") == "jane-q-synthex"


def test_score_names():
    q = set(ar.normalise_name("Synthex Manufacturing Company").split())
    assert ar.score_names(q, "SYNTHEX MFG CO") == 1.0
    assert ar.score_names(q, "Totally Unrelated Inc") == 0.0


# ---------------------------------------------------------------------------
# companies
# ---------------------------------------------------------------------------

def test_propose_company_finds_corpus_variants(tmp_path):
    _, conn_pat, conn_tm, conn_ent = _conns(tmp_path)
    prop = ar.propose_company(conn_pat, conn_tm, "Synthex Manufacturing Company")
    sources = {(v["name"], v["source"]) for v in prop["variants"]}
    assert (ENTITY_VARIANT, "patent_assignee") in sources
    assert (ENTITY_VARIANT, "trademark_owner") in sources
    conn_pat.close(); conn_tm.close(); conn_ent.close()


def test_commit_company_creates_and_is_idempotent(tmp_path):
    _, conn_pat, conn_tm, conn_ent = _conns(tmp_path)
    # Use a fresh canonical not already in the fixture.
    prop = ar.propose_company(conn_pat, conn_tm, "Synthex Works")
    prop["canonical"] = "Synthex Works"  # register under a new canonical name
    r1 = ar.commit_company(conn_ent, prop)
    assert r1["created"] is True and r1["variants_added"] >= 1
    # Next id reserves retired (aliased) ids too: the fixture seeds
    # entity_alias(retired_id=9003, ...), so allocation is max(1, 9003)+1 = 9004,
    # never reusing a retired id (Phase 35).
    assert r1["entity_id"] == 9004
    r2 = ar.commit_company(conn_ent, prop)
    assert r2["created"] is False and r2["variants_added"] == 0
    conn_pat.close(); conn_tm.close(); conn_ent.close()


# ---------------------------------------------------------------------------
# people
# ---------------------------------------------------------------------------

def test_propose_people_from_inventors(tmp_path):
    _, conn_pat, conn_tm, conn_ent = _conns(tmp_path)
    props = ar.propose_people_from_inventors(conn_ent, conn_pat)
    names = {p["canonical"] for p in props}
    assert "Jane Synthex" in names
    jane = next(p for p in props if p["canonical"] == "Jane Synthex")
    assert jane["slug"] == "jane-synthex"
    assert jane["patent_count"] == 3  # on all three fixture patents
    conn_pat.close(); conn_tm.close(); conn_ent.close()


def test_commit_people_then_skip_existing(tmp_path):
    _, conn_pat, conn_tm, conn_ent = _conns(tmp_path)
    props = ar.propose_people_from_inventors(conn_ent, conn_pat)
    res = ar.commit_people(conn_ent, props, kind="inventor")
    assert res["people_added"] == len(props) >= 1
    row = conn_ent.execute(
        "SELECT canonical_name, slug, kind FROM person_entity WHERE slug = 'jane-synthex'"
    ).fetchone()
    assert row == ("Jane Synthex", "jane-synthex", "inventor")
    # Re-propose: already-registered inventors are skipped.
    again = ar.propose_people_from_inventors(conn_ent, conn_pat)
    assert again == []
    conn_pat.close(); conn_tm.close(); conn_ent.close()


def test_people_slug_collision_disambiguated(tmp_path):
    repo, conn_pat, conn_tm, conn_ent = _conns(tmp_path)
    # Pre-seed a person whose slug equals the inventor's slug.
    conn_ent.execute(
        "INSERT INTO person_entity (person_id, canonical_name, slug, kind) "
        "VALUES (99, 'Jane Synthex', 'jane-synthex', 'founder')"
    )
    conn_ent.commit()
    props = ar.propose_people_from_inventors(conn_ent, conn_pat)
    # The inventor 'Jane Synthex' is a *new variant* (not yet in person_name_variant),
    # so it is proposed, but with a disambiguated slug.
    jane = next(p for p in props if p["canonical"] == "Jane Synthex")
    assert jane["slug"] == "jane-synthex-2"
    conn_pat.close(); conn_tm.close(); conn_ent.close()
