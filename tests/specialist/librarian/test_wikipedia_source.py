"""Tests for the Wikipedia citation-discovery adapter.

Template parsing and title matching are pure; fetch_citations and
resolve_to_source are covered with mocked urlopen / mocked ia+gutenberg.
"""

from __future__ import annotations

import io
import json
from contextlib import contextmanager

from markery.specialist.librarian.sources import wikipedia as wp
from markery.specialist.librarian.sources.common import WikiCitation, IAResult, GutenbergResult


@contextmanager
def _resp(payload):
    yield io.BytesIO(json.dumps(payload).encode())


# ---------------------------------------------------------------------------
# pure: template parsing
# ---------------------------------------------------------------------------

def test_parse_template_params_basic():
    p = wp._parse_template_params("title=Filing Systems |last=Smith |first=John |year=1912")
    assert p["title"] == "Filing Systems"
    assert p["last"] == "Smith"
    assert p["year"] == "1912"


def test_parse_template_params_ignores_nested_pipes():
    p = wp._parse_template_params("title=A {{lang|en|Book}} |year=1920")
    assert p["title"] == "A {{lang|en|Book}}"
    assert p["year"] == "1920"


def test_extract_templates_balanced():
    text = "intro {{cite book|title=One}} mid {{cite book|title=Two|ref={{harv}}}} end"
    tpls = wp._extract_templates(text, "cite book")
    assert len(tpls) == 2
    assert tpls[1].endswith("}}") and "Two" in tpls[1]


def test_template_to_citation_last_first():
    c = wp._template_to_citation(
        "{{cite book|title=Filing Systems|last=Smith|first=John|year=1912|isbn=123}}",
        "cite book")
    assert c.title == "Filing Systems"
    assert c.author == "Smith, John"
    assert c.year == 1912
    assert c.isbn == "123"
    assert c.template_type == "cite book"


def test_template_to_citation_author_and_date_year():
    c = wp._template_to_citation(
        "{{cite journal|title=Paper|author=Jane Doe|date=March 1925}}", "cite journal")
    assert c.author == "Jane Doe"
    assert c.year == 1925


def test_template_to_citation_last1_fallback():
    c = wp._template_to_citation(
        "{{cite book|title=X|last1=Roe|first1=Amy}}", "cite book")
    assert c.author == "Roe, Amy"


# ---------------------------------------------------------------------------
# pure: title matching
# ---------------------------------------------------------------------------

def test_title_matches_significant_words():
    assert wp._title_matches("The Filing System Manual", "Filing System") is True
    assert wp._title_matches("Completely Different", "Filing System") is False


def test_title_matches_empty_target():
    assert wp._title_matches("anything", "the a of") is False


# ---------------------------------------------------------------------------
# fetch_citations (mocked urlopen)
# ---------------------------------------------------------------------------

def test_fetch_citations_extracts_and_dedupes(monkeypatch):
    wikitext = (
        "{{cite book|title=Filing Systems|last=Smith|first=John|year=1912}}\n"
        "{{cite book|title=Filing Systems|last=Smith|first=John|year=1912}}\n"
        "{{cite journal|title=A Study|author=Roe|date=1930}}"
    )
    payload = {"parse": {"wikitext": {"*": wikitext}}}
    monkeypatch.setattr(wp.urllib.request, "urlopen", lambda *a, **k: _resp(payload))
    cites = wp.fetch_citations("Card index")
    titles = [c.title for c in cites]
    assert titles == ["Filing Systems", "A Study"]  # deduplicated


def test_fetch_citations_api_error(monkeypatch):
    payload = {"error": {"info": "missingtitle"}}
    monkeypatch.setattr(wp.urllib.request, "urlopen", lambda *a, **k: _resp(payload))
    import pytest
    with pytest.raises(ValueError):
        wp.fetch_citations("Nonexistent")


# ---------------------------------------------------------------------------
# resolve_to_source (mocked ia / gutenberg)
# ---------------------------------------------------------------------------

def test_resolve_via_ia_identifier(monkeypatch):
    cit = WikiCitation("Filing Systems", "John Smith", 1912, None, None, "cite book")
    monkeypatch.setattr(wp._ia, "guess_identifiers", lambda t, a: ["filingsystems00smith"])
    monkeypatch.setattr(wp._ia, "fetch_metadata", lambda i: {
        "metadata": {"title": "Filing Systems", "creator": "Smith, John",
                     "access-restricted-item": ""}})
    sr = wp.resolve_to_source(cit)
    assert sr is not None
    assert sr.source == "ia" and sr.access == "open"


def test_resolve_falls_back_to_gutenberg(monkeypatch):
    cit = WikiCitation("Pride and Prejudice", "Austen", 1813, None, None, "cite book")
    monkeypatch.setattr(wp._ia, "guess_identifiers", lambda t, a: [])
    monkeypatch.setattr(wp._gut, "search",
                        lambda q, max_results=3: [GutenbergResult("1342", "Pride and Prejudice", "Austen", None)])
    sr = wp.resolve_to_source(cit)
    assert sr is not None and sr.source == "gutenberg"


def test_resolve_returns_none_when_nothing_matches(monkeypatch):
    cit = WikiCitation("Obscure Work", "Nobody", 1900, None, None, "cite book")
    monkeypatch.setattr(wp._ia, "guess_identifiers", lambda t, a: [])
    monkeypatch.setattr(wp._gut, "search", lambda q, max_results=3: [])
    monkeypatch.setattr(wp._ia, "search", lambda q, max_results=5: [])
    assert wp.resolve_to_source(cit) is None
