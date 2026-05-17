"""
cli.py — command-line entry point for the match package.

    python -m match <project>
    python -m match --all
    python -m match --entity "Remington Rand"
    python -m match --list-entities
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from .link import (
    entity_ids_for_project,
    generate_candidates,
    write_candidates,
    read_confirmed,
)

PROJECTS_DIR  = Path("projects")
ENTITIES_DB   = "data/entities.duckdb"


def list_entities() -> None:
    conn = duckdb.connect(ENTITIES_DB, read_only=True)
    print("Entities in entities.duckdb:")
    for r in conn.execute(
        "SELECT entity_id, canonical_name, industry FROM company_entity ORDER BY entity_id"
    ).fetchall():
        print(f"  {r[0]:>3}  {r[1]:<25}  {r[2]}")
    conn.close()


def run_project(project_name: str, min_score: float) -> None:
    project_dir  = PROJECTS_DIR / project_name
    entities_file = project_dir / "entities.txt"
    matches_dir  = project_dir / "matches"

    entity_ids = entity_ids_for_project(entities_file)
    if not entity_ids:
        print(f"No entities.txt found at {entities_file} (or file is empty).")
        print("Create it with one entity_id per line.")
        return

    print(f"Project: {project_name}")
    print(f"Entities in scope: {entity_ids}")

    candidates = generate_candidates(entity_ids, min_score=min_score)
    write_candidates(candidates, matches_dir / "candidates.jsonl")

    confirmed_path = matches_dir / "confirmed.jsonl"
    confirmed = read_confirmed(confirmed_path)
    if confirmed:
        confirmed_keys = {(c["patent_no"], c["trademark_serial"]) for c in confirmed}
        novel = [c for c in candidates
                 if (c["patent_no"], c["trademark_serial"]) not in confirmed_keys]
        print(f"  {len(confirmed)} confirmed pairs already in confirmed.jsonl")
        print(f"  {len(novel)} novel candidates (not yet confirmed)")


def run_all(min_score: float) -> None:
    print("Generating candidates for all entities ...")
    candidates = generate_candidates(entity_ids=None, min_score=min_score)
    out = Path("matches_all.jsonl")
    write_candidates(candidates, out)


def run_entity(name: str, min_score: float) -> None:
    conn = duckdb.connect(ENTITIES_DB, read_only=True)
    row = conn.execute(
        "SELECT entity_id FROM company_entity WHERE canonical_name = ?", [name]
    ).fetchone()
    conn.close()
    if not row:
        print(f"Entity '{name}' not found in entities.duckdb.")
        return
    candidates = generate_candidates([row[0]], min_score=min_score)
    out = Path(f"match_{name.lower().replace(' ', '_')}.jsonl")
    write_candidates(candidates, out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate patent-trademark candidate pairs via entities.duckdb"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("project", nargs="?",
                       help="Project name under projects/ (uses projects/<name>/entities.txt)")
    group.add_argument("--all", action="store_true",
                       help="Run for all entities, write to matches_all.jsonl")
    group.add_argument("--entity", metavar="NAME",
                       help="Single canonical entity name")
    group.add_argument("--list-entities", action="store_true",
                       help="List all entities in entities.duckdb and exit")
    parser.add_argument("--min-score", type=float, default=0.1,
                        help="Minimum score to include in output (default: 0.1)")
    args = parser.parse_args()

    if args.list_entities:
        list_entities()
    elif args.all:
        run_all(args.min_score)
    elif args.entity:
        run_entity(args.entity, args.min_score)
    elif args.project:
        run_project(args.project, args.min_score)
