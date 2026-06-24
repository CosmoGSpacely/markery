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


def cmd_search(args: argparse.Namespace) -> None:
    """Search the local patents.duckdb by assignee substring (case-insensitive).

    Closes the P5 gap where checking 'is there a Mack assignee in the corpus?'
    required a raw DuckDB query — this surfaces local-DB assignee reads via the CLI.
    """
    import duckdb

    conn = duckdb.connect(str(DB["patents"]), read_only=True)
    pattern = f"%{args.assignee}%"
    rows = conn.execute(
        "SELECT assignee_name, COUNT(*) AS n "
        "FROM patents "
        "WHERE assignee_name IS NOT NULL AND assignee_name != '' "
        "  AND assignee_name ILIKE ? "
        "GROUP BY assignee_name ORDER BY n DESC, assignee_name",
        [pattern],
    ).fetchall()

    if not rows:
        print(f"No assignees matching '{args.assignee}' in patents.duckdb.")
        conn.close()
        return

    print(f"Assignees matching '{args.assignee}' ({len(rows)} distinct):\n")
    for name, n in rows:
        print(f"  {n:>5}×  {name}")
        if args.examples:
            examples = conn.execute(
                "SELECT patent_no, title, YEAR(grant_dt) FROM patents "
                "WHERE assignee_name = ? AND title IS NOT NULL "
                "ORDER BY grant_dt LIMIT ?",
                [name, args.examples],
            ).fetchall()
            for pno, title, year in examples:
                yr = f" ({year})" if year else ""
                print(f"          {pno}  {title}{yr}")
    conn.close()


def cmd_coverage_check(args: argparse.Namespace) -> None:
    """Query EPO OPS for expected record counts before committing to a full sweep."""
    from markery.specialist.patent.build import _cql
    from markery.specialist.patent.epo_client import EPOClient
    from markery.common.auth import load_epo_credentials

    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)

    window_years = 5
    print(f"Coverage check: {', '.join(args.classes)}  {args.year_start}–{args.year_end}\n")
    any_nonzero = False
    for cls in args.classes:
        total_class = 0
        windows = range(args.year_start, args.year_end + 1, window_years)
        for ys in windows:
            ye = min(ys + window_years - 1, args.year_end)
            cql = _cql(cls, ys, ye)
            try:
                total, _ = client.search(cql, 1, 1)
                mark = "" if total > 0 else "  (no coverage)"
                print(f"  {cls}  {ys}–{ye}:  {total:>6}{mark}")
                total_class += total
                if total > 0:
                    any_nonzero = True
            except Exception as exc:
                print(f"  {cls}  {ys}–{ye}:  ERROR — {exc}")
        print(f"  {cls}  total: {total_class}\n")

    if not any_nonzero:
        print("WARNING: all classes returned 0 results.")
        print("CPC reclassification may be incomplete for this era.")
        print("Consider: markery patent pull <patent_no> for known patents,")
        print("          or D007 (PatentsView) for 1976+ coverage.")
        sys.exit(1)


def cmd_coverage(args: argparse.Namespace) -> None:
    """Print the local patents-corpus manifest, or query one class×year slice."""
    import duckdb
    from markery.common.config import require_db
    from markery.common.coverage import patent_coverage, format_coverage, coverage_query
    from markery.specialist.patent.build import _fetch_log_path, _load_fetch_log

    db_path = require_db("patents")

    # Query mode: answer the loop's "is this class×year covered?" question.
    if args.cpc_class:
        if args.year_start is None or args.year_end is None:
            print("--class requires --year-start and --year-end.", file=sys.stderr)
            sys.exit(1)
        q = coverage_query(db_path, args.cpc_class, args.year_start, args.year_end)
        print(f"coverage: {args.cpc_class}  {args.year_start}–{args.year_end}")
        print(f"  fully covered: {'yes' if q['covered'] else 'no'}")
        print(f"  local patents: {q['local_count']:,}")
        if q["missing_spans"]:
            spans = ", ".join(f"{a}–{b}" for a, b in q["missing_spans"])
            print(f"  missing windows to fetch: {spans}")
        else:
            print("  missing windows to fetch: none")
        return

    windows = len(_load_fetch_log(_fetch_log_path(str(db_path))))
    conn = duckdb.connect(str(db_path), read_only=True)
    cov = patent_coverage(conn, fetch_log_windows=windows)
    conn.close()
    print(format_coverage("patent", cov))


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

    # search
    p_search = sub.add_parser("search",
                              help="Search local patents.duckdb (e.g. by assignee substring)")
    p_search.add_argument("--assignee", required=True, metavar="SUBSTR",
                          help="Case-insensitive substring to match against assignee_name")
    p_search.add_argument("--examples", type=int, default=0, metavar="N",
                          help="Show up to N example patents per assignee (default: 0)")

    # coverage-check
    p_cov = sub.add_parser(
        "coverage-check",
        help="Dry-run: query EPO OPS for expected record counts before a full sweep",
    )
    p_cov.add_argument("--classes", nargs="+", metavar="CPC", required=True,
                       help="CPC class codes to check")
    p_cov.add_argument("--year-start", type=int, required=True, metavar="YEAR")
    p_cov.add_argument("--year-end",   type=int, required=True, metavar="YEAR")

    # coverage (local manifest; or a class×year query the loops consult)
    p_lcov = sub.add_parser(
        "coverage",
        help="Local corpus coverage + freshness manifest (what's loaded, how fresh)",
    )
    p_lcov.add_argument("--class", dest="cpc_class", metavar="CPC", default=None,
                        help="Query coverage for one CPC class (with --year-start/--year-end)")
    p_lcov.add_argument("--year-start", type=int, default=None, metavar="YEAR")
    p_lcov.add_argument("--year-end", type=int, default=None, metavar="YEAR")

    args = ap.parse_args()
    {
        "build":               cmd_build,
        "fetch":               cmd_fetch,
        "figures":             cmd_figures,
        "pull":                cmd_pull,
        "citations":           cmd_citations,
        "verify-credentials":  cmd_verify_credentials,
        "signals":             cmd_signals,
        "search":              cmd_search,
        "coverage-check":      cmd_coverage_check,
        "coverage":            cmd_coverage,
    }[args.cmd](args)
