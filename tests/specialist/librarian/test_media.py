"""Tests for Phase 24 P2 media acquisition: Commons license resolution + storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import markery.common.project as _proj_mod
from markery.specialist.librarian.sources import commons
from markery.specialist.librarian import media


def _ext(**pairs) -> dict:
    """Build an extmetadata block ({key: {'value': ...}})."""
    return {k: {"value": v} for k, v in pairs.items()}


# ── license resolution ───────────────────────────────────────────────────────

def test_admits_pd_and_cc0():
    assert commons.resolve_license(_ext(License="pd", LicenseShortName="Public domain"))["license"] == "PD"
    assert commons.resolve_license(_ext(License="cc0", LicenseShortName="CC0"))["license"] == "CC0"


def test_admits_cc_by_and_by_sa_with_attribution():
    by = commons.resolve_license(_ext(License="cc-by-4.0", LicenseShortName="CC BY 4.0",
                                      Artist="<a>Jane Roe</a>"))
    assert by["license"] == "CC-BY"
    assert "Jane Roe" in by["attribution_text"] and "CC BY 4.0" in by["attribution_text"]
    sa = commons.resolve_license(_ext(License="cc-by-sa-3.0", LicenseShortName="CC BY-SA 3.0"))
    assert sa["license"] == "CC-BY-SA"


def test_rejects_nc_nd_and_restrictions():
    assert commons.resolve_license(_ext(License="cc-by-nc-4.0", LicenseShortName="CC BY-NC")) is None
    assert commons.resolve_license(_ext(License="cc-by-nd-4.0", LicenseShortName="CC BY-ND")) is None
    # A non-empty Restrictions field (e.g. trademark) rejects even a PD file.
    assert commons.resolve_license(_ext(License="pd", LicenseShortName="Public domain",
                                        Restrictions="trademarked")) is None


def test_rejects_unknown_license():
    assert commons.resolve_license(_ext(License="all rights reserved")) is None
    assert commons.resolve_license(_ext()) is None


def test_pd_attribution_is_rights_only_when_creator_unknown():
    r = commons.resolve_license(_ext(License="pd", LicenseShortName="Public domain"))
    assert r["creator"] == "Unknown"
    assert r["attribution_text"] == "Public domain"


# ── acquisition + storage ────────────────────────────────────────────────────

@pytest.fixture()
def project_root(tmp_path, monkeypatch):
    (tmp_path / "projects" / "demo").mkdir(parents=True)
    monkeypatch.setattr(_proj_mod, "ROOT", tmp_path)
    return tmp_path


def test_acquire_commons_stores_metadata_and_index(project_root, monkeypatch):
    monkeypatch.setattr(commons, "fetch", lambda title: commons.CommonsResult(
        title=title, url="https://upload.wikimedia.org/x/Deere.jpg", license="PD",
        creator="Unknown", license_url="", rights_statement="Public domain",
        attribution_text="Public domain",
    ))
    monkeypatch.setattr(commons, "download",
                        lambda url, dest: (dest.parent.mkdir(parents=True, exist_ok=True),
                                           dest.write_bytes(b"\x89PNG fake"), dest)[-1])

    meta = media.acquire_commons("demo", "File:John Deere plow.jpg", kind="photo")
    assert meta is not None
    assert meta["license"] == "PD"
    assert meta["source"] == "wikimedia_commons"
    assert meta["format"] == "jpg"
    assert meta["sha256"]
    # Files on disk
    item = media.media_dir("demo") / meta["slug"]
    assert (item / "metadata.json").exists()
    assert (item / meta["file"]).exists()
    # Index updated and listable
    listed = media.list_media("demo")
    assert len(listed) == 1 and listed[0]["slug"] == meta["slug"]


def test_acquire_commons_rejects_unadmitted(project_root, monkeypatch):
    monkeypatch.setattr(commons, "fetch", lambda title: None)  # resolve_license rejected
    assert media.acquire_commons("demo", "File:Copyrighted.jpg") is None
    assert media.list_media("demo") == []
