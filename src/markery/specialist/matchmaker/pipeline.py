"""Pipeline state tracking for the match → enrich → rescore workflow.

State is persisted in projects/<name>/matches/pipeline_state.json.
Each pass writes its timestamp and relevant metrics; the next pass
checks the state before running to prevent accidental data loss.

Typical session:

    markery match <project>              → writes generated_at, clears enriched_at
    markery patent signals <project>     → writes enriched_at
    markery match rescore <project>      → writes rescored_at   (Phase 6C)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def read_state(path: Path) -> dict:
    """Return current pipeline state. Empty dict if the file does not exist."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, default=str) + "\n")


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    sv  = sorted(values)
    idx = min(int(len(sv) * p), len(sv) - 1)
    return round(sv[idx], 4)


def mark_generated(
    path: Path,
    candidate_count: int,
    scores: list[float],
) -> None:
    """Record a completed generate pass. Clears enriched_at and rescored_at."""
    state = {
        "generated_at":    datetime.now().isoformat(timespec="seconds"),
        "enriched_at":     None,
        "rescored_at":     None,
        "candidate_count": candidate_count,
        "enriched_count":  None,
        "score_p50":       _percentile(scores, 0.50),
        "score_p90":       _percentile(scores, 0.90),
    }
    _write(path, state)


def mark_enriched(path: Path, enriched_count: int) -> None:
    """Record a completed enrich pass. Clears rescored_at."""
    state = read_state(path)
    state["enriched_at"]    = datetime.now().isoformat(timespec="seconds")
    state["enriched_count"] = enriched_count
    state["rescored_at"]    = None
    _write(path, state)


def mark_rescored(path: Path) -> None:
    """Record a completed rescore pass."""
    state = read_state(path)
    state["rescored_at"] = datetime.now().isoformat(timespec="seconds")
    _write(path, state)


def is_enriched(path: Path) -> bool:
    """True if enrichment has been run since the last generate pass."""
    return bool(read_state(path).get("enriched_at"))
