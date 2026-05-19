"""Cross-specialist operation dispatch.

Policy (G5): any call that crosses a specialist boundary routes through this
module.  Callers import from here; they do not import from other specialists
directly.  This gives a single auditable place to:

  - see every operation that crosses a specialist boundary
  - apply rate limiting, retry logic, or permission checks in the future
  - keep specialist internal APIs from leaking into unrelated callers

All imports from other specialists are deferred (inside each function) so that
importing this module does not pull in every specialist's dependencies.

Current operations
------------------
enrich_signal_fields   patent specialist → add text signals to candidates.jsonl
"""

from __future__ import annotations

from pathlib import Path


def enrich_signal_fields(candidates_path: Path) -> int:
    """Enrich candidates.jsonl with text-match signals via the patent specialist.

    Adds title_name_hit, abstract_name_hit, goods_title_overlap,
    goods_abstract_overlap to each candidate row by reading patents.duckdb
    and trademarks.duckdb through the patent specialist's published API.

    Returns the count of candidates enriched.
    """
    from markery.specialist.patent.signals import enrich_candidates
    return enrich_candidates(candidates_path)
