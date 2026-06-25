"""Phase 30 P4 — book discovery (Open Library) + routing + ILL prep (hermetic)."""

from __future__ import annotations

import pytest

from markery.specialist.librarian import books
from markery.specialist.librarian.sources import openlibrary


_OL_RESP = {"docs": [
    {"title": "Big Business and Radio", "author_name": ["Archer, Gleason"],
     "first_publish_year": 1939, "ia": ["bigbusinessradio00arch"],
     "isbn": ["123"], "key": "/works/OL1W"},
    {"title": "An Obscure Monograph", "author_name": ["Nobody"],
     "first_publish_year": 1928, "isbn": ["999"], "key": "/works/OL2W"},
]}


def test_openlibrary_search_normalizes(monkeypatch):
    monkeypatch.setattr(openlibrary, "_get", lambda url: _OL_RESP)
    out = openlibrary.search("radio")
    assert out[0]["ia_ids"] == ["bigbusinessradio00arch"]
    assert out[0]["author"] == "Archer, Gleason" and out[0]["year"] == 1939
    assert out[1]["ia_ids"] == []   # no digitized copy


def test_route_digitized_vs_ill():
    digitized = {"title": "T", "author": "A", "ia_ids": ["id1"]}
    assert books.route(digitized)["action"] == "acquire"
    assert books.route(digitized)["ia_id"] == "id1"

    needs_ill = {"title": "Obscure", "author": "Nobody", "year": 1928, "isbn": "999", "ia_ids": []}
    r = books.route(needs_ill)
    assert r["action"] == "ill" and r["ia_id"] is None
    assert "search.worldcat.org" in r["worldcat_url"]
    assert "ILL REQUEST" in r["ill_request"] and "Obscure" in r["ill_request"]


def test_worldcat_url_and_prepare_ill():
    assert books.worldcat_url("Filing Systems", "Smith").startswith("https://search.worldcat.org/search?q=")
    text = books.prepare_ill({"title": "Filing Systems", "author": "Smith",
                              "year": 1912, "isbn": "x"})
    assert "Filing Systems" in text and "interlibrary-loan" in text
    assert "search.worldcat.org" in text


def test_find_books_delegates(monkeypatch):
    monkeypatch.setattr(openlibrary, "_get", lambda url: _OL_RESP)
    out = books.find_books("radio", max_results=5)
    assert len(out) == 2 and out[0]["title"] == "Big Business and Radio"
