"""USPTO Open Data Portal (ODP) trademark text search.

`markery trademark search-tsdr <mark-text>` resolves a brand name to serial
numbers — the lookup the serial-keyed TSDR API cannot do (D028).

Why a separate client from `tsdr_client.py`:
  - Different host: ``api.uspto.gov`` (ODP), not ``tsdrapi.uspto.gov`` (TSDR).
  - Different key: an ID.me-linked ODP key passed as ``X-API-KEY`` (see
    ``common.auth.load_odp_key``), not the static ``USPTO-API-KEY`` TSDR key.

Endpoint caveat
---------------
The ODP is mid-migration and its docs are JS-rendered (not machine-readable),
so the exact search route/shape below is **provisional and must be verified
against the live ODP once a key is available** — `_SEARCH_PATH` and the response
parsing are the single places to adjust. Parsing is deliberately defensive
(accepts snake_case and camelCase field names) to survive shape differences.
When the API is unreachable or unauthenticated, callers get
``ODPSearchUnavailable`` so the CLI can fall back to the documented manual path.
"""

from __future__ import annotations

import requests

_ODP_BASE = "https://api.uspto.gov"
# Provisional — confirm against the live ODP swagger once an ODP key is in hand.
_SEARCH_PATH = "/api/v1/trademarks/search"


class ODPSearchUnavailable(RuntimeError):
    """The ODP search API could not be reached, authenticated, or understood."""


def _pick(record: dict, *keys: str) -> str | None:
    """Return the first present, non-empty value among `keys` (snake/camel tolerant)."""
    for k in keys:
        v = record.get(k)
        if v not in (None, ""):
            return str(v).strip()
    return None


def _extract_results(data) -> list[dict]:
    """Find the list of mark records in an ODP response of unknown exact shape."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("results", "trademarks", "hits", "data", "items", "marks"):
            v = data.get(key)
            if isinstance(v, dict) and isinstance(v.get("hits"), list):
                return v["hits"]          # OpenSearch-style {hits: {hits: [...]}}
            if isinstance(v, list):
                return v
    return []


def _normalise(record: dict) -> dict:
    """Flatten one ODP mark record into Markery's fields (defensive key matching)."""
    src = record.get("_source") if isinstance(record.get("_source"), dict) else record
    return {
        "serial_no":       _pick(src, "serial_number", "serialNumber", "serial"),
        "mark_text":       _pick(src, "wordmark", "markText", "markElement", "mark_literal_elements"),
        "owner_name":      _pick(src, "owner_name", "ownerName", "owner", "registrant"),
        "filing_dt":       _pick(src, "filed_date", "filingDate", "filing_dt", "applicationDate"),
        "registration_no": _pick(src, "registration_id", "usRegistrationNumber", "registrationNumber"),
        "status":          _pick(src, "status", "status_label", "caseStatus"),
    }


def search_marks(
    query: str,
    api_key: str,
    *,
    base_url: str = _ODP_BASE,
    active_only: bool = False,
    limit: int = 20,
    session: requests.Session | None = None,
) -> list[dict]:
    """Search USPTO trademarks by mark text via the ODP.

    Returns a list of dicts with keys serial_no, mark_text, owner_name,
    filing_dt, registration_no, status (most-relevant first, capped at `limit`).
    Raises ODPSearchUnavailable on auth failure (401/403) or any non-200/parse
    failure so the CLI can show the manual fallback.
    """
    sess = session or requests.Session()
    params = {"q": query, "rows": limit}
    if active_only:
        params["status"] = "active"
    try:
        resp = sess.get(
            f"{base_url}{_SEARCH_PATH}",
            params=params,
            headers={"X-API-KEY": api_key, "Accept": "application/json"},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ODPSearchUnavailable(f"could not reach the ODP search API: {exc}") from exc

    if resp.status_code in (401, 403):
        raise ODPSearchUnavailable(
            f"ODP rejected the API key ({resp.status_code}). Confirm USPTO_ODP_API_KEY "
            "is an ID.me-linked Open Data Portal key, not the TSDR key."
        )
    if resp.status_code != 200:
        raise ODPSearchUnavailable(
            f"ODP search returned HTTP {resp.status_code}: {resp.text[:200]}"
        )
    try:
        data = resp.json()
    except ValueError as exc:
        raise ODPSearchUnavailable(f"ODP response was not JSON: {resp.text[:120]}") from exc

    results = [_normalise(r) for r in _extract_results(data)]
    return [r for r in results if r["serial_no"]][:limit]
