"""Phase 30 P1 — PD media adapters (LoC/NARA/DPLA/IA) + unified acquire (hermetic)."""

from __future__ import annotations

import pytest

import markery.common.config as cfg
from markery.specialist.librarian.sources.common import normalize_license, MediaResult
from markery.specialist.librarian.sources import loc, nara, dpla, ia_media, chronam
from markery.specialist.librarian import media, catalog


# ---------------------------------------------------------------------------
# shared license normaliser
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,url,expected", [
    ("No known restrictions on publication.", "", "PD"),
    ("", "http://rightsstatements.org/vocab/NoC-US/1.0/", "PD"),
    ("", "http://rightsstatements.org/vocab/InC/1.0/", None),
    ("", "http://creativecommons.org/publicdomain/zero/1.0/", "CC0"),
    ("", "https://creativecommons.org/licenses/by-sa/4.0/", "CC-BY-SA"),
    ("", "https://creativecommons.org/licenses/by/4.0/", "CC-BY"),
    ("", "https://creativecommons.org/licenses/by-nc/4.0/", None),
    ("All rights reserved", "", None),
    ("U.S. Government work", "", "PD-USGov"),
])
def test_normalize_license(raw, url, expected):
    assert normalize_license(raw, url) == expected


# ---------------------------------------------------------------------------
# LoC
# ---------------------------------------------------------------------------

def test_loc_fetch_admits_pd(monkeypatch):
    monkeypatch.setattr(loc, "_api_get", lambda url: {
        "item": {"title": "Plow", "rights": "No known restrictions on publication.",
                 "contributor_names": ["Bain News Service"]},
        "image_url": ["https://tile.loc.gov/x/plow.jpg"],
    })
    r = loc.fetch("plow123")
    assert r is not None and r.license == "PD" and r.source == "loc"
    assert r.url.endswith("plow.jpg")


def test_loc_fetch_rejects_unevaluated(monkeypatch):
    monkeypatch.setattr(loc, "_api_get", lambda url: {
        "item": {"title": "X", "rights": "Rights status not evaluated."},
        "image_url": ["https://x/y.jpg"],
    })
    assert loc.fetch("x") is None


# ---------------------------------------------------------------------------
# NARA
# ---------------------------------------------------------------------------

def _nara_hit(status, with_obj=True):
    rec = {"title": "Memo", "useRestriction": {"status": {"value": status}}}
    if with_obj:
        rec["digitalObjects"] = [{"objectUrl": "https://nara/obj.jpg"}]
    return {"body": {"hits": {"hits": [{"_source": {"record": rec}}]}}}


def test_nara_fetch_admits_unrestricted(monkeypatch):
    monkeypatch.setattr(nara, "_api_get", lambda path, params: _nara_hit("Unrestricted"))
    r = nara.fetch("12345")
    assert r is not None and r.license == "PD-USGov" and r.url.endswith("obj.jpg")


def test_nara_fetch_rejects_restricted(monkeypatch):
    monkeypatch.setattr(nara, "_api_get", lambda path, params: _nara_hit("Restricted"))
    assert nara.fetch("12345") is None


# ---------------------------------------------------------------------------
# DPLA — key gating + admission
# ---------------------------------------------------------------------------

def test_dpla_key_missing_raises(monkeypatch):
    monkeypatch.delenv("DPLA_API_KEY", raising=False)
    with pytest.raises(dpla.DPLAKeyMissing):
        dpla.search("anything")


def test_dpla_fetch_admits_rightsstatements_noc(monkeypatch):
    monkeypatch.setenv("DPLA_API_KEY", "k")
    monkeypatch.setattr(dpla, "_api_get", lambda path, params: {"docs": [{
        "id": "abc", "object": "https://dpla/thumb.jpg",
        "sourceResource": {"title": "Poster",
                           "rights": "http://rightsstatements.org/vocab/NoC-US/1.0/"},
        "provider": {"name": "NYPL"},
    }]})
    r = dpla.fetch("abc")
    assert r is not None and r.license == "PD" and r.source == "dpla"


# ---------------------------------------------------------------------------
# Internet Archive media
# ---------------------------------------------------------------------------

def test_ia_media_fetch_admits_pd_mark(monkeypatch):
    monkeypatch.setattr(ia_media, "_get", lambda url: {
        "metadata": {"title": "Factory", "identifier": "factory1",
                     "licenseurl": "http://creativecommons.org/publicdomain/mark/1.0/"},
        "files": [{"name": "thumb.gif", "source": "derivative"},
                  {"name": "factory.jpg", "source": "original"}],
    })
    r = ia_media.fetch("factory1")
    assert r is not None and r.license == "PD"
    assert r.url.endswith("factory.jpg")   # prefers the original


# ---------------------------------------------------------------------------
# Chronicling America (newspapers) — date-capped PD clippings
# ---------------------------------------------------------------------------

def test_chronam_search_builds_year_range(monkeypatch):
    captured = {}

    def _get(url):
        captured["url"] = url
        return {"items": [{"id": "/lccn/sn1/1925-01-01/ed-1/seq-1/"}]}

    monkeypatch.setattr(chronam, "_get", _get)
    ids = chronam.search("plows", year_start=1920, year_end=1930)
    assert ids == ["/lccn/sn1/1925-01-01/ed-1/seq-1/"]
    assert "date1=1920" in captured["url"] and "date2=1930" in captured["url"]


def test_chronam_fetch_admits_pd_date(monkeypatch):
    monkeypatch.setattr(chronam, "_get", lambda url: {
        "issue": {"date_issued": "1925-03-04"},
        "title": {"name": "The Daily Planet"}, "sequence": 1,
    })
    r = chronam.fetch("/lccn/sn1/1925-03-04/ed-1/seq-1/")
    assert r is not None and r.license == "PD" and r.kind == "clipping"
    assert r.url.endswith("seq-1.jpg")
    assert "Chronicling America" in r.attribution_text and "1925-03-04" in r.attribution_text


def test_chronam_fetch_rejects_in_copyright(monkeypatch):
    monkeypatch.setattr(chronam, "_get", lambda url: {
        "issue": {"date_issued": "2010-01-01"}, "title": {"name": "Modern Times"},
    })
    assert chronam.fetch("/lccn/sn9/2010-01-01/ed-1/seq-1/") is None


# ---------------------------------------------------------------------------
# unified media.acquire dispatch + dedup
# ---------------------------------------------------------------------------

@pytest.fixture
def library(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "ROOT", tmp_path)
    (tmp_path / "library" / "media").mkdir(parents=True)
    return tmp_path


def test_acquire_dispatches_and_stores(library, monkeypatch):
    result = MediaResult(
        source="loc", source_id="plow123", title="Steel Plow",
        url="https://tile.loc.gov/x/plow.jpg", license="PD",
        creator="Bain", license_url="", rights_statement="No known restrictions",
        attribution_text="Steel Plow — Library of Congress (PD)",
        source_url="https://www.loc.gov/item/plow123/",
    )
    monkeypatch.setattr(loc, "fetch", lambda ident, **kw: result)
    monkeypatch.setattr(loc, "download",
                        lambda url, dest: (dest.parent.mkdir(parents=True, exist_ok=True),
                                           dest.write_bytes(b"\x89PNG loc"))[-1])
    meta = media.acquire("loc", "plow123")
    assert meta is not None and meta["source"] == "loc" and meta["license"] == "PD"
    assert (library / "library" / "media" / meta["slug"]).is_dir()
    assert catalog.load()[meta["slug"]]["source"] == "loc"


def test_acquire_dedups_by_source_url(library, monkeypatch):
    result = MediaResult(
        source="loc", source_id="p1", title="P", url="https://loc/p.jpg",
        license="PD", creator="", license_url="", rights_statement="PD",
        attribution_text="P (PD)", source_url="https://loc/item/p1/")
    calls = {"dl": 0}

    def _dl(url, dest):
        calls["dl"] += 1
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"x")
        return dest

    monkeypatch.setattr(loc, "fetch", lambda ident, **kw: result)
    monkeypatch.setattr(loc, "download", _dl)
    media.acquire("loc", "p1")
    media.acquire("loc", "p1")
    assert calls["dl"] == 1   # second call deduped on source_url


def test_acquire_rejects_unadmitted(library, monkeypatch):
    monkeypatch.setattr(nara, "fetch", lambda ident, **kw: None)
    assert media.acquire("nara", "999") is None


def test_acquire_unknown_source_raises(library):
    with pytest.raises(ValueError):
        media.acquire("flickr", "x")
