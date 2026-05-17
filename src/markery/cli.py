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
  markery fetch-patents information-systems --confirmed
  markery fetch-patents --patent US1261167A
  markery score-signals information-systems
"""

from __future__ import annotations

import sys

_SUBCOMMANDS = {
    "match":          "Generate patent-trademark candidate pairs",
    "review":         "Interactive candidate pair review",
    "status":         "Show database row counts and project metrics",
    "enhance":        "Enhance mark images  (enhance|batch|gallery)",
    "fetch-patents":  "Download patent PDFs and extract figures",
    "score-signals":  "Enrich candidates.jsonl with text signals",
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
    from markery.matching.cli import main
    sys.argv = ["markery match"] + rest
    main()


def cmd_review(rest: list[str]) -> None:
    from markery.review import main
    sys.argv = ["markery review"] + rest
    main()


def cmd_status() -> None:
    from markery.status import main
    main()


def cmd_enhance(rest: list[str]) -> None:
    from image_enhancement.cli import main
    sys.argv = ["markery enhance"] + rest
    main()


def cmd_fetch_patents(rest: list[str]) -> None:
    from patent_docs.cli import main
    sys.argv = ["markery fetch-patents", "fetch"] + rest
    main()


def cmd_score_signals(rest: list[str]) -> None:
    from patent_docs.cli import main
    sys.argv = ["markery score-signals", "score"] + rest
    main()


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
        "match":         lambda: cmd_match(rest),
        "review":        lambda: cmd_review(rest),
        "status":        lambda: cmd_status(),
        "enhance":       lambda: cmd_enhance(rest),
        "fetch-patents":  lambda: cmd_fetch_patents(rest),
        "score-signals": lambda: cmd_score_signals(rest),
    }[cmd]()


if __name__ == "__main__":
    main()
