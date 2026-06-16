"""Tests for ODP trademark text search (D028) — mocked, no live API."""

from __future__ import annotations

import argparse
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from markery.specialist.trademark.odp_search import (
    search_marks, ODPSearchUnavailable, _normalise, _extract_results,
)


class _FakeResp:
    def __init__(self, status, payload=None, text=""):
        self.status_code = status
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class _FakeSession:
    def __init__(self, resp):
        self._resp = resp
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, params, headers))
        return self._resp


# ── parsing ─────────────────────────────────────────────────────────────────

class TestParsing:
    def test_normalise_snake_case(self):
        r = _normalise({"serial_number": "71234567", "wordmark": "KODACHROME",
                        "owner_name": "EASTMAN KODAK CO", "filed_date": "1935-04-01",
                        "registration_id": "0327821", "status": "Registered"})
        assert r["serial_no"] == "71234567"
        assert r["mark_text"] == "KODACHROME"
        assert r["owner_name"] == "EASTMAN KODAK CO"
        assert r["filing_dt"] == "1935-04-01"

    def test_normalise_camel_case(self):
        r = _normalise({"serialNumber": "71000001", "markText": "BROWNIE",
                        "ownerName": "EASTMAN KODAK COMPANY", "filingDate": "1901-02-01"})
        assert r["serial_no"] == "71000001" and r["mark_text"] == "BROWNIE"

    def test_extract_results_variants(self):
        assert _extract_results({"results": [{"a": 1}]}) == [{"a": 1}]
        assert _extract_results([{"a": 1}]) == [{"a": 1}]
        assert _extract_results({"hits": {"hits": [{"_source": {"x": 1}}]}}) == [{"_source": {"x": 1}}]
        assert _extract_results({"nope": 1}) == []

    def test_opensearch_source_unwrapped(self):
        r = _normalise({"_source": {"serial_number": "71999999", "wordmark": "VERICHROME"}})
        assert r["serial_no"] == "71999999" and r["mark_text"] == "VERICHROME"


# ── search_marks behaviour ────────────────────────────────────────────────────

class TestSearchMarks:
    def test_success_filters_and_caps(self):
        payload = {"results": [
            {"serial_number": "71000001", "wordmark": "KODAK"},
            {"serial_number": "", "wordmark": "NO SERIAL"},   # dropped (no serial)
            {"serial_number": "71000002", "wordmark": "KODACOLOR"},
        ]}
        sess = _FakeSession(_FakeResp(200, payload))
        out = search_marks("KODAK", "odp-key", session=sess, limit=20)
        assert [r["serial_no"] for r in out] == ["71000001", "71000002"]
        # header + query carried
        _url, params, headers = sess.calls[0]
        assert params["q"] == "KODAK"
        assert headers["X-API-KEY"] == "odp-key"

    def test_limit_caps_results(self):
        payload = {"results": [{"serial_number": f"710000{i:02d}"} for i in range(10)]}
        out = search_marks("X", "k", session=_FakeSession(_FakeResp(200, payload)), limit=3)
        assert len(out) == 3

    def test_active_only_param(self):
        sess = _FakeSession(_FakeResp(200, {"results": []}))
        search_marks("X", "k", session=sess, active_only=True)
        assert sess.calls[0][1]["status"] == "active"

    def test_auth_failure_raises_unavailable(self):
        for code in (401, 403):
            with pytest.raises(ODPSearchUnavailable, match="key"):
                search_marks("X", "k", session=_FakeSession(_FakeResp(code, text="denied")))

    def test_non_200_raises_unavailable(self):
        with pytest.raises(ODPSearchUnavailable, match="500"):
            search_marks("X", "k", session=_FakeSession(_FakeResp(500, text="boom")))

    def test_non_json_raises_unavailable(self):
        with pytest.raises(ODPSearchUnavailable, match="not JSON"):
            search_marks("X", "k", session=_FakeSession(_FakeResp(200, payload=None, text="<html>")))


# ── CLI graceful fallback ─────────────────────────────────────────────────────

class TestCmdSearchTsdr:
    def test_missing_key_exits_1_with_fallback(self, capsys):
        from markery.specialist.trademark.cli import cmd_search_tsdr
        args = argparse.Namespace(mark_text="KODAK", active_only=False, limit=20)
        with patch("markery.common.auth.load_odp_key",
                   side_effect=EnvironmentError("USPTO_ODP_API_KEY not set in .env")):
            with pytest.raises(SystemExit) as exc:
                cmd_search_tsdr(args)
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "manual fallback" in err.lower()
        assert "markery trademark fetch" in err

    def test_api_unavailable_exits_1(self, capsys):
        from markery.specialist.trademark.cli import cmd_search_tsdr
        args = argparse.Namespace(mark_text="KODAK", active_only=False, limit=20)
        with (
            patch("markery.common.auth.load_odp_key", return_value="k"),
            patch("markery.specialist.trademark.odp_search.search_marks",
                  side_effect=ODPSearchUnavailable("ODP rejected the API key (403).")),
        ):
            with pytest.raises(SystemExit) as exc:
                cmd_search_tsdr(args)
        assert exc.value.code == 1

    def test_success_prints_table(self, capsys):
        from markery.specialist.trademark.cli import cmd_search_tsdr
        args = argparse.Namespace(mark_text="KODACHROME", active_only=False, limit=20)
        rows = [{"serial_no": "71234567", "mark_text": "KODACHROME",
                 "owner_name": "EASTMAN KODAK CO", "filing_dt": "1935-04-01",
                 "registration_no": "0327821", "status": "Registered"}]
        with (
            patch("markery.common.auth.load_odp_key", return_value="k"),
            patch("markery.specialist.trademark.odp_search.search_marks", return_value=rows),
        ):
            cmd_search_tsdr(args)
        out = capsys.readouterr().out
        assert "TSDR SEARCH: KODACHROME" in out
        assert "71234567" in out and "KODACHROME" in out
