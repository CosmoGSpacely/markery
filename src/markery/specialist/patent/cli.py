"""CLI for the PATENT specialist.

Registered as: markery patent <subcommand>

Subcommands:
  build             Populate patents.duckdb from EPO OPS
  fetch             Fetch figures for patents in a project
  figures           Fetch figure for a single patent number
  verify-credentials  Check EPO OPS token
  signals           Enrich candidates.jsonl with text signals
"""

from __future__ import annotations

import argparse
import sys

from markery.common.config import DB
from markery.common.project import Project, require_project, validate_patent_no


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
        seed_path  = args.seed_path or None,
        seed_only  = args.seed_only,
    )


def cmd_fetch(args: argparse.Namespace) -> None:
    from markery.specialist.patent.build import open_db
    from markery.specialist.patent.figures import fetch_and_store
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials

    project = require_project(args.project)

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

    patent_no = validate_patent_no(args.patent_no)
    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    conn   = open_db()
    ok = fetch_and_store(patent_no, client, conn)
    conn.close()
    if ok:
        print(f"{patent_no}: figure stored.")
    else:
        print(f"{patent_no}: skipped (already stored or no figure available).")


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

    project = require_project(args.project)

    candidates_path = project.candidates
    print(f"Enriching {candidates_path} ...")
    n = enrich_candidates(candidates_path)
    mark_enriched(project.pipeline_state, enriched_count=n)
    print(f"Enriched {n} candidates with text signals.")


def cmd_pull(args: argparse.Namespace) -> None:
    from markery.specialist.patent.build import open_db
    from markery.specialist.patent.fetch import fetch_patent_record
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials

    patent_no = validate_patent_no(args.patent_no)
    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    conn   = open_db()
    ok = fetch_patent_record(patent_no, client, conn)
    conn.close()
    if ok:
        print(f"{patent_no}: stored.")
    else:
        print(f"{patent_no}: not found on EPO.")


def cmd_citations(args: argparse.Namespace) -> None:
    from markery.specialist.patent.build import open_db
    from markery.specialist.patent.fetch import fetch_citation_chain
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials

    patent_no = validate_patent_no(args.patent_no)
    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    conn   = open_db()
    print(f"Fetching citations for {patent_no} ...")
    n = fetch_citation_chain(patent_no, client, conn)
    conn.close()
    print(f"{n} new patent(s) added.")


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
                         help="CPC class codes to fetch (required unless --seed-only)")
    p_build.add_argument("--resume", action="store_true",
                         help="Skip windows already in the fetch-log JSON")
    p_build.add_argument("--year-start", type=int, default=None, metavar="YEAR",
                         help="Start year for EPO query window (required unless --seed-only)")
    p_build.add_argument("--year-end",   type=int, default=None, metavar="YEAR",
                         help="End year for EPO query window (required unless --seed-only)")
    p_build.add_argument("--seed-path", metavar="FILE",
                         help="Path to a JSON file of seed patent records to insert")
    p_build.add_argument("--seed-only",  action="store_true",
                         help="Insert seed patents only, skip EPO fetch")

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch figures for patents in a project")
    p_fetch.add_argument("project", nargs="?", default=None)
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
    p_sig.add_argument("project", nargs="?", default=None)

    # pull
    p_pull = sub.add_parser("pull",
                             help="Fetch a single patent from EPO and upsert into patents.duckdb")
    p_pull.add_argument("patent_no", metavar="PATENT_NO",
                        help="Full patent number, e.g. US1261167A")

    # citations
    p_cit = sub.add_parser("citations",
                            help="Fetch backward citations for a patent; pull any new ones")
    p_cit.add_argument("patent_no", metavar="PATENT_NO")

    args = ap.parse_args()
    {
        "build":               cmd_build,
        "fetch":               cmd_fetch,
        "figures":             cmd_figures,
        "pull":                cmd_pull,
        "citations":           cmd_citations,
        "verify-credentials":  cmd_verify_credentials,
        "signals":             cmd_signals,
    }[args.cmd](args)
