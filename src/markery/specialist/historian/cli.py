"""Historian specialist CLI."""

from __future__ import annotations

import argparse
import sys


def historian_main() -> None:
    parser = argparse.ArgumentParser(
        prog="markery historian",
        description="Historian specialist commands",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    prep = sub.add_parser("prepare", help="Generate BRIEF.md for a project session")
    prep.add_argument("project", help="Project name (directory under projects/)")
    prep.add_argument(
        "--min-score", type=float, default=0.5, metavar="SCORE",
        help="Minimum candidate score to count as unreviewed (default: 0.5)",
    )

    args = parser.parse_args()

    if args.action == "prepare":
        from markery.specialist.historian.prepare import prepare
        prepare(args.project, min_score=args.min_score)
