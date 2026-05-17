"""
cli.py — argument parsing for the patent_docs module.

Subcommands:
  migrate    Add patent_documents / patent_figures tables to patents.duckdb
  fetch      Download grant PDFs and extract page-1 figures
  score      Enrich candidates.jsonl with text-signal fields
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECTS_DIR = Path("projects")
PATENTS_DB   = Path("patents.duckdb")
TM_DB        = Path("trademarks.duckdb")


def _project_dir(name: str) -> Path:
    d = PROJECTS_DIR / name
    if not d.is_dir():
        print(f"Project not found: {d}")
        sys.exit(1)
    return d


def cmd_migrate(args: argparse.Namespace) -> None:
    from .migrate import migrate
    migrate(str(PATENTS_DB))


def cmd_fetch(args: argparse.Namespace) -> None:
    from .fetch import (
        fetch_patents,
        patents_from_confirmed,
        patents_from_candidates,
    )

    project_dir = _project_dir(args.project)

    if args.patent:
        patent_nos = args.patent
    elif args.confirmed:
        patent_nos = patents_from_confirmed(project_dir / "matches" / "confirmed.jsonl")
    else:
        patent_nos = patents_from_candidates(
            project_dir / "matches" / "candidates.jsonl",
            min_score=args.min_score,
        )

    if not patent_nos:
        print("No patents to fetch.")
        return

    print(f"Fetching {len(patent_nos)} patent(s): {', '.join(patent_nos)}")
    fetch_patents(patent_nos, project_dir, PATENTS_DB, force=args.force)


def cmd_score(args: argparse.Namespace) -> None:
    from .signals import enrich_candidates

    project_dir     = _project_dir(args.project)
    candidates_path = project_dir / "matches" / "candidates.jsonl"

    print(f"Enriching {candidates_path} ...")
    n = enrich_candidates(candidates_path, PATENTS_DB, TM_DB)
    print(f"Enriched {n} candidates with text signals.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Patent document tools: migrate, fetch, score"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    # migrate
    sub.add_parser("migrate", help="Add patent_documents/patent_figures tables")

    # fetch
    p_fetch = sub.add_parser("fetch", help="Download PDFs and extract figures")
    p_fetch.add_argument("project", nargs="?", default="information-systems")
    p_fetch.add_argument("--patent", nargs="+", metavar="PATENT_NO",
                         help="Specific patent number(s) to fetch")
    p_fetch.add_argument("--confirmed", action="store_true",
                         help="Fetch all patents in confirmed.jsonl (default when no --patent)")
    p_fetch.add_argument("--min-score", type=float, default=0.70,
                         help="Fetch candidates with score >= this (default: 0.70)")
    p_fetch.add_argument("--force", action="store_true",
                         help="Re-download even if PDF already exists")

    # score
    p_score = sub.add_parser("score", help="Enrich candidates.jsonl with text signals")
    p_score.add_argument("project", nargs="?", default="information-systems")

    args = ap.parse_args()
    {
        "migrate": cmd_migrate,
        "fetch":   cmd_fetch,
        "score":   cmd_score,
    }[args.cmd](args)
