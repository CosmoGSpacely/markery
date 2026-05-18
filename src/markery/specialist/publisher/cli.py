"""Publisher specialist CLI — static site generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def publisher_main() -> None:
    ap = argparse.ArgumentParser(prog="markery publisher")
    sub = ap.add_subparsers(dest="action", required=True)

    bp = sub.add_parser("build", help="Build static site for a project")
    bp.add_argument("project", help="Project name (directory under projects/)")
    bp.add_argument("--out", metavar="DIR",
                    help="Output directory (default: projects/<project>/site)")
    bp.add_argument("--base-url", metavar="URL", default=None,
                    help="Absolute base URL for Open Graph og:url tags")

    args = ap.parse_args()
    if args.action == "build":
        from markery.specialist.publisher.build import build_site
        build_site(args.project, Path(args.out) if args.out else None, base_url=args.base_url)
