"""Score patent-trademark candidate pairs.

Score components (additive, max ~1.0):
  date_order      patent grant precedes trademark filing → positive
                  trademark filed before patent → slight negative (not disqualifying)
  date_proximity  closer dates → higher score (within 5 years is peak)
  class_signal    CPC class maps to trademark goods category → boost
"""

from __future__ import annotations

import re
from datetime import date

PRODUCT_CLASSES = {"B42F", "B42D", "B41J", "B41L", "G06C", "G06K", "G09F"}

_LEGAL_SUFFIXES = re.compile(
    r'\b(COMPANY|CO\.?|INC\.?|CORP\.?|CORPORATION|LTD\.?|LLC)\b',
    re.IGNORECASE,
)


def _normalise(s: str) -> str:
    """Strip legal suffixes, upper-case, collapse whitespace."""
    s = _LEGAL_SUFFIXES.sub("", s or "").upper()
    return " ".join(s.split())


def is_company_name_mark(canonical_name: str, mark_name: str | None) -> bool:
    """True when the mark text is essentially the company's own name.

    Filters marks like "REMINGTON" for entity "Remington Arms Company" —
    pairing those against every patent produces systematic false positives
    (D006).
    """
    cn = _normalise(canonical_name)
    mn = _normalise(mark_name or "")
    if not mn:
        return False
    return cn in mn or mn in cn


def date_score(grant_dt: date | None, filing_dt: date | None) -> float:
    """Score in [-0.4, 0.5] based on date ordering and proximity.

    Patent grant before trademark filing is expected (positive).
    Trademark filed before patent grant is a flag (negative, not disqualifying —
    the trademark may cover a product line that preceded the specific patent).
    """
    if grant_dt is None or filing_dt is None:
        return 0.0

    delta_years = (filing_dt - grant_dt).days / 365.25

    if delta_years >= 0:
        proximity = max(0.0, 1.0 - delta_years / 20.0)
        return 0.5 * proximity
    else:
        return max(-0.4, delta_years / 25.0)


def class_score(cpc_classes: list[str]) -> float:
    """0.3 if any CPC class is in the product signal set, else 0.0."""
    return 0.3 if any(c in PRODUCT_CLASSES for c in cpc_classes) else 0.0


# Bonus weights for each semantic signal component
SEMANTIC_CAP = 0.25
_TITLE_HIT_WEIGHT    = 0.20  # mark name in patent title — controlled vocab, specific
_ABSTRACT_HIT_WEIGHT = 0.10  # mark name in abstract — broader, weaker signal
_GOODS_TITLE_WEIGHT  = 0.10  # G&S tokens overlap patent title tokens
_GOODS_ABSTRACT_WEIGHT = 0.05  # G&S tokens overlap abstract tokens
_GOODS_OVERLAP_THRESHOLD = 0.05  # minimum Jaccard to fire goods overlap signals


def semantic_score(
    title_name_hit: bool = False,
    abstract_name_hit: bool = False,
    goods_title_overlap: float = 0.0,
    goods_abstract_overlap: float = 0.0,
) -> float:
    """Compute raw semantic bonus from text-match signals (not yet capped).

    The caller is responsible for capping at SEMANTIC_CAP before adding to
    structural score. Keeping cap outside this function makes it testable.
    """
    score = 0.0
    if title_name_hit:
        score += _TITLE_HIT_WEIGHT
    if abstract_name_hit:
        score += _ABSTRACT_HIT_WEIGHT
    if goods_title_overlap > _GOODS_OVERLAP_THRESHOLD:
        score += _GOODS_TITLE_WEIGHT
    if goods_abstract_overlap > _GOODS_OVERLAP_THRESHOLD:
        score += _GOODS_ABSTRACT_WEIGHT
    return score


def total_score(
    grant_dt: date | None,
    filing_dt: date | None,
    cpc_classes: list[str],
    title_name_hit: bool = False,
    abstract_name_hit: bool = False,
    goods_title_overlap: float = 0.0,
    goods_abstract_overlap: float = 0.0,
) -> float:
    """Structural + capped semantic score. All signal params default to off.

    Calling total_score(grant_dt, filing_dt, cpc_classes) without signal args
    is identical to the pre-6C behaviour.
    """
    structural = date_score(grant_dt, filing_dt) + class_score(cpc_classes)
    semantic   = min(SEMANTIC_CAP, semantic_score(
        title_name_hit, abstract_name_hit,
        goods_title_overlap, goods_abstract_overlap,
    ))
    return round(structural + semantic, 4)
