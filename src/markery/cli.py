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
  markery site build information-systems
  markery site build information-systems --out projects/information-systems/site
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
    "site":           "Build static research site  (build <project>)",
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
        _site_build(args.project, args.out)


def _site_build(project: str, out: str | None) -> None:
    from pathlib import Path
    from site_builder import queries as q
    from site_builder import render as r

    db_paths = {
        "entities":   "data/entities.duckdb",
        "patents":    "data/patents.duckdb",
        "trademarks": "data/trademarks.duckdb",
    }

    out_dir = Path(out) if out else Path(f"projects/{project}/site")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "entities").mkdir(exist_ok=True)
    (out_dir / "matches").mkdir(exist_ok=True)

    print(f"Building site for '{project}' → {out_dir}/")

    entity_ids  = q.get_project_entity_ids(project)
    entities    = q.get_entities(db_paths, entity_ids)
    trademarks  = q.get_trademarks_for_project(db_paths, entity_ids)
    patents     = q.get_patents_for_project(db_paths, entity_ids)
    matches     = q.get_confirmed_matches(project, db_paths)
    stats       = q.get_entity_stats(db_paths, entity_ids, trademarks, patents, matches)
    colors      = r._entity_color_map(entity_ids)

    pages: list[Path] = []

    pages.append(r.render_landing(project, entities, trademarks, patents, matches, stats, db_paths, out_dir))
    print(f"  landing          → {pages[-1].name}")

    pages.append(r.render_trademark_gallery(project, entities, trademarks, matches, colors, db_paths, out_dir))
    print(f"  trademark gallery → {pages[-1].name}")

    pages.append(r.render_patent_gallery(project, entities, patents, matches, colors, db_paths, out_dir))
    print(f"  patent gallery   → {pages[-1].name}")

    for entity in entities:
        ent_tms  = [t for t in trademarks if t["entity_id"] == entity["entity_id"]]
        ent_pats = [p for p in patents    if p["entity_id"] == entity["entity_id"]]
        ent_mats = [m for m in matches    if m["entity_id"] == entity["entity_id"]]
        ent_stats = stats.get(entity["entity_id"], {})
        p = r.render_entity_page(project, entity, entities, ent_tms, ent_pats, ent_mats, ent_stats, out_dir)
        pages.append(p)
        print(f"  entity           → entities/{p.name}")

    seen_slugs: set[str] = set()
    for match in matches:
        slug = match.get("slug", "")
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        p = r.render_match_essay(project, match, entities, db_paths, out_dir)
        pages.append(p)
        print(f"  match essay      → matches/{p.name}")

    print(f"\n{len(pages)} pages written to {out_dir}/")


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
        "site":          lambda: cmd_site(rest),
    }[cmd]()


if __name__ == "__main__":
    main()
