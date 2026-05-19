"""CLI for the PATENT specialist.

Registered as: markery patent <subcommand>

Subcommands:
  build             Populate patents.duckdb from EPO OPS
  fetch             Fetch figures for patents in a project
  figures           Fetch figure for a single patent number
  verify-credentials  Check EPO OPS token
  signals           Enrich candidates.jsonl with text signals
  migrate-figures   One-time migration: disk PNGs → BLOB storage
"""

from __future__ import annotations

import argparse
import sys

from markery.common.config import DB, Project


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_build(args: argparse.Namespace) -> None:
    from markery.specialist.patent.build import build
    build(
        classes    = args.classes or None,
        resume     = args.resume,
        year_start = args.year_start,
        year_end   = args.year_end,
        seed_only  = args.seed_only,
    )


def cmd_fetch(args: argparse.Namespace) -> None:
    from markery.specialist.patent.build import open_db
    from markery.specialist.patent.figures import fetch_and_store
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials
    from markery.common.config import Project

    project = Project(args.project)
    if not project.exists():
        print(f"Project not found: {project.root}")
        sys.exit(1)

    if args.patent:
        patent_nos = args.patent
    elif args.confirmed:
        import json
        confirmed = project.confirmed
        if not confirmed.exists():
            print(f"No confirmed.jsonl at {confirmed}")
            sys.exit(1)
        patent_nos = [
            json.loads(l)["patent_no"]
            for l in confirmed.read_text().splitlines() if l.strip()
        ]
    else:
        import json
        candidates = project.candidates
        if not candidates.exists():
            print(f"No candidates.jsonl at {candidates}")
            sys.exit(1)
        patent_nos = list({
            json.loads(l)["patent_no"]
            for l in candidates.read_text().splitlines() if l.strip()
            if json.loads(l).get("score", 0) >= args.min_score
        })

    if not patent_nos:
        print("No patents to fetch.")
        return

    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    conn   = open_db()

    print(f"Fetching figures for {len(patent_nos)} patent(s) ...")
    stored = 0
    for pno in patent_nos:
        ok = fetch_and_store(pno, client, conn)
        if ok:
            stored += 1
            print(f"  {pno}: stored")
        else:
            print(f"  {pno}: skipped (already stored or no figure)")
    conn.close()
    print(f"\n{stored} figure(s) stored.")


def cmd_figures(args: argparse.Namespace) -> None:
    from markery.specialist.patent.build import open_db
    from markery.specialist.patent.figures import fetch_and_store
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials

    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    conn   = open_db()
    ok = fetch_and_store(args.patent_no, client, conn)
    conn.close()
    if ok:
        print(f"{args.patent_no}: figure stored.")
    else:
        print(f"{args.patent_no}: skipped (already stored or no figure available).")


def cmd_verify_credentials(args: argparse.Namespace) -> None:
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials

    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    info   = client.token_info()
    print(f"Token: {info['token_prefix']}")
    print(f"Expires in: {info['expires_in_s']}s")
    print("EPO credentials OK.")


def cmd_signals(args: argparse.Namespace) -> None:
    from markery.specialist.patent.signals import enrich_candidates
    from markery.specialist.matchmaker.pipeline import mark_enriched

    project = Project(args.project)
    if not project.exists():
        print(f"Project not found: {project.root}")
        sys.exit(1)

    candidates_path = project.candidates
    print(f"Enriching {candidates_path} ...")
    n = enrich_candidates(candidates_path)
    mark_enriched(project.pipeline_state, enriched_count=n)
    print(f"Enriched {n} candidates with text signals.")


def cmd_migrate_figures(args: argparse.Namespace) -> None:
    from markery.specialist.patent.build import open_db
    from markery.specialist.patent.figures import migrate_path_figures

    conn = open_db()
    n    = migrate_path_figures(args.project, conn)
    conn.close()
    print(f"Migrated {n} figure(s) to BLOB storage.")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        prog="markery patent",
        description="PATENT specialist: build, fetch, and query patents.duckdb",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    # build
    p_build = sub.add_parser("build", help="Populate patents.duckdb from EPO OPS")
    p_build.add_argument("--classes", nargs="+", metavar="CPC",
                         help="CPC class codes to fetch (default: all 7)")
    p_build.add_argument("--resume", action="store_true",
                         help="Skip windows already in fetch_log")
    p_build.add_argument("--year-start", type=int, default=1900, metavar="YEAR")
    p_build.add_argument("--year-end",   type=int, default=1939, metavar="YEAR")
    p_build.add_argument("--seed-only",  action="store_true",
                         help="Insert seed patents only, skip EPO fetch")

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch figures for patents in a project")
    p_fetch.add_argument("project", nargs="?", default="information-systems")
    p_fetch.add_argument("--patent", nargs="+", metavar="PATENT_NO",
                         help="Specific patent number(s)")
    p_fetch.add_argument("--confirmed", action="store_true",
                         help="Fetch all patents in confirmed.jsonl")
    p_fetch.add_argument("--min-score", type=float, default=0.70,
                         help="Minimum score threshold for candidates (default: 0.70)")

    # figures
    p_fig = sub.add_parser("figures", help="Fetch figure for a single patent")
    p_fig.add_argument("patent_no", metavar="PATENT_NO")

    # verify-credentials
    sub.add_parser("verify-credentials", help="Verify EPO OPS OAuth2 credentials")

    # signals
    p_sig = sub.add_parser("signals", help="Enrich candidates.jsonl with text signals")
    p_sig.add_argument("project", nargs="?", default="information-systems")

    # migrate-figures
    p_mig = sub.add_parser("migrate-figures",
                            help="Migrate on-disk PNGs to BLOB storage (one-time)")
    p_mig.add_argument("project", nargs="?", default="information-systems")

    args = ap.parse_args()
    {
        "build":               cmd_build,
        "fetch":               cmd_fetch,
        "figures":             cmd_figures,
        "verify-credentials":  cmd_verify_credentials,
        "signals":             cmd_signals,
        "migrate-figures":     cmd_migrate_figures,
    }[args.cmd](args)
