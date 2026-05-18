"""CLI for the TRADEMARK specialist.

Registered as: markery trademark <subcommand>

Subcommands:
  build              Rebuild trademarks.duckdb from CSV source files
  enrich             Fetch TSDR image and status for one serial number
  enrich-project     Enrich all marks in a project's confirmed/candidates file
  verify-credentials Verify USPTO API key with a live TSDR request
  status             Print row counts for all trademark tables
"""

from __future__ import annotations

import argparse
import sys


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_build(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import build

    try:
        counts = build(
            csv_dir    = args.csv_dir or None,
            date_start = args.date_start,
            date_end   = args.date_end,
        )
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)

    total = sum(counts.values())
    print(f"\nDone. {total:,} rows across {len(counts)} tables.")


def cmd_enrich(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db
    from markery.specialist.trademark.enrich import store_mark_image, store_case_status
    from markery.specialist.trademark.tsdr_client import TSDRClient
    from markery.common.auth import load_tsdr_key

    client = TSDRClient(load_tsdr_key())
    conn   = open_db()

    img_ok = store_mark_image(args.serial_no, client, conn, force=args.force)
    sts_ok = store_case_status(args.serial_no, client, conn, force=args.force)
    conn.close()

    print(f"{args.serial_no}: image={'stored' if img_ok else 'skipped'}  "
          f"status={'stored' if sts_ok else 'skipped'}")


def cmd_enrich_project(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db
    from markery.specialist.trademark.enrich import enrich_project
    from markery.specialist.trademark.tsdr_client import TSDRClient
    from markery.common.auth import load_tsdr_key
    from markery.common.config import Project

    proj = Project(args.project)
    if not proj.exists():
        print(f"Project not found: {proj.root}")
        sys.exit(1)

    client = TSDRClient(load_tsdr_key())
    conn   = open_db()

    print(f"Enriching marks from '{args.project}' ({args.source}) ...")
    result = enrich_project(
        project   = args.project,
        client    = client,
        conn      = conn,
        source    = args.source,
        min_score = args.min_score,
        force     = args.force,
    )
    conn.close()
    print(f"\n{result['images']} image(s) stored, {result['status']} status record(s) stored.")


def cmd_verify_credentials(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.tsdr_client import TSDRClient
    from markery.common.auth import load_tsdr_key

    client = TSDRClient(load_tsdr_key())
    try:
        info = client.verify_credentials()
        print(f"API key: {info['api_key_prefix']}")
        print(f"Status:  {info['status_code']}")
        print("USPTO TSDR credentials OK.")
    except Exception as e:
        print(f"Credential check failed: {e}")
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db

    conn = open_db()
    tables = [
        r[0] for r in conn.execute("SHOW TABLES").fetchall()
    ]
    print("trademarks.duckdb:")
    for t in sorted(tables):
        n = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t:<25} {n:>8,}")
    conn.close()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        prog="markery trademark",
        description="TRADEMARK specialist: build, enrich, and query trademarks.duckdb",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    # build
    p_build = sub.add_parser("build",
                              help="Rebuild trademarks.duckdb from CSV source files")
    p_build.add_argument("--csv-dir", metavar="DIR",
                         help="Path to CSV directory (default: csv/)")
    p_build.add_argument("--date-start", default="1900-01-01", metavar="DATE")
    p_build.add_argument("--date-end",   default="1939-12-31", metavar="DATE")

    # enrich
    p_enrich = sub.add_parser("enrich",
                               help="Fetch TSDR image and status for one mark")
    p_enrich.add_argument("serial_no", metavar="SERIAL_NO")
    p_enrich.add_argument("--force", action="store_true",
                          help="Re-fetch even if already stored")

    # enrich-project
    p_ep = sub.add_parser("enrich-project",
                           help="Enrich all marks in a project")
    p_ep.add_argument("project", nargs="?", default="information-systems")
    p_ep.add_argument("--source", choices=["confirmed", "candidates"],
                      default="confirmed",
                      help="Source file to read serial numbers from (default: confirmed)")
    p_ep.add_argument("--min-score", type=float, default=0.0,
                      help="Minimum score when using candidates (default: 0.0)")
    p_ep.add_argument("--force", action="store_true",
                      help="Re-fetch even if already stored")

    # verify-credentials
    sub.add_parser("verify-credentials",
                   help="Verify USPTO API key with a live TSDR request")

    # status
    sub.add_parser("status", help="Print row counts for all trademark tables")

    args = ap.parse_args()
    {
        "build":               cmd_build,
        "enrich":              cmd_enrich,
        "enrich-project":      cmd_enrich_project,
        "verify-credentials":  cmd_verify_credentials,
        "status":              cmd_status,
    }[args.cmd](args)
