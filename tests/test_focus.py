"""Hermetic tests for the focus schema + cross-link resolver (Phase 34)."""

from __future__ import annotations

import json

import pytest

from markery.common.focus import (
    Focus,
    FOCUS_TYPES,
    LinkResolver,
    UnresolvedLink,
    default_focus_url,
    load_all_foci,
    registry_link_maps,
)


# --- focus.json manifest ----------------------------------------------------

def test_focus_roundtrip(tmp_path):
    f = Focus(type="mark", subject="71153780", slug="rectigon-71153780",
              title="Rectigon")
    d = f.write(tmp_path)
    assert (d / "focus.json").exists()
    loaded = Focus.load(d / "focus.json")
    assert loaded == f
    assert loaded.link_key == ("mark", "rectigon-71153780")


def test_technology_focus_carries_selector(tmp_path):
    f = Focus(type="technology", subject="tech-0007",
              slug="arc-quenching-circuit-interruption",
              title="Arc-Quenching Circuit Interruption",
              selector={"cpc": ["H01H", "H02B"], "years": [1915, 1940]})
    f.write(tmp_path)
    loaded = Focus.load(Focus.dir(tmp_path, "technology", f.slug) / "focus.json")
    assert loaded.selector["cpc"] == ["H01H", "H02B"]


def test_selector_rejected_on_non_technology():
    with pytest.raises(ValueError):
        Focus(type="entity", subject="9", slug="westinghouse",
              title="Westinghouse", selector={"cpc": ["H01H"]})


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        Focus(type="widget", subject="1", slug="x", title="X")


def test_from_dict_requires_keys():
    with pytest.raises(ValueError):
        Focus.from_dict({"type": "mark", "slug": "x"})  # missing subject/title


def test_load_all_foci_ordered(tmp_path):
    Focus("person", "5", "john-fitzgerald", "John Fitzgerald").write(tmp_path)
    Focus("mark", "71153780", "rectigon-71153780", "Rectigon").write(tmp_path)
    Focus("entity", "9", "westinghouse", "Westinghouse").write(tmp_path)
    foci = load_all_foci(tmp_path)
    # Ordered by FOCUS_TYPES rank, then slug: mark < entity < person.
    assert [f.type for f in foci] == ["mark", "entity", "person"]


def test_load_all_foci_empty(tmp_path):
    assert load_all_foci(tmp_path) == []


# --- resolver ---------------------------------------------------------------

def _resolver():
    return LinkResolver(
        url_for={
            ("entity", "westinghouse"): "focus/entity/westinghouse/",
            ("patent", "us1389147a"): "focus/patent/us1389147a/",
        },
        aliases={("entity", "westinghouse-old"): "westinghouse"},
    )

def test_resolve_direct():
    assert _resolver().resolve("entity", "westinghouse") == "focus/entity/westinghouse/"


def test_resolve_through_alias():
    assert _resolver().resolve("entity", "westinghouse-old") == "focus/entity/westinghouse/"


def test_resolve_unknown_raises():
    with pytest.raises(UnresolvedLink):
        _resolver().resolve("entity", "nope")


def test_resolve_alias_cycle_raises():
    r = LinkResolver(url_for={}, aliases={("entity", "a"): "b", ("entity", "b"): "a"})
    with pytest.raises(UnresolvedLink):
        r.resolve("entity", "a")


def test_resolve_html_replaces_owned_links():
    html = _resolver().resolve_html("See [[entity:westinghouse]] and [[patent:us1389147a]].")
    assert '<a href="focus/entity/westinghouse/">westinghouse</a>' in html
    assert '<a href="focus/patent/us1389147a/">us1389147a</a>' in html


def test_resolve_html_uses_labels():
    html = _resolver().resolve_html(
        "[[entity:westinghouse]]",
        label_for={("entity", "westinghouse"): "Westinghouse Electric"},
    )
    assert ">Westinghouse Electric</a>" in html


def test_resolve_html_passes_through_foreign_namespaces():
    # media/figure are other passes' concern — left verbatim, not failed.
    html = _resolver().resolve_html("[[media:synthex-works]] [[figure:US1]]")
    assert "[[media:synthex-works]]" in html
    assert "[[figure:US1]]" in html


def test_resolve_html_unresolved_fails_build():
    with pytest.raises(UnresolvedLink):
        _resolver().resolve_html("A dangling [[entity:ghost]] link.")


def test_unresolved_lists_owned_only():
    bad = _resolver().unresolved("[[entity:ghost]] [[media:x]] [[patent:us1389147a]]")
    assert bad == [("entity", "ghost")]


def test_default_focus_url():
    assert default_focus_url("technology", "arc") == "focus/technology/arc/"
    assert default_focus_url("cpc", "h01h") == "cpc/h01h/"


# --- registry-derived maps --------------------------------------------------

def test_registry_link_maps_with_alias(tmp_path):
    import duckdb
    from markery.specialist.matchmaker import entities

    conn = entities.open_db(tmp_path / "entities.duckdb")
    conn.execute("INSERT INTO company_entity (entity_id, canonical_name, slug) "
                 "VALUES (9, 'Westinghouse Electric & Manufacturing Company', 'westinghouse')")
    # A retired duplicate id, aliased to the survivor 9, keeping its old slug.
    conn.execute("INSERT INTO entity_alias (retired_id, retired_slug, survivor_id) "
                 "VALUES (9003, 'westinghouse-electric', 9)")
    conn.execute("INSERT INTO person_entity (person_id, canonical_name, slug, kind) "
                 "VALUES (1, 'John W. Fitzgerald', 'john-w-fitzgerald', 'inventor')")
    conn.commit()

    url_for, aliases = registry_link_maps(conn)
    conn.close()

    r = LinkResolver(url_for=url_for, aliases=aliases)
    assert r.resolve("entity", "westinghouse") == "focus/entity/westinghouse/"
    # Retired slug redirects to the survivor's URL.
    assert r.resolve("entity", "westinghouse-electric") == "focus/entity/westinghouse/"
    assert r.resolve("person", "john-w-fitzgerald") == "focus/person/john-w-fitzgerald/"
