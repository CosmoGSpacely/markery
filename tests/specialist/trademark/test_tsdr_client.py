"""Unit tests for TSDRClient using responses (HTTP mocking)."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest
import responses as rsps_lib

from markery.specialist.trademark.tsdr_client import TSDRClient, _parse_case_status

_BASE   = "https://tsdrapi.uspto.gov"
_IMG_URL   = f"{_BASE}/ts/cd/rawImage/71165547"
_STATUS_URL = f"{_BASE}/ts/cd/casestatus/sn71165547/info"

_CASE_STATUS_JSON = {
    "trademarkCaseFiles": [{
        "markVerbalElementText": "VI-DEX",
        "applicationDate":       "1927-01-15",
        "registrationNumber":    "0212345",
        "registrationDate":      "1928-03-10",
        "caseStatusCode":        "700",
        "goodsAndServicesClassification": [{
            "internationalClassNumber":    "16",
            "goodsAndServicesDescription": "Card filing systems",
        }],
        "firstUseAnywhere":   "1926-01-01",
        "firstUseInCommerce": "1926-06-01",
    }]
}


# ---------------------------------------------------------------------------
# _parse_case_status
# ---------------------------------------------------------------------------

def test_parse_case_status_extracts_fields():
    result = _parse_case_status(_CASE_STATUS_JSON, "71165547")
    assert result["serial_no"]       == "71165547"
    assert result["mark_text"]       == "VI-DEX"
    assert result["filing_dt"]       == "1927-01-15"
    assert result["registration_no"] == "0212345"
    assert result["status_cd"]       == "700"
    assert result["intl_class"]      == "16"
    assert result["goods_desc"]      == "Card filing systems"
    assert result["first_use_dt"]    == "1926-01-01"


def test_parse_case_status_missing_goods_classification():
    data = {"trademarkCaseFiles": [{"markVerbalElementText": "SOUNDEX"}]}
    result = _parse_case_status(data, "71000001")
    assert result["mark_text"] == "SOUNDEX"
    assert result["intl_class"] is None
    assert result["goods_desc"] is None


# ---------------------------------------------------------------------------
# TSDRClient.fetch_mark_image
# ---------------------------------------------------------------------------

@rsps_lib.activate
def test_fetch_mark_image_returns_bytes():
    rsps_lib.add(rsps_lib.GET, _IMG_URL, body=b"\x89PNG\r\n", content_type="image/png")
    client = TSDRClient("test-api-key")
    result = client.fetch_mark_image("71165547")
    assert result == b"\x89PNG\r\n"


@rsps_lib.activate
def test_fetch_mark_image_returns_none_on_404():
    rsps_lib.add(rsps_lib.GET, _IMG_URL, status=404)
    client = TSDRClient("test-api-key")
    result = client.fetch_mark_image("71165547")
    assert result is None


@rsps_lib.activate
def test_fetch_mark_image_sets_api_key_header():
    rsps_lib.add(rsps_lib.GET, _IMG_URL, body=b"\x89PNG\r\n", content_type="image/png")
    client = TSDRClient("my-secret-key")
    client.fetch_mark_image("71165547")
    sent_key = rsps_lib.calls[0].request.headers.get("USPTO-API-KEY")
    assert sent_key == "my-secret-key"


# ---------------------------------------------------------------------------
# TSDRClient.fetch_case_status
# ---------------------------------------------------------------------------

@rsps_lib.activate
def test_fetch_case_status_returns_parsed_dict():
    rsps_lib.add(rsps_lib.GET, _STATUS_URL, json=_CASE_STATUS_JSON)
    client = TSDRClient("test-api-key")
    result = client.fetch_case_status("71165547")
    assert result is not None
    assert result["mark_text"] == "VI-DEX"
    assert result["filing_dt"] == "1927-01-15"


@rsps_lib.activate
def test_fetch_case_status_returns_none_on_404():
    rsps_lib.add(rsps_lib.GET, _STATUS_URL, status=404)
    client = TSDRClient("test-api-key")
    result = client.fetch_case_status("71165547")
    assert result is None


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

@rsps_lib.activate
def test_rate_sleep_applied_after_request():
    rsps_lib.add(rsps_lib.GET, _IMG_URL, body=b"\x89PNG\r\n", content_type="image/png")
    client = TSDRClient("test-api-key")
    with patch("markery.specialist.trademark.tsdr_client.time.sleep") as mock_sleep:
        client.fetch_mark_image("71165547")
    # RATE_SLEEP (1.0) must be called; delay=0 for first attempt so only one call
    sleep_args = [call.args[0] for call in mock_sleep.call_args_list]
    assert any(s >= 1.0 for s in sleep_args)


# ---------------------------------------------------------------------------
# verify_credentials
# ---------------------------------------------------------------------------

@rsps_lib.activate
def test_verify_credentials_ok():
    verify_url = f"{_BASE}/ts/cd/casestatus/sn71165547/info"
    rsps_lib.add(rsps_lib.GET, verify_url, json=_CASE_STATUS_JSON)
    client = TSDRClient("abcdefgh-key")
    info   = client.verify_credentials()
    assert info["api_key_prefix"] == "abcdefgh..."
    assert info["status_code"]    == 200
