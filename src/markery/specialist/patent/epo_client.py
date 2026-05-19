"""EPO Open Patent Services client.

Handles OAuth2 client-credentials auth with lazy token refresh, search,
biblio fetch, and drawing figure download. No DuckDB imports -- all DB
work lives in build.py and figures.py.

Rate limits: 0.5 s between requests; 503 retries with backoff [5, 15, 30] s.
EPO OPS docs: https://www.epo.org/searching-for-patents/data/web-services/ops.html
"""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any

import requests

RATE_SLEEP    = 0.5
RETRY_DELAYS  = [5, 15, 30]


# ---------------------------------------------------------------------------
# OPS JSON helpers
# ---------------------------------------------------------------------------

def _text(v: Any) -> str:
    """EPO OPS stores text in a '$' key; unwrap it."""
    if isinstance(v, dict):
        return v.get("$", "")
    return str(v) if v else ""


def _list(v: Any) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _first_date(doc_ids: Any) -> date | None:
    for d in _list(doc_ids):
        if isinstance(d, dict) and d.get("date"):
            raw = _text(d["date"]).replace("-", "")
            try:
                return datetime.strptime(raw[:8], "%Y%m%d").date()
            except ValueError:
                pass
    return None


def _epodoc_num(patent_no: str) -> str:
    """US1234567A → 1234567  (epodoc numeric-only format for image endpoint)."""
    n = patent_no.lstrip("US").lstrip("0")
    return n.rstrip("ABCDabcd") or "0"


def _parse_exchange_doc(doc: dict) -> dict | None:
    """Parse one exchange-document node into a flat patent dict."""
    if doc.get("@country", "") != "US":
        return None
    doc_number = doc.get("@doc-number", "")
    kind       = doc.get("@kind", "")
    if not doc_number:
        return None

    patent_no = f"US{doc_number}{kind}"
    bib       = doc.get("bibliographic-data", {})

    # Title (prefer English)
    title_raw = bib.get("invention-title")
    if isinstance(title_raw, list):
        en = next(
            (t for t in title_raw if isinstance(t, dict) and t.get("@lang") == "en"),
            title_raw[0],
        )
        title_raw = en
    title = _text(title_raw).strip().title() if title_raw else None

    # Dates
    pub_ref  = bib.get("publication-reference", {})
    app_ref  = bib.get("application-reference", {})
    grant_dt = _first_date(_list(pub_ref.get("document-id")))
    app_dt   = _first_date(_list(app_ref.get("document-id")))

    # Assignee (first epodoc-format applicant)
    assignee_name = None
    parties       = bib.get("parties", {})
    applicants    = _list(parties.get("applicants", {}).get("applicant"))
    for ap in applicants:
        if not isinstance(ap, dict):
            continue
        if ap.get("@data-format") == "epodoc":
            assignee_name = _text(ap.get("applicant-name", {}).get("name")).strip() or None
            break
    if not assignee_name and applicants:
        ap = applicants[0]
        if isinstance(ap, dict):
            assignee_name = _text(ap.get("applicant-name", {}).get("name")).strip() or None

    # Inventors
    inventors = []
    for inv in _list(parties.get("inventors", {}).get("inventor")):
        if isinstance(inv, dict) and inv.get("@data-format") == "epodoc":
            name = _text(inv.get("inventor-name", {}).get("name")).strip()
            if name:
                inventors.append(name)

    # CPC classifications
    cpc_symbols: list[str] = []
    for pc in _list(bib.get("patent-classifications", {}).get("patent-classification")):
        if not isinstance(pc, dict):
            continue
        scheme = pc.get("classification-scheme", {})
        if not (isinstance(scheme, dict) and scheme.get("@scheme", "").upper() in ("CPC", "CPCI")):
            continue
        symbol = "".join([
            _text(pc.get("section")),
            _text(pc.get("class")),
            _text(pc.get("subclass")),
            _text(pc.get("main-group")),
            "/",
            _text(pc.get("subgroup")),
        ]).rstrip("/")
        if symbol:
            cpc_symbols.append(symbol)

    return {
        "patent_no":     patent_no,
        "title":         title,
        "app_dt":        str(app_dt)   if app_dt   else None,
        "grant_dt":      str(grant_dt) if grant_dt else None,
        "abstract":      None,
        "assignee_name": assignee_name,
        "inventors":     inventors,
        "cpc":           cpc_symbols,
    }


# ---------------------------------------------------------------------------
# EPOClient
# ---------------------------------------------------------------------------

class EPOClient:
    """OAuth2 client for EPO Open Patent Services v3.2.

    Token refresh is lazy: every public method calls _ensure_token()
    before issuing a request. The token is refreshed if absent or expiring
    within 60 seconds. Callers never manage token state.
    """

    _AUTH_URL   = "https://ops.epo.org/3.2/auth/accesstoken"
    _SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"
    _IMAGE_URL  = "https://ops.epo.org/3.2/rest-services/published-data/images"

    def __init__(self, key: str, secret: str) -> None:
        self._key     = key
        self._secret  = secret
        self._token   = ""
        self._expiry  = 0.0          # unix timestamp
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"

    # ── Auth ─────────────────────────────────────────────────────────────────

    def _ensure_token(self) -> None:
        if self._token and time.time() < self._expiry:
            return
        import base64
        creds = base64.b64encode(f"{self._key}:{self._secret}".encode()).decode()
        r = self._session.post(
            self._AUTH_URL,
            headers={"Authorization": f"Basic {creds}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            data="grant_type=client_credentials",
            timeout=20,
        )
        r.raise_for_status()
        payload      = r.json()
        self._token  = payload["access_token"]
        self._expiry = time.time() + int(payload.get("expires_in", 1200)) - 60
        self._session.headers["Authorization"] = f"Bearer {self._token}"

    def _get(self, url: str, **kwargs) -> requests.Response:
        """GET with lazy token refresh, rate limiting, and 503 retry."""
        self._ensure_token()
        for attempt, delay in enumerate([0, *RETRY_DELAYS]):
            if delay:
                time.sleep(delay)
            r = self._session.get(url, timeout=30, **kwargs)
            if r.status_code == 401:
                self._expiry = 0  # force re-auth
                self._ensure_token()
                continue
            if r.status_code != 503:
                time.sleep(RATE_SLEEP)
                return r
            if attempt < len(RETRY_DELAYS):
                print(f"  EPO throttled, retrying in {RETRY_DELAYS[attempt]}s ...")
        time.sleep(RATE_SLEEP)
        return r

    # ── Public interface ──────────────────────────────────────────────────────

    def token_info(self) -> dict:
        """Return token expiry info; used by verify-credentials."""
        self._ensure_token()
        remaining = max(0, int(self._expiry - time.time()))
        return {"token_prefix": self._token[:12] + "...", "expires_in_s": remaining}

    def search(self, cql: str, range_start: int, range_end: int) -> tuple[int, list[dict]]:
        """Fetch one page of biblio results.

        Returns (total_results, list_of_patent_dicts). Returns (0, []) on 404.
        """
        r = self._get(
            self._SEARCH_URL,
            params={"q": cql},
            headers={"X-OPS-Range": f"{range_start}-{range_end}"},
        )
        if r.status_code == 404:
            return 0, []
        r.raise_for_status()

        data   = r.json()
        search = data.get("ops:world-patent-data", {}).get("ops:biblio-search", {})
        total  = int(search.get("@total-result-count", 0))

        patents: list[dict] = []
        docs_container = (
            search
            .get("ops:search-result", {})
            .get("exchange-documents", {})
        )
        for item in _list(docs_container):
            inner = item.get("exchange-document", item) if isinstance(item, dict) else item
            for doc in (_list(inner) if isinstance(inner, list) else [inner]):
                parsed = _parse_exchange_doc(doc)
                if parsed:
                    patents.append(parsed)
                    break

        return total, patents

    def fetch_biblio(self, patent_no: str) -> dict | None:
        """Fetch biblio for a single patent. Returns None if not found."""
        num = _epodoc_num(patent_no)
        url = f"https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/US{num}/biblio"
        r   = self._get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        docs = (
            r.json()
            .get("ops:world-patent-data", {})
            .get("exchange-documents", {})
            .get("exchange-document", {})
        )
        for doc in (_list(docs) if isinstance(docs, list) else [docs]):
            parsed = _parse_exchange_doc(doc)
            if parsed:
                return parsed
        return None

    def fetch_abstract(self, patent_no: str) -> str | None:
        """Fetch the English abstract for a patent. Returns None on 404 or if absent."""
        num = _epodoc_num(patent_no)
        url = f"https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/US{num}/abstract"
        r   = self._get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        try:
            docs = (
                r.json()
                .get("ops:world-patent-data", {})
                .get("exchange-documents", {})
                .get("exchange-document", {})
            )
            # exchange-document may be a list; take first
            if isinstance(docs, list):
                docs = docs[0]
            abstracts = _list(docs.get("abstract"))
            for ab in abstracts:
                if not isinstance(ab, dict):
                    continue
                if ab.get("@lang", "en") != "en":
                    continue
                paras = _list(ab.get("p"))
                parts = [_text(p) for p in paras if _text(p)]
                if parts:
                    return " ".join(parts)
        except Exception:
            pass
        return None

    def fetch_citations(self, patent_no: str) -> list[str]:
        """Return backward citation patent numbers (US only) for a patent.

        Fetches the citations endpoint and extracts patcit entries whose
        country is US. Non-patent literature citations (nplcit) are ignored.
        Returns [] on 404 or if no US patent citations are found.
        """
        num = _epodoc_num(patent_no)
        url = (
            f"https://ops.epo.org/3.2/rest-services/published-data/"
            f"publication/epodoc/US{num}/citations"
        )
        r = self._get(url)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        try:
            docs = (
                r.json()
                .get("ops:world-patent-data", {})
                .get("exchange-documents", {})
                .get("exchange-document", {})
            )
            if isinstance(docs, list):
                docs = docs[0]
            refs = docs.get("references-cited", {})
            citations = _list(refs.get("citation"))
            patent_nos: list[str] = []
            for cit in citations:
                if not isinstance(cit, dict):
                    continue
                patcit = cit.get("patcit")
                if not patcit:
                    continue
                for doc_id in _list(patcit.get("document-id")):
                    if not isinstance(doc_id, dict):
                        continue
                    country = _text(doc_id.get("country"))
                    if country != "US":
                        continue
                    doc_num = _text(doc_id.get("doc-number"))
                    kind    = _text(doc_id.get("kind"))
                    if doc_num:
                        patent_nos.append(f"US{doc_num}{kind}")
                        break
            return patent_nos
        except Exception:
            return []

    def fetch_figure(self, patent_no: str, page: int = 1) -> bytes | None:
        """Fetch page-1 drawing as TIFF bytes. Returns None on 404.

        The EPO images endpoint requires the numeric epodoc form of the
        US patent number (no 'US' prefix, no kind code, no leading zeros).
        See reference/patent-number-formats.md for the stripping rules.
        """
        num = _epodoc_num(patent_no)
        url = f"{self._IMAGE_URL}/US/{num}/A/FullImage"
        r   = self._get(url, headers={"Accept": "application/tiff", "Range": str(page)})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content
