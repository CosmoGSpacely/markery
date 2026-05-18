"""
markery — unified CLI for the Markery research tool.

Usage:
  markery match information-systems
  markery match --list-entities
  markery review information-systems --min-score 0.65
  markery review --mark VI-DEX
  markery status
  markery enhance enhance 71235764 --out-dir projects/information-systems/output/vi-dex
  markery enhance batch "cf.serial_no IN ('71235764')" --out-dir projects/.../output/batch
  markery enhance gallery projects/.../output/vi-dex --title "VI-DEX, Wilson Jones 1927"
  markery patent build --seed-only
  markery patent build --resume
  markery patent fetch information-systems --confirmed
  markery patent figures US1261167A
  markery patent verify-credentials
  markery patent signals information-systems
  markery patent migrate-figures information-systems
  markery site build information-systems
  markery site build information-systems --out projects/information-systems/site
  markery publisher build information-systems
"""

from __future__ import annotations

import sys

_SUBCOMMANDS = {
    "match":       "Generate patent-trademark candidate pairs",
    "review":      "Interactive candidate pair review",
    "status":      "Show database row counts and project metrics",
    "enhance":     "Enhance mark images  (enhance|batch|gallery)",
    "patent":      "Patent specialist  (build|fetch|figures|signals|…)",
    "trademark":   "Trademark specialist  (build|enrich|status|…)",
    "matchmaker":  "Entity registry management  (build|list|status)",
    "site":        "Build static research site  (build <project>)",
    "publisher":   "Publisher specialist  (build <project>)",
}


def _print_help() -> None:
    print("usage: markery <subcommand> [args]\n")
    print("USPTO trademark-patent cross-reference research tool\n")
    print("subcommands:")
    for name, desc in _SUBCOMMANDS.items():
        print(f"  {name:<16}  {desc}")
    print("\nRun 'markery <subcommand> --help' for subcommand options.")
    print("All commands must be run from the project root with the venv active.")


def cmd_match(rest: list[str]) -> None:
    from markery.specialist.matchmaker.cli import match_main
    sys.argv = ["markery match"] + rest
    match_main()


def cmd_matchmaker(rest: list[str]) -> None:
    from markery.specialist.matchmaker.cli import matchmaker_main
    sys.argv = ["markery matchmaker"] + rest
    matchmaker_main()


def cmd_review(rest: list[str]) -> None:
    from markery.specialist.historian.review import main
    sys.argv = ["markery review"] + rest
    main()


def cmd_status() -> None:
    from markery.specialist.historian.status import main
    main()


def cmd_enhance(rest: list[str]) -> None:
    from markery.specialist.publisher.image_enhancement.cli import main
    sys.argv = ["markery enhance"] + rest
    main()


def cmd_patent(rest: list[str]) -> None:
    from markery.specialist.patent.cli import main
    sys.argv = ["markery patent"] + rest
    main()


def cmd_trademark(rest: list[str]) -> None:
    from markery.specialist.trademark.cli import main
    sys.argv = ["markery trademark"] + rest
    main()


def cmd_publisher(rest: list[str]) -> None:
    from markery.specialist.publisher.cli import publisher_main
    sys.argv = ["markery publisher"] + rest
    publisher_main()


def cmd_site(rest: list[str]) -> None:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(prog="markery site")
    sub = parser.add_subparsers(dest="action", required=True)

    build = sub.add_parser("build", help="Render project to HTML")
    build.add_argument("project", help="Project name (directory under projects/)")
    build.add_argument("--out", metavar="DIR",
                       help="Output directory (default: projects/<project>/site)")

    args = parser.parse_args(rest)

    if args.action == "build":
        from markery.specialist.publisher.build import build_site
        build_site(args.project, Path(args.out) if args.out else None)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        _print_help()
        return

    cmd  = sys.argv[1]
    rest = sys.argv[2:]

    if cmd not in _SUBCOMMANDS:
        print(f"markery: unknown subcommand '{cmd}'")
        print("Run 'markery --help' for available subcommands.")
        sys.exit(1)

    {
        "match":      lambda: cmd_match(rest),
        "review":     lambda: cmd_review(rest),
        "status":     lambda: cmd_status(),
        "enhance":    lambda: cmd_enhance(rest),
        "patent":     lambda: cmd_patent(rest),
        "trademark":  lambda: cmd_trademark(rest),
        "matchmaker": lambda: cmd_matchmaker(rest),
        "site":       lambda: cmd_site(rest),
        "publisher":  lambda: cmd_publisher(rest),
    }[cmd]()


if __name__ == "__main__":
    main()
