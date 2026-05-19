"""USPTO TSDR API client.

Handles mark image and case status retrieval with rate limiting and retry.
No OAuth2 — USPTO uses a static API key header.

Rate limits: 1.0 s between requests (60 req/min); 429/503 retries [5, 15, 30] s.
TSDR docs: https://tsdrapi.uspto.gov/ts/cd/docs
"""

from __future__ import annotations

import time

import requests

RATE_SLEEP    = 1.0
RETRY_DELAYS  = [5, 15, 30]

_BASE_URL = "https://tsdrapi.uspto.gov"


class TSDRClient:
    """USPTO TSDR REST API client.

    Authentication is a static API key sent as a request header on every call.
    No token refresh cycle — key is valid until revoked.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({
            "USPTO-API-KEY": api_key,
            "Accept":        "application/json",
        })

    # ── Internal ──────────────────────────────────────────────────────────────

    def _get(self, url: str, **kwargs) -> requests.Response:
        """GET with rate limiting and 429/503 retry."""
        for attempt, delay in enumerate([0, *RETRY_DELAYS]):
            if delay:
                time.sleep(delay)
            r = self._session.get(url, timeout=30, **kwargs)
            if r.status_code not in (429, 503):
                time.sleep(RATE_SLEEP)
                return r
            if attempt < len(RETRY_DELAYS):
                print(f"  TSDR throttled ({r.status_code}), retrying in {RETRY_DELAYS[attempt]}s ...")
        time.sleep(RATE_SLEEP)
        return r

    # ── Public interface ───────────────────────────────────────────────────────

    def fetch_mark_image(self, serial_no: str) -> bytes | None:
        """Fetch the PNG mark image for a serial number. Returns None on 404."""
        url = f"{_BASE_URL}/ts/cd/rawImage/{serial_no}"
        r   = self._get(url, headers={"Accept": "image/png"})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content

    def fetch_case_status(self, serial_no: str) -> dict | None:
        """Fetch case status for a serial number. Returns parsed flat dict or None on 404.

        The returned dict includes raw_json (the full response body as a JSON string)
        for auditability and future re-parsing without re-fetching.
        """
        import json as _json
        url = f"{_BASE_URL}/ts/cd/casestatus/sn{serial_no}/info"
        r   = self._get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data   = r.json()
        parsed = _parse_case_status(data, serial_no)
        parsed["raw_json"] = _json.dumps(data)
        return parsed

    def verify_credentials(self) -> dict:
        """Make a cheap live request to confirm the API key is accepted.

        Uses a known-registered serial number (71165547 = VI-DEX, Wilson Jones).
        Returns {"api_key_prefix": "...", "status_code": 200} or raises on auth failure.
        """
        url = f"{_BASE_URL}/ts/cd/casestatus/sn71165547/info"
        r   = self._get(url)
        r.raise_for_status()
        return {
            "api_key_prefix": self._api_key[:8] + "...",
            "status_code":    r.status_code,
        }


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_case_status(data: dict, serial_no: str) -> dict:
    """Extract flat fields from TSDR case status JSON."""
    record = (
        data.get("trademarkCaseFiles", [{}])[0]
        if isinstance(data.get("trademarkCaseFiles"), list)
        else data
    )

    def _get(key: str) -> str | None:
        v = record.get(key)
        return str(v).strip() if v is not None else None

    # Goods and services classification is a list; take the first element
    gsc = record.get("goodsAndServicesClassification")
    if isinstance(gsc, list) and gsc and isinstance(gsc[0], dict):
        goods_desc = str(gsc[0]["goodsAndServicesDescription"]).strip() \
                     if gsc[0].get("goodsAndServicesDescription") else None
        intl_class = str(gsc[0]["internationalClassNumber"]).strip() \
                     if gsc[0].get("internationalClassNumber") else None
    else:
        goods_desc = _get("goodsAndServicesDescription")
        intl_class = None

    return {
        "serial_no":          serial_no,
        "mark_text":          _get("markVerbalElementText"),
        "filing_dt":          _get("applicationDate"),
        "registration_no":    _get("registrationNumber"),
        "registration_dt":    _get("registrationDate"),
        "status_cd":          _get("caseStatusCode"),
        "goods_desc":         goods_desc,
        "intl_class":         intl_class,
        "owner_name":         _get("registrantName") or _get("applicantName"),
        "first_use_dt":       _get("firstUseAnywhere"),
        "first_use_comm_dt":  _get("firstUseInCommerce"),
        "raw_json":           None,  # populated by caller with json.dumps(data)
    }
