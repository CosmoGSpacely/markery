"""CLI for project management commands.

Commands:
    markery project init [name]      — scaffold a new project directory
    markery project adopt <name>     — declare the type of an existing project
    markery project onboard <name>   — run full pre-match validation checklist
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markery.common.config import ROOT
from markery.common.project import ProjectType, detect_project_type, load_project, scaffold_project


_TYPE_CHOICES = list(ProjectType)


def _prompt_name() -> str:
    name = input("Project name (directory under projects/): ").strip()
    if not name:
        print("Project name cannot be empty.", file=sys.stderr)
        sys.exit(1)
    return name


def _prompt_type() -> ProjectType:
    print("\nProject type:")
    for i, pt in enumerate(_TYPE_CHOICES, 1):
        print(f"  {i}) {pt.value}")
    raw = input("Select [1]: ").strip() or "1"
    try:
        idx = int(raw) - 1
        if not (0 <= idx < len(_TYPE_CHOICES)):
            raise ValueError
    except ValueError:
        print(f"Invalid selection '{raw}'.", file=sys.stderr)
        sys.exit(1)
    return _TYPE_CHOICES[idx]


def cmd_init(name: str | None, ptype: str | None = None) -> None:
    if not name:
        name = _prompt_name()

    project_root = ROOT / "projects" / name

    if (project_root / "project.json").exists():
        print(
            f"Project '{name}' already has a project.json at {project_root}.\n"
            "Use 'markery project adopt' to update an existing project's type.",
            file=sys.stderr,
        )
        sys.exit(1)

    project_type = ProjectType(ptype) if ptype else _prompt_type()

    try:
        created = scaffold_project(project_root, project_type)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print(f"\nScaffolded '{name}' ({project_type.value}):")
    for p in created:
        rel = p.relative_to(ROOT)
        suffix = "/" if p.is_dir() else ""
        print(f"  {rel}{suffix}")
    print(f"\nNext: cd into projects/{name} and start filling in the files.")


def cmd_adopt(name: str) -> None:
    project_root = ROOT / "projects" / name

    if not project_root.is_dir():
        print(f"No directory found at {project_root}.", file=sys.stderr)
        sys.exit(1)

    detected = detect_project_type(project_root)
    if detected is not None:
        print(f"Detected type: {detected.value}")
        confirm = input(f"Write project.json with type '{detected.value}'? [Y/n] ").strip().lower()
        if confirm not in ("", "y"):
            project_type = _prompt_type()
        else:
            project_type = detected
    else:
        print("Could not detect project type from directory structure.")
        project_type = _prompt_type()

    json_path = project_root / "project.json"
    import json
    json_path.write_text(json.dumps({"type": project_type.value}, indent=2) + "\n", encoding="utf-8")
    print(f"Written: {json_path.relative_to(ROOT)}")


def cmd_onboard(args: argparse.Namespace) -> None:
    """Run the full pre-match onboarding checklist for a project.

    Steps:
      1  Entity ID uniqueness   — no ID collision with another project in entities.duckdb
      2  Variant suggestions    — informational top-5 per entity (never fails)
      3  Variant validation     — all patent_assignee/trademark_owner variants match DB
      4  Coverage counts        — patent and trademark totals per entity
      5  Patent coverage        — at least one local patent per entity (or no variants)
    """
    import duckdb

    from markery.common.config import DB
    from markery.specialist.matchmaker.entities import _read_csv

    name = args.project
    proj_root = ROOT / "projects" / name

    for fname in ("entities.csv", "variants.csv"):
        if not (proj_root / fname).exists():
            print(
                f"  {fname} not found at {proj_root / fname}.\n"
                "  Run 'markery project init' first.",
                file=sys.stderr,
            )
            sys.exit(1)

    entities = {
        int(r["entity_id"]): r["canonical_name"]
        for r in _read_csv(proj_root / "entities.csv")
    }
    variants = _read_csv(proj_root / "variants.csv")

    # Load project.json for class_hints (may not exist yet)
    class_hints: list[str] = []
    proj_json = proj_root / "project.json"
    if proj_json.exists():
        import json
        raw = json.loads(proj_json.read_text())
        class_hints = raw.get("class_hints", [])

    failed: list[str] = []

    print(f"\n=== Onboarding: {name} ===\n")

    # ------------------------------------------------------------------
    # Step 1 — Entity ID uniqueness
    # ------------------------------------------------------------------
    print("Step 1 — Entity ID uniqueness")
    conn_ent = duckdb.connect(str(DB["entities"]), read_only=True)
    conflicts: list[str] = []
    for eid, canonical in entities.items():
        row = conn_ent.execute(
            "SELECT canonical_name FROM company_entity WHERE entity_id = ?", [eid]
        ).fetchone()
        if row and row[0] != canonical:
            conflicts.append(
                f"  entity_id={eid}: local={canonical!r}, DB={row[0]!r}"
            )
    conn_ent.close()
    if conflicts:
        print("  FAIL — ID conflict(s) with entities already in entities.duckdb:")
        for c in conflicts:
            print(c)
        print("  → Change entity IDs in entities.csv to avoid collisions.")
        failed.append("entity-id-uniqueness")
    else:
        print(f"  PASS — {len(entities)} entity ID(s) are unique")

    # ------------------------------------------------------------------
    # Step 2 — Variant suggestions (informational)
    # ------------------------------------------------------------------
    print("\nStep 2 — Variant suggestions (informational)")
    import re

    _ABBREV = {
        r'\bINCORPORATED\b': 'INC', r'\bCORPORATION\b': 'CORP',
        r'\bCOMPANY\b': 'CO',      r'\bLIMITED\b': 'LTD',
        r'\bMANUFACTURING\b': 'MFG', r'\bBROTHERS\b': 'BROS',
    }
    _STRIP = re.compile(r'\b(INC\.?|CORP\.?|CO\.?|LTD\.?|MFG\.?|THE)\b|[,.]', re.I)

    def _norm(s: str) -> str:
        s = s.upper()
        for pat, repl in _ABBREV.items():
            s = re.sub(pat, repl, s)
        return ' '.join(_STRIP.sub(' ', s).split())

    def _score(qt: set[str], cand: str) -> float:
        ct = set(_norm(cand).split())
        return len(qt & ct) / len(qt | ct) if ct else 0.0

    conn_pat = duckdb.connect(str(DB["patents"]), read_only=True)
    conn_tm  = duckdb.connect(str(DB["trademarks"]), read_only=True)
    pat_rows = conn_pat.execute(
        "SELECT assignee_name, COUNT(*) AS n FROM patents "
        "WHERE assignee_name IS NOT NULL AND assignee_name != '' "
        "GROUP BY assignee_name"
    ).fetchall()
    tm_rows = conn_tm.execute(
        "SELECT own_name, COUNT(*) AS n FROM owner "
        "WHERE own_name IS NOT NULL AND own_name != '' "
        "GROUP BY own_name"
    ).fetchall()

    for eid in sorted(entities):
        canonical = entities[eid]
        qt = set(_norm(canonical).split())
        top_pat = sorted(
            [(n, c, _score(qt, n)) for n, c in pat_rows if _score(qt, n) >= 0.3],
            key=lambda x: (-x[2], -x[1]),
        )[:5]
        top_tm = sorted(
            [(n, c, _score(qt, n)) for n, c in tm_rows if _score(qt, n) >= 0.3],
            key=lambda x: (-x[2], -x[1]),
        )[:5]
        print(f"  {canonical}:")
        if top_pat:
            for n, c, s in top_pat:
                print(f"    patent    {s:.2f}  {c:>5}×  {n}")
        else:
            print("    patent    (none above threshold)")
        if top_tm:
            for n, c, s in top_tm:
                print(f"    trademark {s:.2f}  {c:>5}×  {n}")
        else:
            print("    trademark (none above threshold)")

    # ------------------------------------------------------------------
    # Step 3 — Variant validation
    # ------------------------------------------------------------------
    print("\nStep 3 — Variant validation")
    actionable = [v for v in variants if v["source"] in ("patent_assignee", "trademark_owner")]
    zero_matches = 0
    for eid in sorted(entities):
        ev = [v for v in actionable if int(v["entity_id"]) == eid]
        if not ev:
            print(f"  {entities[eid]}: no patent_assignee/trademark_owner variants")
            continue
        for v in ev:
            vname, source = v["variant_name"], v["source"]
            if source == "patent_assignee":
                cnt = conn_pat.execute(
                    "SELECT COUNT(*) FROM patents WHERE assignee_name = ?", [vname]
                ).fetchone()[0]
                label = "patent  "
            else:
                cnt = conn_tm.execute(
                    "SELECT COUNT(DISTINCT serial_no) FROM owner WHERE own_name = ?", [vname]
                ).fetchone()[0]
                label = "trademark"
            flag = "  *** NO MATCH ***" if cnt == 0 else ""
            print(f"  {entities[eid][:28]:<28}  {label}  {cnt:>6}×  {vname}{flag}")
            if cnt == 0:
                zero_matches += 1

    if zero_matches:
        print(f"  FAIL — {zero_matches} zero-match variant(s). Run 'markery matchmaker suggest-variants' to find correct names.")
        failed.append("variant-validation")
    else:
        print(f"  PASS — all {len(actionable)} variant(s) matched")

    # ------------------------------------------------------------------
    # Step 4 — Coverage counts
    # ------------------------------------------------------------------
    print("\nStep 4 — Coverage counts")
    pat_variants = [v for v in variants if v["source"] == "patent_assignee"]
    tm_variants  = [v for v in variants if v["source"] == "trademark_owner"]

    for eid in sorted(entities):
        canonical = entities[eid]
        pv_names = [v["variant_name"] for v in pat_variants if int(v["entity_id"]) == eid]
        tv_names = [v["variant_name"] for v in tm_variants  if int(v["entity_id"]) == eid]
        pat_total = sum(
            conn_pat.execute("SELECT COUNT(*) FROM patents WHERE assignee_name = ?", [n]).fetchone()[0]
            for n in pv_names
        )
        tm_total = sum(
            conn_tm.execute("SELECT COUNT(DISTINCT serial_no) FROM owner WHERE own_name = ?", [n]).fetchone()[0]
            for n in tv_names
        )
        print(
            f"  {canonical[:34]:<34}  "
            f"patents={pat_total:>5}  ({len(pv_names)} variant(s))  "
            f"trademarks={tm_total:>4}  ({len(tv_names)} variant(s))"
        )

    # ------------------------------------------------------------------
    # Step 5 — Patent coverage (local DB)
    # ------------------------------------------------------------------
    print("\nStep 5 — Patent coverage (local DB)")
    if class_hints:
        print(f"  class_hints in project.json: {', '.join(class_hints)}")

    uncovered: list[str] = []
    for eid in sorted(entities):
        canonical = entities[eid]
        pv_names = [v["variant_name"] for v in pat_variants if int(v["entity_id"]) == eid]
        if not pv_names:
            print(f"  {canonical}: no patent_assignee variants — skipped")
            continue
        total = sum(
            conn_pat.execute("SELECT COUNT(*) FROM patents WHERE assignee_name = ?", [n]).fetchone()[0]
            for n in pv_names
        )
        print(f"  {canonical}: {total} patent(s) in local DB")
        if total == 0:
            uncovered.append(canonical)

    conn_pat.close()
    conn_tm.close()

    if uncovered:
        hint = f" --classes {' '.join(class_hints)}" if class_hints else ""
        print(f"  FAIL — {len(uncovered)} entity/entities have 0 local patents:")
        for u in uncovered:
            print(f"    {u}")
        print(f"  → Run: markery patent build{hint}")
        failed.append("patent-coverage")
    else:
        print("  PASS — all entities with patent_assignee variants have local coverage")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    if not failed:
        print("Onboarding PASSED")
    else:
        print(f"Onboarding FAILED ({', '.join(failed)})")
        sys.exit(1)


def project_main() -> None:
    parser = argparse.ArgumentParser(
        prog="markery project",
        description="Project management for Markery research projects",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    init_p = sub.add_parser("init", help="Scaffold a new project directory")
    init_p.add_argument("name", nargs="?", default=None, help="Project name (prompted if omitted)")
    init_p.add_argument("--type", dest="ptype", default=None,
                        choices=[t.value for t in ProjectType],
                        help="Project type (non-interactive; prompted if omitted). "
                             "Used by the spawn loop.")

    adopt_p = sub.add_parser("adopt", help="Declare the type of an existing project")
    adopt_p.add_argument("name", help="Project name (directory under projects/)")

    onboard_p = sub.add_parser("onboard", help="Run pre-match onboarding checklist")
    onboard_p.add_argument("project", help="Project name (directory under projects/)")

    args = parser.parse_args()

    if args.action == "init":
        cmd_init(args.name, ptype=args.ptype)
    elif args.action == "adopt":
        cmd_adopt(args.name)
    elif args.action == "onboard":
        cmd_onboard(args)
