"""Tests for Phase 6D: patent/fetch.py and EPOClient.fetch_abstract/fetch_citations."""

from __future__ import annotations

import json

import duckdb
import pytest
import responses as rsps_lib

from markery.specialist.patent.epo_client import EPOClient
from markery.specialist.patent.fetch import (
    upsert_patent,
    fetch_patent_record,
    fetch_citation_chain,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
TOKEN_RESP = {"access_token": "tok_test", "expires_in": 1200}

_DDL = """
CREATE TABLE IF NOT EXISTS patents (
    patent_no      VARCHAR PRIMARY KEY,
    title          VARCHAR,
    app_dt         DATE,
    grant_dt       DATE,
    abstract       VARCHAR,
    assignee_name  VARCHAR,
    assignee_city  VARCHAR,
    assignee_state VARCHAR
);
CREATE TABLE IF NOT EXISTS patent_classes (
    patent_no VARCHAR NOT NULL,
    cpc_class VARCHAR,
    cpc_full  VARCHAR
);
CREATE TABLE IF NOT EXISTS patent_inventors (
    patent_no     VARCHAR NOT NULL,
    inventor_name VARCHAR
);
"""


def _mem_db() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:")
    conn.execute(_DDL)
    return conn


def _record(**kwargs) -> dict:
    base = {
        "patent_no":     "US1261167A",
        "title":         "Index",
        "app_dt":        "1917-10-25",
        "grant_dt":      "1918-04-02",
        "abstract":      "A phonetic indexing system.",
        "assignee_name": "Remington Typewriter Co",
        "cpc":           ["B42F17/00"],
        "inventors":     ["Russell Robert C"],
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# upsert_patent
# ---------------------------------------------------------------------------

def test_upsert_patent_inserts_new_record():
    conn = _mem_db()
    upsert_patent(conn, _record())
    row = conn.execute("SELECT patent_no, abstract FROM patents").fetchone()
    assert row[0] == "US1261167A"
    assert row[1] == "A phonetic indexing system."


def test_upsert_patent_inserts_cpc_and_inventors():
    conn = _mem_db()
    upsert_patent(conn, _record())
    cpc = conn.execute("SELECT cpc_class FROM patent_classes").fetchone()
    inv = conn.execute("SELECT inventor_name FROM patent_inventors").fetchone()
    assert cpc[0] == "B42F"
    assert inv[0] == "Russell Robert C"


def test_upsert_patent_updates_existing_abstract():
    conn = _mem_db()
    upsert_patent(conn, _record(abstract="Original."))
    upsert_patent(conn, _record(abstract="Updated."))
    row = conn.execute("SELECT abstract FROM patents WHERE patent_no = 'US1261167A'").fetchone()
    assert row[0] == "Updated."
    # Only one row
    n = conn.execute("SELECT count(*) FROM patents").fetchone()[0]
    assert n == 1


def test_upsert_patent_replaces_cpc_on_update():
    conn = _mem_db()
    upsert_patent(conn, _record(cpc=["B42F17/00"]))
    upsert_patent(conn, _record(cpc=["B42D99/00", "G09F3/00"]))
    rows = conn.execute("SELECT cpc_class FROM patent_classes ORDER BY cpc_class").fetchall()
    classes = [r[0] for r in rows]
    assert "B42D" in classes
    assert "G09F" in classes
    assert "B42F" not in classes


def test_upsert_patent_no_cpc_inserts_null_row():
    conn = _mem_db()
    upsert_patent(conn, _record(cpc=[]))
    row = conn.execute("SELECT cpc_class FROM patent_classes").fetchone()
    assert row[0] is None


# ---------------------------------------------------------------------------
# fetch_patent_record
# ---------------------------------------------------------------------------

def test_fetch_patent_record_returns_false_when_not_found():
    class _Client:
        def fetch_biblio(self, _): return None
        def fetch_abstract(self, _): return None

    conn = _mem_db()
    result = fetch_patent_record("US9999999A", _Client(), conn)
    assert result is False
    assert conn.execute("SELECT count(*) FROM patents").fetchone()[0] == 0


def test_fetch_patent_record_upserts_and_returns_true():
    rec = _record(abstract=None)

    class _Client:
        def fetch_biblio(self, _): return dict(rec)
        def fetch_abstract(self, _): return "Fetched abstract."

    conn = _mem_db()
    result = fetch_patent_record("US1261167A", _Client(), conn)
    assert result is True
    row = conn.execute("SELECT abstract FROM patents WHERE patent_no = 'US1261167A'").fetchone()
    assert row[0] == "Fetched abstract."


def test_fetch_patent_record_does_not_call_abstract_when_biblio_has_it():
    abstract_calls: list[str] = []

    class _Client:
        def fetch_biblio(self, _): return _record(abstract="Already present.")
        def fetch_abstract(self, pno):
            abstract_calls.append(pno)
            return "Should not be called."

    conn = _mem_db()
    fetch_patent_record("US1261167A", _Client(), conn)
    assert abstract_calls == []


# ---------------------------------------------------------------------------
# fetch_citation_chain
# ---------------------------------------------------------------------------

def test_fetch_citation_chain_returns_zero_when_no_citations():
    class _Client:
        def fetch_citations(self, _): return []
        def fetch_biblio(self, _): return None
        def fetch_abstract(self, _): return None

    conn = _mem_db()
    assert fetch_citation_chain("US1261167A", _Client(), conn) == 0


def test_fetch_citation_chain_skips_patents_already_in_db():
    conn = _mem_db()
    upsert_patent(conn, _record(patent_no="US1111111A"))
    fetched: list[str] = []

    class _Client:
        def fetch_citations(self, _): return ["US1111111A"]
        def fetch_biblio(self, pno):
            fetched.append(pno)
            return _record(patent_no=pno)
        def fetch_abstract(self, _): return None

    n = fetch_citation_chain("US1261167A", _Client(), conn)
    assert n == 0
    assert fetched == []


def test_fetch_citation_chain_fetches_new_cited_patents():
    conn = _mem_db()

    class _Client:
        def fetch_citations(self, _): return ["US9000001A", "US9000002A"]
        def fetch_biblio(self, pno): return _record(patent_no=pno, abstract="cited")
        def fetch_abstract(self, _): return None

    n = fetch_citation_chain("US1261167A", _Client(), conn)
    assert n == 2
    count = conn.execute("SELECT count(*) FROM patents").fetchone()[0]
    assert count == 2


def test_fetch_citation_chain_counts_only_found_patents():
    conn = _mem_db()

    class _Client:
        def fetch_citations(self, _): return ["US9000001A", "US9000002A"]
        def fetch_biblio(self, pno):
            # Only US9000001A exists on EPO
            return _record(patent_no=pno) if pno == "US9000001A" else None
        def fetch_abstract(self, _): return None

    n = fetch_citation_chain("US1261167A", _Client(), conn)
    assert n == 1


# ---------------------------------------------------------------------------
# EPOClient.fetch_abstract (HTTP mock)
# ---------------------------------------------------------------------------

_ABSTRACT_URL = "https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/US1261167/abstract"


@rsps_lib.activate
def test_epo_fetch_abstract_returns_text():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(rsps_lib.GET, _ABSTRACT_URL, json={
        "ops:world-patent-data": {
            "exchange-documents": {
                "exchange-document": {
                    "abstract": [
                        {"@lang": "en", "p": {"$": "A phonetic indexing method."}}
                    ]
                }
            }
        }
    })
    client = EPOClient("k", "s")
    result = client.fetch_abstract("US1261167A")
    assert result == "A phonetic indexing method."


@rsps_lib.activate
def test_epo_fetch_abstract_returns_none_on_404():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(rsps_lib.GET, _ABSTRACT_URL, status=404)
    client = EPOClient("k", "s")
    assert client.fetch_abstract("US1261167A") is None


@rsps_lib.activate
def test_epo_fetch_abstract_concatenates_multiple_paragraphs():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(rsps_lib.GET, _ABSTRACT_URL, json={
        "ops:world-patent-data": {
            "exchange-documents": {
                "exchange-document": {
                    "abstract": [
                        {"@lang": "en", "p": [{"$": "Para one."}, {"$": "Para two."}]}
                    ]
                }
            }
        }
    })
    client = EPOClient("k", "s")
    result = client.fetch_abstract("US1261167A")
    assert "Para one." in result
    assert "Para two." in result


# ---------------------------------------------------------------------------
# EPOClient.fetch_citations (HTTP mock)
# ---------------------------------------------------------------------------

_CITATIONS_URL = "https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/US1261167/citations"


def _citation_response(us_numbers: list[str], include_npl: bool = False) -> dict:
    citations = []
    for i, pno in enumerate(us_numbers):
        num  = pno.lstrip("US").rstrip("ABCDabcd")
        kind = "A"
        citations.append({
            "@sequence": str(i + 1),
            "patcit": {
                "document-id": [{
                    "@document-id-type": "docdb",
                    "country": {"$": "US"},
                    "doc-number": {"$": num},
                    "kind": {"$": kind},
                }]
            },
        })
    if include_npl:
        citations.append({"@sequence": "99", "nplcit": {"text": {"$": "Some article."}}})
    return {
        "ops:world-patent-data": {
            "exchange-documents": {
                "exchange-document": {
                    "references-cited": {"citation": citations}
                }
            }
        }
    }


@rsps_lib.activate
def test_epo_fetch_citations_returns_us_patent_list():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(rsps_lib.GET, _CITATIONS_URL,
                 json=_citation_response(["US1100001A", "US1100002A"]))
    client = EPOClient("k", "s")
    result = client.fetch_citations("US1261167A")
    assert "US1100001A" in result
    assert "US1100002A" in result


@rsps_lib.activate
def test_epo_fetch_citations_returns_empty_on_404():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(rsps_lib.GET, _CITATIONS_URL, status=404)
    client = EPOClient("k", "s")
    assert client.fetch_citations("US1261167A") == []


@rsps_lib.activate
def test_epo_fetch_citations_ignores_nplcit():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(rsps_lib.GET, _CITATIONS_URL,
                 json=_citation_response(["US1100001A"], include_npl=True))
    client = EPOClient("k", "s")
    result = client.fetch_citations("US1261167A")
    assert len(result) == 1
    assert result[0] == "US1100001A"
