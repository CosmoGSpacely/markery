"""Project root resolution and path contracts for all specialists."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class Project:
    """Path contract for a research project directory."""

    name: str

    @property
    def root(self) -> Path:
        return ROOT / "projects" / self.name

    @property
    def candidates(self) -> Path:
        return self.root / "matches" / "candidates.jsonl"

    @property
    def confirmed(self) -> Path:
        return self.root / "matches" / "confirmed.jsonl"

    @property
    def content(self) -> Path:
        return self.root / "content"

    @property
    def site(self) -> Path:
        return self.root / "site"

    @property
    def rejected(self) -> Path:
        return self.root / "matches" / "rejected.jsonl"

    @property
    def entities_file(self) -> Path:
        return self.root / "entities.txt"

    def exists(self) -> bool:
        return self.root.is_dir()
