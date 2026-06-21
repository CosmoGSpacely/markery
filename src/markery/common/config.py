"""Project root resolution and shared database paths.

Project type definitions and path contracts have moved to
markery.common.project. Import Project from there.
"""

from __future__ import annotations

from pathlib import Path


def _find_root() -> Path:
    """Walk up from this file until pyproject.toml is found."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not locate project root (no pyproject.toml found)")


ROOT = _find_root()

# Unified site root: the Markery portal and every project's nested site live here.
SITE_ROOT = ROOT / "site"

# Single definition site for the default LLM model. The dated ID is pinned for
# reproducibility. Override per-call with --model or the MARKERY_MODEL env var.
# Note: Haiku 4.5's cacheable-prefix minimum is 4096 tokens (see common/llm.py).
DEFAULT_MODEL = "claude-haiku-4-5-20251001"

DB = {
    "patents":    ROOT / "data" / "patents.duckdb",
    "trademarks": ROOT / "data" / "trademarks.duckdb",
    "entities":   ROOT / "data" / "entities.duckdb",
}

_SETUP_HINTS = {
    "patents":    "Run 'markery patent build' to populate patents.duckdb.",
    "trademarks": "Run 'markery trademark build' to populate trademarks.duckdb.",
    "entities":   "Copy or create data/entities.duckdb with the entity registry.",
}


def require_db(name: str) -> "Path":
    """Return the DB path for name, or exit with a clear setup hint.

    Call this at CLI entry points before opening a DuckDB connection.
    """
    import sys
    path = DB[name]
    if not path.exists():
        print(
            f"Database '{name}' not found at {path}.\n"
            f"{_SETUP_HINTS.get(name, 'Check SETUP.md for instructions.')}",
            file=sys.stderr,
        )
        sys.exit(1)
    return path
