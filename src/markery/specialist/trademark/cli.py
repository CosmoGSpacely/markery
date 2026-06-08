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

from markery.common.project import require_project, validate_serial_no


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

    serial_no = validate_serial_no(args.serial_no)
    client = TSDRClient(load_tsdr_key())
    conn   = open_db()

    img_ok = store_mark_image(serial_no, client, conn, force=args.force)
    sts_ok = store_case_status(serial_no, client, conn, force=args.force)
    conn.close()

    print(f"{serial_no}: image={'stored' if img_ok else 'skipped'}  "
          f"status={'stored' if sts_ok else 'skipped'}")


def cmd_enrich_project(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db
    from markery.specialist.trademark.enrich import enrich_project
    from markery.specialist.trademark.tsdr_client import TSDRClient
    from markery.common.auth import load_tsdr_key
    proj = require_project(args.project)

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


def cmd_load_events(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db, load_events
    conn = open_db()
    try:
        n = load_events(args.csv_dir, conn)
    finally:
        conn.close()
    print(f"events: {n:,} rows loaded.")


def cmd_load_foreign(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db, load_foreign_app
    conn = open_db()
    try:
        n = load_foreign_app(args.csv_dir, conn)
    finally:
        conn.close()
    print(f"foreign_app: {n:,} rows loaded.")


def cmd_fetch(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db
    from markery.specialist.trademark.fetch import fetch_mark_record
    from markery.specialist.trademark.tsdr_client import TSDRClient
    from markery.common.auth import load_tsdr_key

    serial_no = validate_serial_no(args.serial_no)
    client = TSDRClient(load_tsdr_key())
    conn   = open_db()
    ok = fetch_mark_record(serial_no, client, conn, force=args.force)
    conn.close()
    if ok:
        print(f"{serial_no}: stored in extended_marks.")
    else:
        print(f"{serial_no}: not found on TSDR (or already stored; use --force to re-fetch).")


def cmd_entity_forward(args: argparse.Namespace) -> None:
    from markery.specialist.orchestrator import entity_forward_report

    rows = entity_forward_report(args.entity, after_year=args.after_year)
    if not rows:
        print(f"No extended marks found for '{args.entity}' filed after {args.after_year}.")
        return
    print(f"Post-{args.after_year} marks for '{args.entity}':")
    print(f"  {'Serial':<12}  {'Filed':<12}  {'Mark':<30}  Status")
    print("  " + "-" * 72)
    for r in rows:
        filing = str(r["filing_dt"])[:10] if r["filing_dt"] else "unknown"
        mark   = (r["mark_text"] or "")[:30]
        status = r["status_cd"] or ""
        print(f"  {r['serial_no']:<12}  {filing:<12}  {mark:<30}  {status}")


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


def cmd_load_assignment(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db, load_assignment
    conn = open_db()
    try:
        n = load_assignment(args.file, conn)
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)
    finally:
        conn.close()
    print(f"assignment: {n:,} rows loaded.")


def cmd_mark_status(args: argparse.Namespace) -> None:
    import csv as _csv
    import duckdb
    from markery.common.config import DB
    from markery.common.project import require_project
    from markery.specialist.trademark.queries import mark_status_report

    proj = require_project(args.project)
    variants_path = proj.root / "variants.csv"
    if not variants_path.exists():
        print(f"No variants.csv found at {variants_path}.", file=sys.stderr)
        sys.exit(1)

    with variants_path.open(newline="", encoding="utf-8") as f:
        rows = list(_csv.DictReader(f))
    tm_variants = list({
        r["variant_name"] for r in rows
        if r.get("source") in ("trademark_owner", "trademark_search")
    })
    if not tm_variants:
        print("No trademark_owner or trademark_search variants found in variants.csv.")
        return

    conn = duckdb.connect(str(DB["trademarks"]), read_only=True)
    results = mark_status_report(
        conn, tm_variants,
        dead_only=args.dead_only,
        pd_only=args.pd_only,
    )
    conn.close()

    if not results:
        print("No marks match the specified filters.")
        return

    hdr = (
        f"{'serial_no':<12}  {'mark_text':<35}  "
        f"{'filing_dt':<12}  {'status_cd':<10}  {'live_dead':<6}  public_domain"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in results:
        print(
            f"  {r['serial_no']:<12}  {(r['mark_text'] or '')[:35]:<35}  "
            f"{(r['filing_dt'] or ''):<12}  {(r['status_cd'] or ''):<10}  "
            f"{r['live_dead']:<6}  {'yes' if r['public_domain'] else 'no'}"
        )
    print(f"\n{len(results)} mark(s).")


def cmd_design_search(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db
    from markery.specialist.trademark.queries import search_by_design_code

    conn = open_db()
    try:
        rows = search_by_design_code(
            conn,
            code_prefix=args.code_prefix,
            filing_before=args.filing_before,
            goods_contains=args.goods_contains,
            limit=args.limit,
        )
    finally:
        conn.close()

    if not rows:
        print("No marks found.")
        return

    print(f"{'serial_no':<12}  {'mark_text':<35}  {'own_name':<30}  {'filing_dt':<12}  goods_desc")
    print("-" * 115)
    for r in rows:
        mark   = (r["mark_text"] or "")[:35]
        owner  = (r["own_name"]  or "")[:30]
        filing = r["filing_dt"] or ""
        goods  = (r["goods_desc"] or "")[:50]
        print(f"  {r['serial_no']:<12}  {mark:<35}  {owner:<30}  {filing:<12}  {goods}")
    print(f"\n{len(rows)} row(s).")


def cmd_reparse(args: argparse.Namespace) -> None:
    from markery.specialist.trademark.build import open_db
    from markery.specialist.trademark.enrich import backfill_structured_fields
    conn = open_db()
    n = backfill_structured_fields(conn)
    conn.close()
    print(f"Reparsed {n} extended_marks row(s).")


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
    p_build.add_argument("--date-start", default=None, metavar="DATE",
                         help="Filter case_file to filing_dt >= DATE (omit for full dataset)")
    p_build.add_argument("--date-end",   default=None, metavar="DATE",
                         help="Filter case_file to filing_dt <= DATE (omit for full dataset)")

    # enrich
    p_enrich = sub.add_parser("enrich",
                               help="Fetch TSDR image and status for one mark")
    p_enrich.add_argument("serial_no", metavar="SERIAL_NO")
    p_enrich.add_argument("--force", action="store_true",
                          help="Re-fetch even if already stored")

    # enrich-project
    p_ep = sub.add_parser("enrich-project",
                           help="Enrich all marks in a project")
    p_ep.add_argument("project", nargs="?", default=None)
    p_ep.add_argument("--source", choices=["confirmed", "candidates"],
                      default="confirmed",
                      help="Source file to read serial numbers from (default: confirmed)")
    p_ep.add_argument("--min-score", type=float, default=0.0,
                      help="Minimum score when using candidates (default: 0.0)")
    p_ep.add_argument("--force", action="store_true",
                      help="Re-fetch even if already stored")

    # load-events
    p_lev = sub.add_parser("load-events",
                            help="Load event.csv into the events table")
    p_lev.add_argument("--csv-dir", metavar="DIR", required=True,
                       help="Path to CSV directory containing event.csv")

    # load-foreign
    p_lfa = sub.add_parser("load-foreign",
                            help="Load foreign_application.csv into the foreign_app table")
    p_lfa.add_argument("--csv-dir", metavar="DIR", required=True,
                       help="Path to CSV directory containing foreign_application.csv")

    # fetch
    p_fetch = sub.add_parser("fetch",
                              help="Fetch a post-1939 or extended mark from TSDR into extended_marks")
    p_fetch.add_argument("serial_no", metavar="SERIAL_NO")
    p_fetch.add_argument("--force", action="store_true",
                         help="Re-fetch even if already stored")

    # entity-forward
    p_ef = sub.add_parser("entity-forward",
                           help="List post-1939 extended marks for a named entity")
    p_ef.add_argument("entity", metavar="ENTITY_NAME",
                      help="Canonical entity name (e.g. 'Remington Rand')")
    p_ef.add_argument("--after-year", type=int, default=1939, metavar="YEAR",
                      help="Show marks filed after this year (default: 1939)")

    # mark-status
    p_ms = sub.add_parser("mark-status",
                          help="Report live/dead and public-domain status for project-scope trademarks")
    p_ms.add_argument("project", metavar="PROJECT",
                      help="Project name under projects/")
    p_ms.add_argument("--dead-only", action="store_true",
                      help="Show only dead marks (cfh_status_cd >= 700)")
    p_ms.add_argument("--pd-only", action="store_true",
                      help="Show only marks with filing_dt year <= current year - 95")

    # load-assignment
    p_las = sub.add_parser("load-assignment",
                           help="Load an assignment CSV into the assignment table")
    p_las.add_argument("--file", metavar="PATH", required=True,
                       help="Path to assignment CSV file")

    # design-search
    p_ds = sub.add_parser("design-search",
                          help="Discover marks by USPTO visual design code prefix")
    p_ds.add_argument("code_prefix", metavar="CODE_PREFIX",
                      help="Design code prefix (e.g. '03' for animals, '01' for celestial)")
    p_ds.add_argument("--filing-before", metavar="YEAR", default=None,
                      help="Restrict to filing_dt before YEAR-01-01")
    p_ds.add_argument("--goods-contains", metavar="TEXT", default=None,
                      help="Case-insensitive substring filter on goods/services description")
    p_ds.add_argument("--limit", type=int, default=200, metavar="N",
                      help="Maximum rows returned (default: 200)")

    # reparse
    sub.add_parser("reparse",
                   help="Re-parse stored raw_json to fill NULL structured fields (no API calls)")

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
        "load-events":         cmd_load_events,
        "load-foreign":        cmd_load_foreign,
        "fetch":               cmd_fetch,
        "entity-forward":      cmd_entity_forward,
        "mark-status":         cmd_mark_status,
        "load-assignment":     cmd_load_assignment,
        "design-search":       cmd_design_search,
        "reparse":             cmd_reparse,
        "verify-credentials":  cmd_verify_credentials,
        "status":              cmd_status,
    }[args.cmd](args)
