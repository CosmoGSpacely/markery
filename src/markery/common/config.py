"""Project root resolution and shared database paths.

Project type definitions and path contracts have moved to
markery.common.project. Import Project from there.
"""

from __future__ import annotations

import os
from pathlib import Path


def _find_root() -> Path:
    """Resolve the project root.

    Honour MARKERY_ROOT if set (used by hermetic tests to point the CLI at a
    synthetic repo); otherwise walk up from this file until pyproject.toml.
    """
    env = os.environ.get("MARKERY_ROOT")
    if env:
        return Path(env).expanduser().resolve()
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

# Data directory holding the corpus DBs. Honour MARKERY_DATA_DIR if set (hermetic
# tests point this at a synthetic-fixture dir); otherwise it is ROOT/data.
_DATA_DIR = (
    Path(os.environ["MARKERY_DATA_DIR"]).expanduser().resolve()
    if os.environ.get("MARKERY_DATA_DIR")
    else ROOT / "data"
)

DB = {
    "patents":    _DATA_DIR / "patents.duckdb",
    "trademarks": _DATA_DIR / "trademarks.duckdb",
    "entities":   _DATA_DIR / "entities.duckdb",
}

# Record-image assets (mark drawings, patent figures) live as files alongside the
# DBs (Phase 28 P3 — externalized from BLOBs). The DB rows reference paths relative
# to this directory.
ASSETS_DIR = _DATA_DIR / "assets"

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
