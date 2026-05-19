"""CLI for the MATCHMAKER specialist.

Two top-level entry points:

    markery match <subcommand>
        Generate patent-trademark candidate pairs (human-facing verb, per Q25).
        Subcommands: project, --all, --entity, --list-entities

    markery matchmaker <subcommand>
        Entity registry management.
        Subcommands: build, list, status
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markery.common.config import DB, Project


# ---------------------------------------------------------------------------
# markery match
# ---------------------------------------------------------------------------

def _list_entities() -> None:
    import duckdb
    conn = duckdb.connect(str(DB["entities"]), read_only=True)
    print("Entities in entities.duckdb:")
    for r in conn.execute(
        "SELECT entity_id, canonical_name, industry FROM company_entity ORDER BY entity_id"
    ).fetchall():
        print(f"  {r[0]:>3}  {r[1]:<28}  {r[2]}")
    conn.close()


def _print_resolve_report(report: dict, project: str, auto_fetch: bool) -> None:
    low, high = 0.40, 0.60
    print(f"\n{report['band_count']} pair(s) in uncertainty band [{low}, {high}]")
    n_abs = len(report["missing_abstracts"])
    n_gds = len(report["missing_goods"])
    print(f"  Missing abstracts : {n_abs} patent(s)")
    if n_abs:
        print(f"    → run: markery patent signals {project}")
    print(f"  Missing G&S text  : {n_gds} trademark(s)")
    if n_gds:
        print(f"    → run: markery trademark enrich-project {project} --source candidates --min-score 0.40")
    print(f"  Resolvable now    : {report['resolvable']} pair(s)")
    if report["resolvable"] and not auto_fetch:
        print(f"    → run: markery match rescore {project}")

    if not auto_fetch:
        return

    if report["resolvable"] == 0:
        print("\n--auto-fetch: no pairs resolvable from existing DB data; run specialist fetch commands first.")
        return

    print(f"\n--auto-fetch: enriching signals from existing DB data and rescoring ...")
    from markery.specialist.orchestrator import enrich_signal_fields
    from markery.specialist.matchmaker.link import rescore_candidates
    from markery.specialist.matchmaker.pipeline import mark_enriched, mark_rescored

    proj = Project(project)
    n_enriched = enrich_signal_fields(proj.candidates)
    mark_enriched(proj.pipeline_state, n_enriched)
    rescore_candidates(proj.candidates)
    mark_rescored(proj.pipeline_state)
    if n_abs or n_gds:
        print(f"  {n_abs + n_gds} patent/trademark(s) still need external API fetch.")
        print("  After fetching, run 'markery match rescore' again to update those pairs.")


def _run_rescore(rest: list[str]) -> None:
    """Entry point for `markery match rescore <project>`."""
    parser = argparse.ArgumentParser(
        prog="markery match rescore",
        description="Pass 3: rewrite score field using existing signal fields",
    )
    parser.add_argument("project", help="Project name under projects/")
    args = parser.parse_args(rest)

    from markery.specialist.matchmaker.link import rescore_candidates
    from markery.specialist.matchmaker.pipeline import mark_rescored

    proj = Project(args.project)
    if not proj.exists():
        print(f"Project not found: {proj.root}")
        sys.exit(1)
    if not proj.candidates.exists():
        print(f"No candidates file. Run 'markery match {args.project}' first.")
        sys.exit(1)

    n = rescore_candidates(proj.candidates)
    if n:
        mark_rescored(proj.pipeline_state)
        print("Pipeline state updated (rescored_at set).")
    else:
        print("Nothing to rescore.")


def _run_project(
    project_name: str,
    min_score: float,
    force: bool = False,
    signals: bool = False,
    full: bool = False,
    resolve: bool = False,
    auto_fetch: bool = False,
) -> None:
    from markery.specialist.matchmaker.link import (
        entity_ids_for_project, generate_candidates,
        write_candidates, read_confirmed, read_rejected,
    )
    from markery.specialist.matchmaker.pipeline import (
        is_enriched, mark_generated,
    )
    proj = Project(project_name)
    if not proj.exists():
        print(f"Project not found: {proj.root}")
        sys.exit(1)

    if not force and is_enriched(proj.pipeline_state):
        print(
            f"candidates.jsonl has been enriched with signals since last generation.\n"
            f"Re-generating will discard those signal fields.\n"
            f"Use --force to regenerate anyway."
        )
        return

    entity_ids = entity_ids_for_project(proj.entities_file)
    if not entity_ids:
        print(f"No entities found at {proj.entities_file}.")
        print("Create it with one entity_id per line.")
        return

    print(f"Project: {project_name}")
    print(f"Entities in scope: {entity_ids}")

    candidates = generate_candidates(entity_ids, min_score=min_score)

    rejected_keys = read_rejected(proj.rejected)
    if rejected_keys:
        before = len(candidates)
        candidates = [
            c for c in candidates
            if (c["patent_no"], str(c["trademark_serial"])) not in rejected_keys
        ]
        print(f"  {before - len(candidates)} previously rejected pairs filtered")

    write_candidates(candidates, proj.candidates)
    mark_generated(
        proj.pipeline_state,
        candidate_count=len(candidates),
        scores=[c["score"] for c in candidates],
    )

    confirmed = read_confirmed(proj.confirmed)
    if confirmed:
        confirmed_keys = {(c["patent_no"], str(c["trademark_serial"])) for c in confirmed}
        novel = [c for c in candidates
                 if (c["patent_no"], str(c["trademark_serial"])) not in confirmed_keys]
        print(f"  {len(confirmed)} confirmed pairs already in confirmed.jsonl")
        print(f"  {len(novel)} novel candidates (not yet confirmed)")

    if signals or full:
        from markery.specialist.orchestrator import enrich_signal_fields
        from markery.specialist.matchmaker.pipeline import mark_enriched
        print("Enriching candidates with text signals ...")
        n = enrich_signal_fields(proj.candidates)
        mark_enriched(proj.pipeline_state, n)

    if full:
        from markery.specialist.matchmaker.link import rescore_candidates
        from markery.specialist.matchmaker.pipeline import mark_rescored
        rescore_candidates(proj.candidates)
        mark_rescored(proj.pipeline_state)

    if resolve:
        from markery.specialist.matchmaker.link import resolve_report
        report = resolve_report(project_name)
        _print_resolve_report(report, project_name, auto_fetch)


def _run_all(min_score: float) -> None:
    from markery.specialist.matchmaker.link import generate_candidates, write_candidates
    print("Generating candidates for all entities ...")
    candidates = generate_candidates(entity_ids=None, min_score=min_score)
    write_candidates(candidates, Path("matches_all.jsonl"))


def _run_entity(name: str, min_score: float) -> None:
    import duckdb
    from markery.specialist.matchmaker.link import generate_candidates, write_candidates
    conn = duckdb.connect(str(DB["entities"]), read_only=True)
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


def match_main() -> None:
    """Entry point for `markery match`."""
    # Dispatch `rescore` subcommand before the main parser sees it.
    rest = sys.argv[1:]
    if rest and rest[0] == "rescore":
        _run_rescore(rest[1:])
        return

    parser = argparse.ArgumentParser(
        prog="markery match",
        description="Generate patent-trademark candidate pairs via entities.duckdb",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("project", nargs="?",
                       help="Project name under projects/")
    group.add_argument("--all", action="store_true",
                       help="Run for all entities, write to matches_all.jsonl")
    group.add_argument("--entity", metavar="NAME",
                       help="Single canonical entity name")
    group.add_argument("--list-entities", action="store_true",
                       help="List all entities in entities.duckdb and exit")
    parser.add_argument("--min-score", type=float, default=0.1,
                        help="Minimum score to include in output (default: 0.1)")
    parser.add_argument("--force", action="store_true",
                        help="Regenerate even if candidates have been enriched")
    parser.add_argument("--signals", action="store_true",
                        help="Pass 1+2: generate then enrich with text signals")
    parser.add_argument("--full", action="store_true",
                        help="Pass 1+2+3: generate, enrich, and rescore")
    parser.add_argument("--resolve", action="store_true",
                        help="After generating, report uncertainty band and missing data")
    parser.add_argument("--auto-fetch", action="store_true",
                        help="With --resolve: enrich and rescore resolvable pairs automatically")
    args = parser.parse_args()

    if args.list_entities:
        _list_entities()
    elif args.all:
        _run_all(args.min_score)
    elif args.entity:
        _run_entity(args.entity, args.min_score)
    elif args.project:
        _run_project(
            args.project, args.min_score,
            force=args.force,
            signals=args.signals,
            full=args.full,
            resolve=args.resolve,
            auto_fetch=args.auto_fetch,
        )


# ---------------------------------------------------------------------------
# markery matchmaker
# ---------------------------------------------------------------------------

def cmd_build(args: argparse.Namespace) -> None:
    from markery.specialist.matchmaker.entities import build
    counts = build()
    print(f"entities.duckdb:")
    print(f"  {counts['entities']} entity/entities added")
    print(f"  {counts['variants']} variant(s) added")


def cmd_list(args: argparse.Namespace) -> None:
    from markery.specialist.matchmaker.entities import open_db, list_entities
    conn     = open_db()
    entities = list_entities(conn)
    conn.close()
    print(f"{'ID':>3}  {'Canonical name':<28}  {'Type':<14}  Industry")
    print("-" * 70)
    for e in entities:
        print(f"  {e['entity_id']:>3}  {e['canonical_name']:<28}  "
              f"{(e['entity_type'] or ''):<14}  {e['industry'] or ''}")


def cmd_status(args: argparse.Namespace) -> None:
    from markery.specialist.matchmaker.entities import open_db
    conn = open_db()
    n_entities = conn.execute("SELECT count(*) FROM company_entity").fetchone()[0]
    n_variants = conn.execute("SELECT count(*) FROM entity_name_variant").fetchone()[0]
    conn.close()
    print(f"entities.duckdb:")
    print(f"  company_entity       {n_entities:>6,}")
    print(f"  entity_name_variant  {n_variants:>6,}")


def matchmaker_main() -> None:
    """Entry point for `markery matchmaker`."""
    ap = argparse.ArgumentParser(
        prog="markery matchmaker",
        description="MATCHMAKER specialist: entity registry management",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("build",  help="Insert seed entities/variants (idempotent)")
    sub.add_parser("list",   help="List all entities with IDs and names")
    sub.add_parser("status", help="Row counts for entity registry tables")

    args = ap.parse_args()
    {
        "build":  cmd_build,
        "list":   cmd_list,
        "status": cmd_status,
    }[args.cmd](args)
