"""Chronicling America (Library of Congress) newspaper source adapter (Phase 30 P2).

Chronicling America serves digitized historic US newspaper pages with a JSON API.
Pages are admitted as public domain and **date-capped** to the rolling US PD
cutoff (this year − 95) so nothing in-copyright is acquired. Each acquired page is
a `clipping` media item whose attribution carries a full newspaper citation.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date
from typing import Optional

from .common import MediaResult, download as _download

_BASE = "https://chroniclingamerica.loc.gov"
_UA = "markery/1.0 (https://github.com/CosmoGSpacely/markery)"


def pd_cutoff_year() -> int:
    """Rolling US public-domain cutoff (works published this year − 95 are PD)."""
    return date.today().year - 95


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def search(query: str, max_results: int = 10,
           year_start: int | None = None, year_end: int | None = None) -> list[str]:
    """Return page ids (``/lccn/<lccn>/<date>/ed-N/seq-N/``) matching the query."""
    params = {"andtext": query, "format": "json", "rows": max_results}
    if year_start or year_end:
        params["dateFilterType"] = "yearRange"
        params["date1"] = str(year_start or 1789)
        params["date2"] = str(year_end or pd_cutoff_year())
    url = f"{_BASE}/search/pages/results/?{urllib.parse.urlencode(params)}"
    data = _get(url)
    return [item["id"] for item in data.get("items", [])[:max_results] if item.get("id")]


def fetch(page_id: str, max_year: int | None = None,
          fair_use: bool = False) -> Optional[MediaResult]:
    """Resolve one page to a clipping MediaResult. None if out of PD range
    (strict); under fair_use, post-cutoff pages are tagged InC and acquired.
    A page with no resolvable date is always skipped (no citation possible)."""
    detail = _get(f"{_BASE}{page_id.rstrip('/')}.json")
    issue = detail.get("issue", {}) or {}
    date_issued = issue.get("date_issued", "") or detail.get("date", "")
    year = int(date_issued[:4]) if date_issued[:4].isdigit() else None
    cutoff = max_year if max_year is not None else pd_cutoff_year()
    if year is None:
        return None  # unknown date → cannot cite
    in_copyright = year > cutoff
    if in_copyright and not fair_use:
        return None

    title_obj = detail.get("title", {}) or {}
    paper = title_obj.get("name", "") if isinstance(title_obj, dict) else str(title_obj)
    seq = detail.get("sequence", "")
    image_url = f"{_BASE}{page_id.rstrip('/')}.jpg"
    citation = (f"{paper}, {date_issued}, p. {seq}. "
                f"Chronicling America: Historic American Newspapers, Library of Congress.")
    code = "InC" if in_copyright else "PD"
    rights_stmt = ("In copyright (non-commercial fair use)" if in_copyright
                   else "Public domain (Chronicling America, LoC)")
    return MediaResult(
        source="chronam", source_id=page_id.strip("/"),
        title=f"{paper} — {date_issued} p.{seq}".strip(" —"),
        url=image_url, license=code, creator=paper or "Chronicling America",
        license_url="", rights_statement=rights_stmt,
        attribution_text=citation, source_url=f"{_BASE}{page_id}",
        date=year, kind="clipping",
    )


def download(url, dest):
    return _download(url, dest)
