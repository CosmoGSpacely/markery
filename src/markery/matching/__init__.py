"""
markery.matching — cross-reference patents.duckdb against trademarks.duckdb via entities.duckdb.

Usage:
    python -m markery.matching <project>                 # generate candidates for a project
    python -m markery.matching --all                     # all entities, no project filter
    python -m markery.matching --entity "Remington Rand" # single entity
"""
