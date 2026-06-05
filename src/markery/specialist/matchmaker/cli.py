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

from markery.common.config import DB
from markery.common.project import Project, require_project


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


def _run_status(rest: list[str]) -> None:
    """Entry point for `markery match status <project>`."""
    parser = argparse.ArgumentParser(
        prog="markery match status",
        description="Print pipeline and review state for a project",
    )
    parser.add_argument("project", help="Project name under projects/")
    args = parser.parse_args(rest)

    from markery.specialist.matchmaker.pipeline import read_state
    from markery.specialist.matchmaker.link import read_confirmed, read_rejected

    proj  = require_project(args.project)
    state = read_state(proj.pipeline_state)

    confirmed = read_confirmed(proj.confirmed)
    rejected  = read_rejected(proj.rejected)

    print(f"Project: {args.project}")
    if state:
        gen_at  = state.get("generated_at",  "never")
        enr_at  = state.get("enriched_at",   "never")
        rsc_at  = state.get("rescored_at",   "never")
        n_cands = state.get("candidate_count", 0) or 0
        p50     = state.get("score_p50", "-")
        p90     = state.get("score_p90", "-")
        enr_n   = state.get("enriched_count", "-")
        print(f"  Generated:   {gen_at}  ({n_cands} candidates, P50={p50}, P90={p90})")
        print(f"  Enriched:    {enr_at}  ({enr_n} signals)")
        print(f"  Rescored:    {rsc_at}")
    else:
        print("  No pipeline state found. Run 'markery match <project>' first.")

    n_conf = len(confirmed)
    n_rej  = len(rejected)
    n_cands = state.get("candidate_count", 0) or 0 if state else 0
    unreviewed = max(0, n_cands - n_conf - n_rej)
    print(f"  Confirmed:   {n_conf} pair(s)")
    print(f"  Rejected:    {n_rej} pair(s)")
    print(f"  Unreviewed:  {unreviewed} candidate(s)")


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

    proj = require_project(args.project)
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
    all_serials: bool = False,
) -> None:
    import json as _json
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

    pjson = proj.root / "project.json"
    focus_serials: set[int] = set()
    if not all_serials and pjson.exists():
        pdata = _json.loads(pjson.read_text(encoding="utf-8"))
        focus_serials = {int(s) for s in pdata.get("focus_serials", [])}

    entity_ids = entity_ids_for_project(proj.entities_file)
    if not entity_ids:
        print(f"No entities found at {proj.entities_file}.")
        print("Create it with one entity_id per line.")
        return

    print(f"Project: {project_name}")
    print(f"Entities in scope: {entity_ids}")

    candidates = generate_candidates(entity_ids, min_score=min_score)

    if focus_serials:
        before = len(candidates)
        candidates = [c for c in candidates if c["trademark_serial"] in focus_serials]
        print(f"  focus_serials filter: {before} → {len(candidates)} candidates "
              f"(use --all-serials to disable)")

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


def _run_auto_disposition(rest: list[str]) -> None:
    """Entry point for `markery match auto-disposition <project>`."""
    import json
    from datetime import date

    parser = argparse.ArgumentParser(
        prog="markery match auto-disposition",
        description="Deterministically reject below-floor candidates without model review",
    )
    parser.add_argument("project", help="Project name under projects/")
    parser.add_argument("--reject-below", type=float, default=None,
                        help="Reject candidates with score below this threshold")
    parser.add_argument("--max-gap-years", type=float, default=None,
                        help="Reject candidates where trademark filing exceeds this many years after patent grant")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be rejected without writing")
    args = parser.parse_args(rest)

    proj = require_project(args.project)
    if not proj.candidates.exists():
        print(f"No candidates.jsonl found. Run 'markery match {args.project}' first.", file=sys.stderr)
        sys.exit(1)

    # Load config from auto_disposition.json, then apply CLI overrides
    config_path = proj.root / "matches" / "auto_disposition.json"
    config: dict = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    reject_below  = args.reject_below  if args.reject_below  is not None else config.get("reject_below",  0.25)
    max_gap_years = args.max_gap_years if args.max_gap_years is not None else config.get("max_gap_years", 20.0)

    # Load existing rejections to skip already-rejected pairs
    from markery.specialist.matchmaker.link import read_rejected
    already_rejected: set[tuple] = read_rejected(proj.rejected) if proj.rejected.exists() else set()

    from markery.specialist.matchmaker.score import is_company_name_mark
    from markery.specialist.matchmaker.score import PRODUCT_CLASSES

    candidates = [json.loads(l) for l in proj.candidates.read_text().splitlines() if l.strip()]

    to_reject: list[tuple[dict, list[str]]] = []
    for c in candidates:
        key = (c["patent_no"], str(c["trademark_serial"]))
        if key in already_rejected:
            continue
        reasons: list[str] = []
        if c["score"] < reject_below:
            reasons.append(f"score {c['score']:.3f} < threshold {reject_below:.2f}")
        if not reasons:  # only check further rules if score passes
            grant_str  = c.get("patent_grant_dt", "")
            filing_str = c.get("tm_filing_dt", "")
            if grant_str and filing_str:
                try:
                    grant_dt  = date.fromisoformat(grant_str)
                    filing_dt = date.fromisoformat(filing_str)
                    gap_years = (filing_dt - grant_dt).days / 365.25
                    if gap_years > max_gap_years:
                        reasons.append(f"date gap {gap_years:.1f}y > ceiling {max_gap_years:.0f}y")
                except ValueError:
                    pass
            if not any(cls in PRODUCT_CLASSES for cls in c.get("cpc_classes", [])):
                reasons.append("no CPC class in product signal set")
            if is_company_name_mark(c.get("entity", ""), c.get("trademark", "")):
                reasons.append("mark is company name")
        if reasons:
            to_reject.append((c, reasons))

    if not to_reject:
        print(f"No candidates meet auto-disposition criteria (threshold {reject_below:.2f}, gap ceiling {max_gap_years:.0f}y).")
        return

    # Report
    print(f"{'Slug':<44}  {'Score':>6}  Reasons")
    print("-" * 80)
    for c, reasons in to_reject:
        slug = f"{c['trademark'][:20]}/{c['patent_no']}"
        print(f"  {slug:<42}  {c['score']:>6.3f}  {'; '.join(reasons)}")
    print(f"\n{len(to_reject)} candidate(s) would be rejected"
          + (" (dry run — nothing written)" if args.dry_run else "."))

    if args.dry_run:
        return

    # Write rejection records
    from markery.specialist.historian.review import write_rejected
    proj.rejected.parent.mkdir(parents=True, exist_ok=True)
    for c, reasons in to_reject:
        write_rejected(proj.rejected, {
            "patent_no":         c["patent_no"],
            "trademark_serial":  c["trademark_serial"],
            "trademark":         c["trademark"],
            "entity_id":         c["entity_id"],
            "entity":            c["entity"],
            "rejection_note":    "",
            "auto_rejected":     True,
            "rejection_reasons": reasons,
        })
    print(f"Written to {proj.rejected.relative_to(proj.root.parent.parent)}")


def _run_preflight(rest: list[str]) -> None:
    """Entry point for `markery match preflight <project>`."""
    import json
    from datetime import datetime, timezone

    parser = argparse.ArgumentParser(
        prog="markery match preflight",
        description="Pre-fetch all available enrichment before a model review session",
    )
    parser.add_argument("project", help="Project name under projects/")
    parser.add_argument("--min-score", type=float, default=0.40,
                        help="Minimum candidate score for signals enrichment (default: 0.40)")
    parser.add_argument("--tsdr-band-low",  type=float, default=0.40)
    parser.add_argument("--tsdr-band-high", type=float, default=0.60)
    args = parser.parse_args(rest)

    proj = require_project(args.project)

    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "signals":   {"fetched": 0, "already_present": 0, "skipped": 0},
        "tsdr":      {"fetched": 0, "already_present": 0, "skipped": 0, "quota_hit": 0},
        "images":    {"fetched": 0, "already_present": 0, "skipped": 0},
    }

    # ── Step 1: signals enrichment ────────────────────────────────────────────
    print("Step 1/3  Signals enrichment ...")
    if not proj.candidates.exists():
        print("  candidates.jsonl not found — skipping")
        report["signals"]["skipped"] = -1  # sentinel: no candidates file
    else:
        candidates = [json.loads(l) for l in proj.candidates.read_text().splitlines() if l.strip()]
        above_min  = [c for c in candidates if c.get("score", 0) >= args.min_score]
        already    = sum(1 for c in above_min if "title_name_hit" in c)
        needs      = len(above_min) - already
        report["signals"]["already_present"] = already
        if needs == 0:
            print(f"  {already} candidate(s) above {args.min_score} already enriched — nothing to do")
        else:
            print(f"  {needs} candidate(s) above {args.min_score} need signal enrichment ...")
            from markery.specialist.orchestrator import enrich_signal_fields
            n = enrich_signal_fields(proj.candidates)
            report["signals"]["fetched"] = n
            print(f"  {n} candidate(s) enriched")

    # ── Step 2: TSDR enrichment for uncertainty-band candidates ───────────────
    print(f"Step 2/3  TSDR enrichment (uncertainty band [{args.tsdr_band_low}, {args.tsdr_band_high}]) ...")
    if not proj.candidates.exists():
        report["tsdr"]["skipped"] = -1
    else:
        import duckdb as _duckdb
        from markery.common.config import DB
        candidates = [json.loads(l) for l in proj.candidates.read_text().splitlines() if l.strip()]
        band = [
            c for c in candidates
            if args.tsdr_band_low <= c.get("score", 0) < args.tsdr_band_high
        ]
        band_serials = list({str(c["trademark_serial"]) for c in band})
        if not band_serials:
            print("  No candidates in uncertainty band — skipping")
        else:
            conn_tm = _duckdb.connect(str(DB["trademarks"]), read_only=True)
            in_ext  = {
                str(r[0]) for r in conn_tm.execute(
                    f"SELECT serial_no FROM extended_marks WHERE serial_no IN ({','.join(band_serials)})"
                ).fetchall()
            }
            conn_tm.close()
            missing = [s for s in band_serials if s not in in_ext]
            report["tsdr"]["already_present"] = len(in_ext)
            print(f"  {len(in_ext)} already in extended_marks, {len(missing)} to fetch")
            from markery.specialist.orchestrator import fetch_trademark
            for sno in missing:
                try:
                    stored = fetch_trademark(sno)
                    if stored:
                        report["tsdr"]["fetched"] += 1
                    else:
                        report["tsdr"]["skipped"] += 1
                except Exception as exc:
                    msg = str(exc).lower()
                    if "quota" in msg or "429" in msg or "403" in msg:
                        report["tsdr"]["quota_hit"] += 1
                        print(f"  Quota hit on {sno} — stopping TSDR step")
                        break
                    report["tsdr"]["skipped"] += 1
            print(f"  TSDR: {report['tsdr']['fetched']} fetched, "
                  f"{report['tsdr']['skipped']} skipped, "
                  f"{report['tsdr']['quota_hit']} quota hits")

    # ── Step 3: mark images for confirmed pairs ───────────────────────────────
    print("Step 3/3  Mark images for confirmed pairs ...")
    if not proj.confirmed.exists():
        print("  confirmed.jsonl not found — skipping")
        report["images"]["skipped"] = -1
    else:
        import duckdb as _duckdb
        from markery.common.config import DB
        confirmed = [json.loads(l) for l in proj.confirmed.read_text().splitlines() if l.strip()]
        serials   = list({str(c["trademark_serial"]) for c in confirmed})
        if not serials:
            print("  No confirmed pairs — skipping")
        else:
            conn_tm = _duckdb.connect(str(DB["trademarks"]), read_only=True)
            in_img  = {
                str(r[0]) for r in conn_tm.execute(
                    f"SELECT DISTINCT serial_no FROM mark_images WHERE serial_no IN ({','.join(serials)})"
                ).fetchall()
            }
            conn_tm.close()
            missing = [s for s in serials if s not in in_img]
            report["images"]["already_present"] = len(in_img)
            print(f"  {len(in_img)} image(s) present, {len(missing)} to fetch")
            from markery.specialist.orchestrator import fetch_trademark
            for sno in missing:
                try:
                    stored = fetch_trademark(sno)
                    if stored:
                        report["images"]["fetched"] += 1
                    else:
                        report["images"]["skipped"] += 1
                except Exception as exc:
                    msg = str(exc).lower()
                    if "quota" in msg or "429" in msg or "403" in msg:
                        report["images"]["quota_hit"] = report["images"].get("quota_hit", 0) + 1
                        print(f"  Quota hit on {sno} — stopping images step")
                        break
                    report["images"]["skipped"] += 1
            print(f"  Images: {report['images']['fetched']} fetched, "
                  f"{report['images']['skipped']} skipped")

    # ── Write preflight.json ──────────────────────────────────────────────────
    preflight_path = proj.root / "matches" / "preflight.json"
    preflight_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nPreflight complete. Report written → {preflight_path.relative_to(proj.root.parent.parent)}")


def match_main() -> None:
    """Entry point for `markery match`."""
    # Dispatch `rescore` subcommand before the main parser sees it.
    rest = sys.argv[1:]
    if rest and rest[0] == "status":
        _run_status(rest[1:])
        return
    if rest and rest[0] == "rescore":
        _run_rescore(rest[1:])
        return
    if rest and rest[0] == "auto-disposition":
        _run_auto_disposition(rest[1:])
        return
    if rest and rest[0] == "preflight":
        _run_preflight(rest[1:])
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
    parser.add_argument("--all-serials", action="store_true",
                        help="Generate from all entity trademarks, ignoring focus_serials in project.json")
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
            all_serials=args.all_serials,
        )


# ---------------------------------------------------------------------------
# markery matchmaker
# ---------------------------------------------------------------------------

def cmd_suggest_variants(args: argparse.Namespace) -> None:
    import re
    import duckdb
    from markery.common.config import DB

    canonical = args.name
    top_n     = args.top

    _ABBREV = {
        r'\bINCORPORATED\b': 'INC',
        r'\bCORPORATION\b':  'CORP',
        r'\bCOMPANY\b':      'CO',
        r'\bLIMITED\b':      'LTD',
        r'\bMANUFACTURING\b':'MFG',
        r'\bBROTHERS\b':     'BROS',
    }
    _STRIP = re.compile(r'\b(INC\.?|CORP\.?|CO\.?|LTD\.?|MFG\.?|THE)\b|[,.]', re.I)

    def _normalise(s: str) -> str:
        s = s.upper()
        for pat, repl in _ABBREV.items():
            s = re.sub(pat, repl, s)
        s = _STRIP.sub(' ', s)
        return ' '.join(s.split())

    def _score(query_tokens: set[str], candidate: str) -> float:
        cand_tokens = set(_normalise(candidate).split())
        if not cand_tokens:
            return 0.0
        overlap = query_tokens & cand_tokens
        # Jaccard on normalised tokens
        return len(overlap) / len(query_tokens | cand_tokens)

    query_tokens = set(_normalise(canonical).split())

    # Patent assignees
    conn_pat = duckdb.connect(str(DB["patents"]), read_only=True)
    pat_rows = conn_pat.execute(
        "SELECT assignee_name, COUNT(*) AS n FROM patents "
        "WHERE assignee_name IS NOT NULL AND assignee_name != '' "
        "GROUP BY assignee_name ORDER BY n DESC"
    ).fetchall()
    conn_pat.close()

    # Trademark owners
    conn_tm = duckdb.connect(str(DB["trademarks"]), read_only=True)
    tm_rows = conn_tm.execute(
        "SELECT own_name, COUNT(*) AS n FROM owner "
        "WHERE own_name IS NOT NULL AND own_name != '' "
        "GROUP BY own_name ORDER BY n DESC"
    ).fetchall()
    conn_tm.close()

    def _rank(rows: list[tuple], min_score: float = 0.3) -> list[tuple]:
        scored = [
            (name, count, _score(query_tokens, name))
            for name, count in rows
        ]
        return sorted(
            [(n, c, s) for n, c, s in scored if s >= min_score],
            key=lambda x: (-x[2], -x[1]),
        )[:top_n]

    pat_ranked = _rank(pat_rows)
    tm_ranked  = _rank(tm_rows)

    print(f"Variant suggestions for: {canonical!r}\n")
    print("Patent assignees:")
    if pat_ranked:
        for name, count, score in pat_ranked:
            print(f"  {score:.2f}  {count:>5}×  {name}")
    else:
        print("  (none above threshold)")

    print("\nTrademark owners:")
    if tm_ranked:
        for name, count, score in tm_ranked:
            print(f"  {score:.2f}  {count:>5}×  {name}")
    else:
        print("  (none above threshold)")


def cmd_validate_variants(args: argparse.Namespace) -> None:
    """Check every patent_assignee and trademark_owner variant against actual DB strings."""
    import duckdb
    from markery.common.config import DB
    from markery.specialist.matchmaker.entities import _read_csv

    data_dir = Path(args.data_dir)
    entities = {int(r["entity_id"]): r["canonical_name"]
                for r in _read_csv(data_dir / "entities.csv")}
    variants = _read_csv(data_dir / "variants.csv")

    conn_pat = duckdb.connect(str(DB["patents"]), read_only=True)
    conn_tm  = duckdb.connect(str(DB["trademarks"]), read_only=True)

    zero_matches = 0
    for eid in sorted(entities):
        name = entities[eid]
        eid_variants = [v for v in variants if int(v["entity_id"]) == eid]
        actionable = [v for v in eid_variants if v["source"] in ("patent_assignee", "trademark_owner")]
        if not actionable:
            continue
        print(f"\nEntity {eid}: {name}")
        for v in actionable:
            vname, source = v["variant_name"], v["source"]
            if source == "patent_assignee":
                cnt = conn_pat.execute(
                    "SELECT COUNT(*) FROM patents WHERE assignee_name = ?", [vname]
                ).fetchone()[0]
            else:
                cnt = conn_tm.execute(
                    "SELECT COUNT(DISTINCT serial_no) FROM owner WHERE own_name = ?", [vname]
                ).fetchone()[0]
            flag = "  *** NO MATCH ***" if cnt == 0 else ""
            label = "patent  " if source == "patent_assignee" else "trademark"
            print(f"  {label}  {cnt:>6}×  {vname}{flag}")
            if cnt == 0:
                zero_matches += 1

    conn_pat.close()
    conn_tm.close()

    print()
    if zero_matches == 0:
        print(f"All variants matched. ({len(variants)} total)")
    else:
        print(f"{zero_matches} zero-match variant(s) found.")
        print("  → run: markery matchmaker suggest-variants \"<entity name>\"")
        sys.exit(1)


def cmd_build(args: argparse.Namespace) -> None:
    from markery.specialist.matchmaker.entities import build
    try:
        counts = build(data_dir=args.data_dir)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
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

    p_build_ent = sub.add_parser("build",  help="Insert entities/variants from CSV (idempotent)")
    p_build_ent.add_argument("--data-dir", metavar="DIR", required=True,
                             help="Directory containing entities.csv and variants.csv")
    sub.add_parser("list",   help="List all entities with IDs and names")
    sub.add_parser("status", help="Row counts for entity registry tables")
    p_sv = sub.add_parser("suggest-variants",
                          help="Rank patent assignee and trademark owner strings matching a canonical name")
    p_sv.add_argument("name", help="Canonical entity name to match against")
    p_sv.add_argument("--top", type=int, default=15, metavar="N",
                      help="Return top N results per source (default: 15)")

    p_vv = sub.add_parser("validate-variants",
                          help="Check every patent_assignee and trademark_owner variant against actual DB strings")
    p_vv.add_argument("--data-dir", metavar="DIR", required=True,
                      help="Directory containing entities.csv and variants.csv")

    args = ap.parse_args()
    {
        "build":              cmd_build,
        "list":               cmd_list,
        "status":             cmd_status,
        "suggest-variants":   cmd_suggest_variants,
        "validate-variants":  cmd_validate_variants,
    }[args.cmd](args)
