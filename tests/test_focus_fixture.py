"""The synthetic fixture reflects the Phase-34 focus model end-to-end (hermetic)."""

from __future__ import annotations

from markery.common.focus import LinkResolver, load_all_foci, registry_link_maps
from markery.specialist.matchmaker import entities
from tests.fixtures.synthetic import build_synthetic_repo, run_markery


def test_fixture_carries_entity_and_mark_foci(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    foci = load_all_foci(repo.root)
    keys = {(f.type, f.slug) for f in foci}
    assert ("entity", repo.entity_slug) in keys
    assert ("mark", repo.mark_focus_slug) in keys


def test_fixture_registry_has_stored_slug_and_alias(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    conn = entities.open_db(repo.db_ent)
    ents = {e["entity_id"]: e for e in entities.list_entities(conn)}
    assert ents[1]["slug"] == repo.entity_slug

    url_for, aliases = registry_link_maps(conn)
    conn.close()

    r = LinkResolver(url_for=url_for, aliases=aliases)
    # Direct + alias-redirect resolution against the fixture registry.
    assert r.resolve("entity", repo.entity_slug) == f"focus/entity/{repo.entity_slug}/"
    assert r.resolve("entity", "synthex-manufacturing") == f"focus/entity/{repo.entity_slug}/"


def test_cli_export_regenerates_registry_csvs(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    out, rc = run_markery(repo, "matchmaker", "export")
    assert rc == 0, out
    reg = repo.root / "registry"
    names = {p.name for p in reg.glob("*.csv")}
    assert {"entities.csv", "entity_variants.csv", "entity_aliases.csv",
            "persons.csv"} <= names
    header, *rows = (reg / "entities.csv").read_text().splitlines()
    assert header == "entity_id,canonical_name,entity_type,industry,slug,founded,dissolved"
    assert any(repo.entity_slug in r for r in rows)
