"""Unit tests for EPOClient using responses (HTTP mocking)."""

from __future__ import annotations

import json
import time

import pytest
import responses as rsps_lib
from responses import RequestsMock

from markery.specialist.patent.epo_client import EPOClient, _epodoc_num, _parse_exchange_doc


# ---------------------------------------------------------------------------
# _epodoc_num
# ---------------------------------------------------------------------------

def test_epodoc_num_strips_prefix_and_kind():
    assert _epodoc_num("US1261167A") == "1261167"


def test_epodoc_num_strips_leading_zeros():
    # rstrip only removes single trailing chars from ABCDabcd; kind codes must be single-char
    assert _epodoc_num("US0012345A") == "12345"


def test_epodoc_num_no_kind_code():
    assert _epodoc_num("US9999999") == "9999999"


# ---------------------------------------------------------------------------
# _parse_exchange_doc
# ---------------------------------------------------------------------------

def _make_doc(doc_number="1261167", kind="A", country="US") -> dict:
    return {
        "@country":    country,
        "@doc-number": doc_number,
        "@kind":       kind,
        "bibliographic-data": {
            "invention-title": {"$": "Index", "@lang": "en"},
            "publication-reference": {
                "document-id": [{"date": {"$": "19180402"}}]
            },
            "application-reference": {
                "document-id": [{"date": {"$": "19171025"}}]
            },
            "parties": {
                "applicants": {
                    "applicant": [{
                        "@data-format": "epodoc",
                        "applicant-name": {"name": {"$": "REMINGTON TYPEWRITER CO"}},
                    }]
                },
                "inventors": {
                    "inventor": [{
                        "@data-format": "epodoc",
                        "inventor-name": {"name": {"$": "Russell Robert C"}},
                    }]
                },
            },
            "patent-classifications": {
                "patent-classification": [{
                    "classification-scheme": {"@scheme": "CPC"},
                    "section": {"$": "B"},
                    "class": {"$": "42"},
                    "subclass": {"$": "F"},
                    "main-group": {"$": "17"},
                    "subgroup": {"$": "00"},
                }]
            },
        },
    }


def test_parse_exchange_doc_happy_path():
    doc = _make_doc()
    result = _parse_exchange_doc(doc)
    assert result is not None
    assert result["patent_no"] == "US1261167A"
    assert result["title"] == "Index"
    assert result["grant_dt"] == "1918-04-02"
    assert result["app_dt"] == "1917-10-25"
    assert result["assignee_name"] == "REMINGTON TYPEWRITER CO"
    assert "Russell Robert C" in result["inventors"]
    assert "B42F17/00" in result["cpc"]


def test_parse_exchange_doc_skips_non_us():
    doc = _make_doc(country="DE")
    assert _parse_exchange_doc(doc) is None


def test_parse_exchange_doc_missing_doc_number():
    doc = _make_doc()
    doc["@doc-number"] = ""
    assert _parse_exchange_doc(doc) is None


# ---------------------------------------------------------------------------
# EPOClient — token refresh
# ---------------------------------------------------------------------------

TOKEN_RESP = {
    "access_token": "tok_abc123xyz",
    "expires_in":   1200,
    "token_type":   "Bearer",
}

AUTH_URL   = "https://ops.epo.org/3.2/auth/accesstoken"
SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"
IMAGE_URL  = "https://ops.epo.org/3.2/rest-services/published-data/images"


@rsps_lib.activate
def test_token_fetched_on_first_call():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(rsps_lib.GET, SEARCH_URL, json={"ops:world-patent-data": {"ops:biblio-search": {"@total-result-count": "0"}}})

    client = EPOClient("key", "secret")
    total, patents = client.search("cpc=B42F", 1, 25)
    assert total == 0
    assert client._token == "tok_abc123xyz"


@rsps_lib.activate
def test_token_refreshed_when_expired():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json={**TOKEN_RESP, "access_token": "tok_refreshed"})
    rsps_lib.add(rsps_lib.GET, SEARCH_URL, json={"ops:world-patent-data": {"ops:biblio-search": {"@total-result-count": "0"}}})

    client = EPOClient("key", "secret")
    client._ensure_token()                # consume first mock → tok_abc123xyz
    assert client._token == "tok_abc123xyz"
    client._expiry = time.time() - 1      # force expiry

    client.search("cpc=B42F", 1, 25)     # triggers refresh → tok_refreshed
    assert client._token == "tok_refreshed"


# ---------------------------------------------------------------------------
# EPOClient.fetch_figure
# ---------------------------------------------------------------------------

@rsps_lib.activate
def test_fetch_figure_returns_bytes():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(
        rsps_lib.GET,
        f"{IMAGE_URL}/US/1261167/A/FullImage",
        body=b"TIFF_BYTES",
        content_type="image/tiff",
    )

    client = EPOClient("key", "secret")
    result = client.fetch_figure("US1261167A", page=1)
    assert result == b"TIFF_BYTES"


@rsps_lib.activate
def test_fetch_figure_returns_none_on_404():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    rsps_lib.add(
        rsps_lib.GET,
        f"{IMAGE_URL}/US/9999999/A/FullImage",
        status=404,
    )

    client = EPOClient("key", "secret")
    result = client.fetch_figure("US9999999A", page=1)
    assert result is None


# ---------------------------------------------------------------------------
# EPOClient.token_info
# ---------------------------------------------------------------------------

@rsps_lib.activate
def test_token_info_returns_prefix_and_expiry():
    rsps_lib.add(rsps_lib.POST, AUTH_URL, json=TOKEN_RESP)
    client = EPOClient("key", "secret")
    info = client.token_info()
    assert info["token_prefix"].startswith("tok_abc123xy")
    assert info["expires_in_s"] > 0
