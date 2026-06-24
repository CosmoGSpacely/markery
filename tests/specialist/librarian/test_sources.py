"""Mocked-HTTP tests for the librarian source adapters (ia, gutenberg).

The adapters call urllib.request.urlopen; we patch it per-module with a fake
response so the search / metadata / download / normalise paths run without
network. Follows the precedent of the well-tested commons.py adapter.
"""

from __future__ import annotations

import io
import json
from contextlib import contextmanager

import pytest

from markery.specialist.librarian.sources import ia, gutenberg
from markery.specialist.librarian.sources.common import IAResult, GutenbergResult


@contextmanager
def _resp(payload):
    """A urlopen() stand-in: context manager whose .read() yields the payload."""
    data = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload).encode()
    yield io.BytesIO(data)


def _patch_urlopen(monkeypatch, module, payload):
    monkeypatch.setattr(module.urllib.request, "urlopen",
                        lambda *a, **k: _resp(payload))


# ---------------------------------------------------------------------------
# Internet Archive
# ---------------------------------------------------------------------------

class TestIA:
    SEARCH = {"response": {"docs": [
        {"identifier": "filingsystems00smith", "title": "Filing Systems",
         "creator": ["Smith, John"], "date": "1912", "access-restricted-item": ""},
        {"identifier": "lockedbook00doe", "title": "Locked Book",
         "creator": "Doe, Jane", "date": "1920", "access-restricted-item": "true"},
    ]}}

    META_OPEN = {"metadata": {"access-restricted-item": ""},
                 "files": [{"name": "filingsystems00smith_djvu.txt"},
                           {"name": "cover.jpg"}]}

    def test_search_parses_open_and_borrow(self, monkeypatch):
        _patch_urlopen(monkeypatch, ia, self.SEARCH)
        results = ia.search("filing systems")
        assert [r.identifier for r in results] == ["filingsystems00smith", "lockedbook00doe"]
        assert results[0].access == "open"
        assert results[1].access == "borrow"
        assert results[0].author == "Smith, John"  # list creator → first element
        assert results[0].year == 1912

    def test_fetch_metadata(self, monkeypatch):
        _patch_urlopen(monkeypatch, ia, self.META_OPEN)
        meta = ia.fetch_metadata("filingsystems00smith")
        assert meta["metadata"]["access-restricted-item"] == ""

    def test_is_open_access(self):
        assert ia.is_open_access(self.META_OPEN) is True
        assert ia.is_open_access({"metadata": {"access-restricted-item": "true"}}) is False

    def test_find_text_filename_canonical(self):
        name = ia.find_text_filename("filingsystems00smith", self.META_OPEN)
        assert name == "filingsystems00smith_djvu.txt"

    def test_find_text_filename_none(self):
        assert ia.find_text_filename("x", {"files": [{"name": "cover.jpg"}]}) is None

    def test_download_text_open(self, monkeypatch, tmp_path):
        # First urlopen → metadata; second → text bytes. Sequence the responses.
        responses = [_resp(self.META_OPEN), _resp(b"OCR TEXT BODY")]
        monkeypatch.setattr(ia.urllib.request, "urlopen",
                            lambda *a, **k: responses.pop(0))
        out = ia.download_text("filingsystems00smith", tmp_path)
        assert out.read_bytes() == b"OCR TEXT BODY"

    def test_download_text_borrow_raises(self, monkeypatch, tmp_path):
        _patch_urlopen(monkeypatch, ia, {"metadata": {"access-restricted-item": "true"}})
        with pytest.raises(PermissionError):
            ia.download_text("lockedbook00doe", tmp_path)

    def test_download_text_no_ocr_raises(self, monkeypatch, tmp_path):
        _patch_urlopen(monkeypatch, ia,
                       {"metadata": {"access-restricted-item": ""}, "files": []})
        with pytest.raises(FileNotFoundError):
            ia.download_text("notext00x", tmp_path)

    def test_to_source_result(self):
        sr = ia.to_source_result(IAResult("id00x", "A Title", "Smith, J", 1910, "open"))
        assert sr.source == "ia" and sr.identifier == "id00x" and sr.slug

    def test_guess_identifiers(self):
        cands = ia.guess_identifiers("The Filing System", "John Smith")
        # All candidates carry the surname stem; "filing"/"system" drop the article.
        assert all("smit" in c for c in cands)
        assert any("filing" in c for c in cands)
        assert len(cands) == len(set(cands))  # deduplicated


# ---------------------------------------------------------------------------
# Project Gutenberg (Gutendex)
# ---------------------------------------------------------------------------

class TestGutenberg:
    SEARCH = {"results": [
        {"id": 1342, "title": "Pride and Prejudice",
         "authors": [{"name": "Austen, Jane"}], "copyright_year": None},
    ]}
    META = {"id": 1342, "title": "Pride and Prejudice",
            "authors": [{"name": "Austen, Jane"}],
            "formats": {"text/plain; charset=utf-8": "https://gutenberg/1342.txt"}}

    def test_search(self, monkeypatch):
        _patch_urlopen(monkeypatch, gutenberg, self.SEARCH)
        results = gutenberg.search("pride prejudice")
        assert results[0].book_id == "1342"
        assert results[0].author == "Austen, Jane"

    def test_fetch_metadata(self, monkeypatch):
        _patch_urlopen(monkeypatch, gutenberg, self.META)
        assert gutenberg.fetch_metadata(1342)["id"] == 1342

    def test_get_text_url(self):
        assert gutenberg.get_text_url(self.META) == "https://gutenberg/1342.txt"
        assert gutenberg.get_text_url({"formats": {}}) is None

    def test_download_text(self, monkeypatch, tmp_path):
        responses = [_resp(self.META), _resp(b"BOOK TEXT")]
        monkeypatch.setattr(gutenberg.urllib.request, "urlopen",
                            lambda *a, **k: responses.pop(0))
        out = gutenberg.download_text(1342, tmp_path)
        assert out.read_bytes() == b"BOOK TEXT"

    def test_download_text_no_format_raises(self, monkeypatch, tmp_path):
        _patch_urlopen(monkeypatch, gutenberg, {"id": 9, "formats": {}})
        with pytest.raises(FileNotFoundError):
            gutenberg.download_text(9, tmp_path)

    def test_to_source_result(self):
        sr = gutenberg.to_source_result(GutenbergResult("1342", "Pride", "Austen", None))
        assert sr.source == "gutenberg" and sr.access is None and sr.slug
