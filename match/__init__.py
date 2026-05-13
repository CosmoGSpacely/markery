"""
match — cross-reference patents.duckdb against trademarks.duckdb via entities.duckdb.

Usage:
    python -m match <project>                 # generate candidates for a project
    python -m match --all                     # all entities, no project filter
    python -m match --entity "Remington Rand" # single entity
"""
