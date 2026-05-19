"""Session handoff verifier. Run: markery status"""

import json
import re
from datetime import date
from pathlib import Path

from markery.common.config import ROOT, DB

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


def human_size(path: Path) -> str:
    b = path.stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.0f} {unit}"
        b /= 1024
    return f"{b:.1f} GB"


def db_stats(db_path: Path) -> dict | None:
    if not HAS_DUCKDB or not db_path.exists():
        return None
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        stats = {}
        for table in sorted(tables):
            stats[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return stats
    except Exception as e:
        return {"error": str(e)}


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text().splitlines() if line.strip())


def read_deferred(md_path: Path) -> list[tuple[str, str]]:
    if not md_path.exists():
        return []
    items = []
    for line in md_path.read_text().splitlines():
        m = re.match(r"\|\s*(D\d+)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            items.append((m.group(1), m.group(2).strip()))
    return items


def read_next_action(context_path: Path) -> str | None:
    if not context_path.exists():
        return None
    lines = context_path.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("## Next Action"):
            for j in range(i + 1, min(i + 5, len(lines))):
                text = lines[j].strip()
                if text:
                    return text
    return None


def section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def main() -> None:
    print(f"=== Markery Status — {date.today()} ===")

    section("Databases")
    dbs = [
        (DB["trademarks"], ["case_file", "mark_images", "extended_marks"]),
        (DB["patents"],    ["patents", "patent_classes", "patent_inventors"]),
        (DB["entities"],  ["company_entity", "entity_name_variant"]),
    ]
    for db_path, key_tables in dbs:
        db_name = str(db_path.relative_to(ROOT))
        if not db_path.exists():
            print(f"  {db_name:<28} MISSING")
            continue
        size = human_size(db_path)
        stats = db_stats(db_path)
        if stats is None:
            print(f"  {db_name:<28} {size}  (duckdb not available)")
        elif "error" in stats:
            print(f"  {db_name:<28} {size}  ERROR: {stats['error']}")
        else:
            counts = "  |  ".join(
                f"{t}: {stats.get(t, '?'):,}" for t in key_tables if t in stats
            )
            print(f"  {db_name:<28} {size:>7}  ({counts})")

    section("Projects")
    projects_dir = ROOT / "projects"
    found_any = False
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        matches_dir = project_dir / "matches"
        content_dir = project_dir / "content"
        candidates  = count_jsonl(matches_dir / "candidates.jsonl")
        confirmed   = count_jsonl(matches_dir / "confirmed.jsonl")
        essays      = len(list(content_dir.glob("*.md"))) if content_dir.exists() else 0
        entities_f  = project_dir / "entities.txt"
        entities    = len([l for l in entities_f.read_text().splitlines()
                           if l.strip() and not l.startswith("#")]) if entities_f.exists() else "—"
        pipeline_path = matches_dir / "pipeline_state.json"
        if pipeline_path.exists():
            try:
                ps = json.loads(pipeline_path.read_text())
                gen = (ps.get("generated_at") or "")[:10]
                enr = ps.get("enriched_at")
                enr_str = f"  enriched {enr[:10]}" if enr else ""
                pipeline_str = f"  (generated {gen}{enr_str})"
            except Exception:
                pipeline_str = ""
        else:
            pipeline_str = ""

        print(f"  {project_dir.name}")
        print(f"    entities:   {entities}")
        print(f"    candidates: {candidates:,}{pipeline_str}")
        print(f"    confirmed:  {confirmed}")
        print(f"    essays:     {essays}")
        found_any = True
    if not found_any:
        print("  (no projects found)")

    section("Deferred items  (DEFERRED.md)")
    items = read_deferred(ROOT / "DEFERRED.md")
    if items:
        for did, desc in items:
            print(f"  {did}  {desc}")
    else:
        print("  (none or DEFERRED.md not found)")

    section("Next action  (CONTEXT.md)")
    action = read_next_action(ROOT / "CONTEXT.md")
    print(f"  {action}" if action else "  (not found)")

    print()


if __name__ == "__main__":
    main()
