"""MATCHMAKER specialist — public interface.

Owns entities.duckdb. Reads patents.duckdb and trademarks.duckdb via ATTACH
for cross-specialist candidate generation (Q19).
"""

from markery.specialist.matchmaker.entities import build as build_entities, open_db
from markery.specialist.matchmaker.link import (
    generate_candidates,
    write_candidates,
    read_confirmed,
)
from markery.specialist.matchmaker.score import total_score

__all__ = [
    "build_entities",
    "open_db",
    "generate_candidates",
    "write_candidates",
    "read_confirmed",
    "total_score",
]
