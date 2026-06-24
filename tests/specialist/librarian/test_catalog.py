"""Phase 29 P1 — global library catalog + global media acquisition (hermetic)."""

from __future__ import annotations

import json

import pytest

import markery.common.config as cfg
from markery.specialist.librarian import catalog, media  # noqa: F401


@pytest.fixture
def library(tmp_path, monkeypatch):
    """Point config.ROOT at a tmp repo with an empty library/."""
    monkeypatch.setattr(cfg, "ROOT", tmp_path)
    (tmp_path / "library" / "works").mkdir(parents=True)
    (tmp_path / "library" / "media").mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# catalog: load / upsert / atomic / dedup
# ---------------------------------------------------------------------------

def test_upsert_and_load_roundtrip(library):
    catalog.upsert({"id": "a", "kind": "photo", "sha256": "x", "source_url": "u1"})
    catalog.upsert({"id": "b", "kind": "work"})
    items = catalog.load()
    assert set(items) == {"a", "b"}
    assert items["a"]["kind"] == "photo"


def test_upsert_last_wins_per_id(library):
    catalog.upsert({"id": "a", "title": "first"})
    catalog.upsert({"id": "a", "title": "second"})
    items = catalog.load()
    assert len(items) == 1 and items["a"]["title"] == "second"


def test_upsert_requires_id(library):
    with pytest.raises(ValueError):
        catalog.upsert({"kind": "photo"})


def test_dedup_lookups(library):
    catalog.upsert({"id": "a", "sha256": "deadbeef", "source_url": "https://x/a"})
    assert catalog.find_by_sha256("deadbeef")["id"] == "a"
    assert catalog.find_by_source_url("https://x/a")["id"] == "a"
    assert catalog.find_by_sha256("nope") is None
    assert catalog.find_by_source_url("https://x/none") is None


def test_atomic_write_leaves_no_temp(library):
    catalog.upsert({"id": "a"})
    leftovers = list((library / "library").glob(".catalog-*"))
    assert leftovers == []


# ---------------------------------------------------------------------------
# catalog: rebuild from per-item metadata.json
# ---------------------------------------------------------------------------

def test_rebuild_from_works_and_media(library):
    work = library / "library" / "works" / "taussig-book-of-radio"
    work.mkdir(parents=True)
    (work / "metadata.json").write_text(json.dumps({
        "slug": "taussig-book-of-radio", "source": "ia", "title": "The Book of Radio",
        "author": "Taussig", "year": 1922, "ia_identifier": "cu31924003626037",
        "acquired_at": "2026-06-03T20:35:11Z",
    }))
    item = library / "library" / "media" / "combination-square"
    item.mkdir(parents=True)
    (item / "metadata.json").write_text(json.dumps({
        "slug": "combination-square", "kind": "drawing", "title": "Combination Square",
        "source": "wikimedia_commons", "source_url": "https://commons/x",
        "license": "PD", "sha256": "abc", "file": "combination-square.jpg",
    }))

    counts = catalog.rebuild()
    assert counts == {"works": 1, "media": 1}
    items = catalog.load()
    assert items["taussig-book-of-radio"]["kind"] == "work"
    assert items["taussig-book-of-radio"]["source_url"].endswith("cu31924003626037")
    assert items["combination-square"]["kind"] == "drawing"
    assert items["combination-square"]["license"] == "PD"


# ---------------------------------------------------------------------------
# global media acquisition (mocked Commons) + dedup
# ---------------------------------------------------------------------------

def _fake_result():
    from markery.specialist.librarian.sources.commons import CommonsResult
    return CommonsResult(
        title="File:Foo.jpg",
        url="https://upload.wikimedia.org/x/Foo.jpg",
        license="PD", creator="Anon",
        license_url="https://pd", rights_statement="Public domain",
        attribution_text="Anon, public domain",
    )


def test_acquire_commons_global(library, monkeypatch):
    from markery.specialist.librarian import media as media_mod
    from markery.specialist.librarian.sources import commons
    monkeypatch.setattr(commons, "fetch", lambda title: _fake_result())
    monkeypatch.setattr(commons, "download",
                        lambda url, path: (path.parent.mkdir(parents=True, exist_ok=True),
                                           path.write_bytes(b"\x89PNG fake")))

    meta = media_mod.acquire_commons("File:Foo.jpg", kind="photo")
    assert meta is not None
    assert meta["license"] == "PD"
    # File landed in the GLOBAL library/media (not a project).
    assert (library / "library" / "media" / meta["slug"]).is_dir()
    # Registered in the catalog.
    assert catalog.load()[meta["slug"]]["source"] == "wikimedia_commons"
    assert meta in media_mod.list_media() or any(
        i["id"] == meta["slug"] for i in media_mod.list_media())


def test_acquire_commons_dedups_by_source_url(library, monkeypatch):
    from markery.specialist.librarian import media as media_mod
    from markery.specialist.librarian.sources import commons
    calls = {"n": 0}

    def _fetch(title):
        calls["n"] += 1
        return _fake_result()

    monkeypatch.setattr(commons, "fetch", _fetch)
    monkeypatch.setattr(commons, "download",
                        lambda url, path: (path.parent.mkdir(parents=True, exist_ok=True),
                                           path.write_bytes(b"data")))
    media_mod.acquire_commons("File:Foo.jpg")
    media_mod.acquire_commons("File:Foo.jpg")   # second time → dedup, no re-fetch
    assert calls["n"] == 1


def test_acquire_commons_rejects_unadmitted_license(library, monkeypatch):
    from markery.specialist.librarian import media as media_mod
    from markery.specialist.librarian.sources import commons
    from markery.specialist.librarian.sources.commons import CommonsResult
    bad = CommonsResult(title="File:Bad.jpg", url="u", license="CC-BY-NC", creator="",
                        license_url="", rights_statement="", attribution_text="")
    monkeypatch.setattr(commons, "fetch", lambda title: bad)
    assert media_mod.acquire_commons("File:Bad.jpg") is None
