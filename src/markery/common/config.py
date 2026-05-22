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

DB = {
    "patents":    ROOT / "data" / "patents.duckdb",
    "trademarks": ROOT / "data" / "trademarks.duckdb",
    "entities":   ROOT / "data" / "entities.duckdb",
}
