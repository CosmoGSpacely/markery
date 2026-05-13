"""
score.py — rank patent-trademark candidate pairs.

Score components (all additive, max ~1.0):
  date_order    patent grant date precedes trademark filing date → strong positive
                trademark filed before patent → flag (negative score)
  date_proximity  closer dates → higher score (within 5 years is peak)
  class_signal  CPC class maps to trademark goods category → boost
"""

from __future__ import annotations
from datetime import date

# CPC classes whose subject matter strongly signals a product trademark
PRODUCT_CLASSES = {"B42F", "B42D", "B41J", "B41L", "G06C", "G06K", "G09F"}


def date_score(grant_dt: date | None, filing_dt: date | None) -> float:
    """
    Returns a score in [-0.4, 0.5] based on date ordering and proximity.
    patent grant before trademark filing is expected (positive).
    trademark filed before patent grant is a flag (negative, but not disqualifying —
    the trademark may cover a product line that preceded the specific patent).
    """
    if grant_dt is None or filing_dt is None:
        return 0.0

    delta_years = (filing_dt - grant_dt).days / 365.25

    if delta_years >= 0:
        # Patent precedes trademark — expected and positive
        # Peak score at 0–5 years gap, tapers to zero at 20 years
        proximity = max(0.0, 1.0 - delta_years / 20.0)
        return 0.5 * proximity
    else:
        # Trademark precedes patent — unusual, slight negative signal
        # Only penalize up to -0.4 for very large reversals (>10 years)
        return max(-0.4, delta_years / 25.0)


def class_score(cpc_classes: list[str]) -> float:
    """0.3 if any CPC class is in the product signal set, else 0.0."""
    return 0.3 if any(c in PRODUCT_CLASSES for c in cpc_classes) else 0.0


def total_score(grant_dt: date | None, filing_dt: date | None,
                cpc_classes: list[str]) -> float:
    return round(date_score(grant_dt, filing_dt) + class_score(cpc_classes), 4)
