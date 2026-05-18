"""PATENT specialist — public interface.

Owns patents.duckdb. Provides programmatic access for MATCHMAKER and PUBLISHER.
"""

from markery.specialist.patent.build import (
    build,
    insert_patent,
    load_seed,
    open_db,
)
from markery.specialist.patent.epo_client import EPOClient
from markery.specialist.patent.figures import fetch_and_store as fetch_figure

__all__ = [
    "build",
    "insert_patent",
    "load_seed",
    "open_db",
    "EPOClient",
    "fetch_figure",
]