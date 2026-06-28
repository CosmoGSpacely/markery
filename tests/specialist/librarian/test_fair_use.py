"""Fair-use acquisition tier — non-commercial permissive media policy."""

from __future__ import annotations

import pytest

from markery.common import config as cfg
from markery.specialist.librarian import media, catalog
from markery.specialist.librarian.sources import loc, commons
from markery.specialist.librarian.sources.common import (
    normalize_license, FAIR_USE_TAGS, MediaResult,
)


# --- normalize_license: strict rejects, fair-use tags honestly ---------------

@pytest.mark.parametrize("raw,url", [
    ("All rights reserved", ""),
    ("", "https://rightsstatements.org/vocab/InC/1.0/"),
    ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/"),
    ("CC BY-ND", ""),
    ("", ""),
])
def test_strict_rejects_fairuse_tags(raw, url):
    assert normalize_license(raw, url) is None                      # strict: rejected
    tag = normalize_license(raw, url, fair_use=True)                # fair-use: honest tag
    assert tag in FAIR_USE_TAGS


def test_fairuse_tag_specificity():
    assert normalize_license("CC BY-NC", "", fair_use=True) == "CC-BY-NC"
    assert normalize_license("CC BY-NC-ND", "", fair_use=True) == "CC-BY-NC-ND"
    assert normalize_license("", "https://rightsstatements.org/vocab/InC/1.0/",
                             fair_use=True) == "InC"
    assert normalize_license("mystery rights", "", fair_use=True) == "rights-unknown"


def test_admitted_still_resolves_under_fairuse():
    # PD/CC items keep their precise admitted code even in the fair-use tier.
    assert normalize_license("public domain", "", fair_use=True) == "PD"
    assert normalize_license("CC0", "", fair_use=True) == "CC0"


def test_commons_resolve_license_fairuse_tags_restriction():
    extmeta = {"Restrictions": {"value": "trademarked"},
               "License": {"value": "pd"}, "Artist": {"value": "Acme"}}
    assert commons.resolve_license(extmeta) is None                 # strict
    resolved = commons.resolve_license(extmeta, fair_use=True)
    assert resolved["license"] == "rights-restricted"


# --- media.acquire: strict rejects non-admitted, fair-use stores it ----------

@pytest.fixture()
def library(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "ROOT", tmp_path)
    (tmp_path / "library" / "media").mkdir(parents=True)
    return tmp_path


def _incopyright_result():
    return MediaResult(
        source="loc", source_id="modern1", title="Modern Poster",
        url="https://tile.loc.gov/x/modern.jpg", license="InC",
        creator="Studio", license_url="", rights_statement="In copyright (fair use)",
        attribution_text="Modern Poster — Library of Congress (InC)",
        source_url="https://www.loc.gov/item/modern1/")


def test_acquire_strict_rejects_incopyright(library, monkeypatch):
    monkeypatch.setattr(loc, "fetch",
                        lambda ident, fair_use=False: None if not fair_use else _incopyright_result())
    assert media.acquire("loc", "modern1") is None                  # strict path


def test_acquire_fairuse_stores_with_honest_tag(library, monkeypatch):
    monkeypatch.setattr(loc, "fetch",
                        lambda ident, fair_use=False: _incopyright_result() if fair_use else None)
    monkeypatch.setattr(loc, "download",
                        lambda url, dest: (dest.parent.mkdir(parents=True, exist_ok=True),
                                           dest.write_bytes(b"\x89PNG"))[-1])
    meta = media.acquire("loc", "modern1", fair_use=True)
    assert meta is not None and meta["license"] == "InC"
    assert catalog.load()[meta["slug"]]["license"] == "InC"         # honest tag persisted
