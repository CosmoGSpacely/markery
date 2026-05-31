"""Wikipedia citation discovery adapter.

Discovery only — never uses Wikipedia prose as a source.
Extracts {{cite book}} and {{cite journal}} templates from article wikitext,
then resolves each citation to an IA or Gutenberg copy.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Optional

from .common import WikiCitation, SourceResult, make_slug
from . import ia as _ia
from . import gutenberg as _gut

_WP_API = "https://en.wikipedia.org/w/api.php"


# ---------------------------------------------------------------------------
# Template parsing
# ---------------------------------------------------------------------------

def _parse_template_params(body: str) -> dict[str, str]:
    """Parse pipe-separated key=value pairs from a template body string."""
    params: dict[str, str] = {}
    # Split on | but not inside nested {{ }}
    depth = 0
    current = ""
    for ch in body:
        if ch == "{":
            depth += 1
            current += ch
        elif ch == "}":
            depth -= 1
            current += ch
        elif ch == "|" and depth == 0:
            _store_param(current.strip(), params)
            current = ""
        else:
            current += ch
    _store_param(current.strip(), params)
    return params


def _store_param(segment: str, params: dict[str, str]) -> None:
    if "=" in segment:
        k, _, v = segment.partition("=")
        params[k.strip().lower()] = v.strip()


def _extract_templates(wikitext: str, template_name: str) -> list[str]:
    """Return list of template bodies (content between {{ and }}) for template_name."""
    pattern = re.compile(
        r"\{\{\s*" + re.escape(template_name) + r"\s*\|",
        re.IGNORECASE,
    )
    results = []
    for m in pattern.finditer(wikitext):
        start = m.start()
        depth = 0
        i = start
        while i < len(wikitext):
            if wikitext[i:i+2] == "{{":
                depth += 1
                i += 2
            elif wikitext[i:i+2] == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    results.append(wikitext[start:i])
                    break
            else:
                i += 1
    return results


def _template_to_citation(body: str, template_type: str) -> WikiCitation:
    # Strip outer {{ }} and template name
    inner = re.sub(r"^\{\{[^|]+\|?", "", body)
    inner = re.sub(r"\}\}$", "", inner)
    p = _parse_template_params(inner)

    # Author: try last/first, then author, then editor, then last1/first1
    author = ""
    if p.get("last") or p.get("first"):
        last = p.get("last", "")
        first = p.get("first", "")
        author = f"{last}, {first}".strip(", ")
    elif p.get("author"):
        author = p["author"]
    elif p.get("last1"):
        author = f"{p.get('last1', '')}, {p.get('first1', '')}".strip(", ")

    year_str = p.get("year") or p.get("date", "")
    year: Optional[int] = None
    m = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", year_str)
    if m:
        year = int(m.group(1))

    return WikiCitation(
        title=p.get("title", ""),
        author=author,
        year=year,
        isbn=p.get("isbn") or p.get("isbn13") or None,
        url=p.get("url") or None,
        template_type=template_type,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_citations(article_title: str) -> list[WikiCitation]:
    """Fetch wikitext for a Wikipedia article and extract cite book/journal templates."""
    params = {
        "action": "parse",
        "page": article_title,
        "prop": "wikitext",
        "format": "json",
        "redirects": "1",
    }
    url = f"{_WP_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "markery/1.0 (research)"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)

    if "error" in data:
        raise ValueError(
            f"Wikipedia API error for '{article_title}': "
            f"{data['error'].get('info', data['error'])}"
        )

    wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
    citations: list[WikiCitation] = []
    for tpl in _extract_templates(wikitext, "cite book"):
        citations.append(_template_to_citation(tpl, "cite book"))
    for tpl in _extract_templates(wikitext, "cite journal"):
        citations.append(_template_to_citation(tpl, "cite journal"))
    # Deduplicate by title (case-insensitive)
    seen: set[str] = set()
    unique: list[WikiCitation] = []
    for c in citations:
        key = c.title.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def resolve_to_source(citation: WikiCitation) -> Optional[SourceResult]:
    """Search IA and Gutenberg for a work matching the citation.

    Strategy:
    1. Guess IA identifiers from title + author, check metadata API.
    2. Search Gutenberg via Gutendex.
    3. Fall back to IA keyword search.
    Returns the first confirmed open-access match, or None.
    """
    title = citation.title
    author = citation.author

    # 1. Try IA identifier guessing
    for candidate_id in _ia.guess_identifiers(title, author):
        try:
            meta = _ia.fetch_metadata(candidate_id)
            if not meta.get("metadata", {}).get("title"):
                continue
            slug = make_slug(
                meta["metadata"].get("title", title),
                meta["metadata"].get("creator", author) or author,
            )
            access = "borrow" if meta["metadata"].get("access-restricted-item") else "open"
            return SourceResult(
                source="ia",
                identifier=candidate_id,
                title=meta["metadata"].get("title", title),
                author=meta["metadata"].get("creator", author) or author,
                year=citation.year,
                slug=slug,
                access=access,
            )
        except Exception:
            continue

    # 2. Try Gutenberg
    query = f"{title} {author}".strip()
    try:
        gut_results = _gut.search(query, max_results=3)
        for r in gut_results:
            if _title_matches(r.title, title):
                return _gut.to_source_result(r)
    except Exception:
        pass

    # 3. IA keyword search as last resort
    try:
        ia_results = _ia.search(f"{title} {author}", max_results=5)
        for r in ia_results:
            if _title_matches(r.title, title):
                return _ia.to_source_result(r)
    except Exception:
        pass

    return None


def _title_matches(found: str, target: str) -> bool:
    """Loose match: significant words of target appear in found."""
    stop = {"the", "a", "an", "of", "in", "and", "for", "to", "its", "by"}
    target_words = [w for w in re.findall(r"[a-z]+", target.lower()) if w not in stop]
    if not target_words:
        return False
    found_lower = found.lower()
    matches = sum(1 for w in target_words if w in found_lower)
    return matches >= max(2, len(target_words) // 2)
