"""Generate BRIEF.md for a project session.

Gathers current project state — confirmed pairs, content gaps, enrichment
coverage, unreviewed candidate count — and writes a structured brief that
the historian reads at the start of each session.

Output: projects/<project>/BRIEF.md  (gitignored; ephemeral)

Entry point: prepare(project)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import duckdb

from markery.common.config import Project
from markery.specialist.historian import queries as hq


# ---------------------------------------------------------------------------
# Data gathering
# ---------------------------------------------------------------------------

def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def gather_confirmed(proj: Project) -> list[dict]:
    """Return confirmed pairs as a list of dicts."""
    return _read_jsonl(proj.confirmed)


def gather_patent_state(
    conn: duckdb.DuckDBPyConnection,
    patent_nos: list[str],
) -> dict[str, dict]:
    """Return per-patent enrichment state: {patent_no: {abstract, figure}}."""
    return {
        pno: {
            "abstract": hq.patent_has_abstract(conn, pno),
            "figure":   hq.patent_has_figure(conn, pno),
        }
        for pno in patent_nos
    }


def gather_trademark_state(
    conn: duckdb.DuckDBPyConnection,
    serial_nos: list[str],
) -> dict[str, bool]:
    """Return per-trademark goods-description availability: {serial_no: bool}."""
    return {
        sn: hq.trademark_goods_available(conn, sn)
        for sn in serial_nos
    }


def count_unreviewed(proj: Project, min_score: float = 0.5) -> int:
    """Count candidates above min_score not yet confirmed or rejected."""
    candidates = _read_jsonl(proj.candidates)
    confirmed_keys = {
        (m["patent_no"], str(m["trademark_serial"]))
        for m in _read_jsonl(proj.confirmed)
    }
    rejected_keys = {
        (m["patent_no"], str(m["trademark_serial"]))
        for m in _read_jsonl(proj.rejected)
    }
    reviewed = confirmed_keys | rejected_keys
    return sum(
        1 for c in candidates
        if c.get("score", 0) >= min_score
        and (c["patent_no"], str(c["trademark_serial"])) not in reviewed
    )


def top_candidates(proj: Project, min_score: float = 0.5, n: int = 5) -> list[dict]:
    """Return the top N unreviewed candidates by score."""
    candidates = _read_jsonl(proj.candidates)
    confirmed_keys = {
        (m["patent_no"], str(m["trademark_serial"]))
        for m in _read_jsonl(proj.confirmed)
    }
    rejected_keys = {
        (m["patent_no"], str(m["trademark_serial"]))
        for m in _read_jsonl(proj.rejected)
    }
    reviewed = confirmed_keys | rejected_keys
    unreviewed = [
        c for c in candidates
        if c.get("score", 0) >= min_score
        and (c["patent_no"], str(c["trademark_serial"])) not in reviewed
    ]
    unreviewed.sort(key=lambda c: -c.get("score", 0))
    return unreviewed[:n]


# ---------------------------------------------------------------------------
# BRIEF.md rendering
# ---------------------------------------------------------------------------

def _session_recommendation(gaps: list[dict]) -> str:
    """Pick the highest-priority gap and return a plain-language task statement."""
    if not gaps:
        return "All known content gaps are filled. Consider writing a thematic essay or sources page."
    g = gaps[0]
    if g["type"] == "match_essay":
        return f"Write the match essay for **{g['label']}** → `{g['path']}`"
    if g["type"] == "entity_summary":
        return f"Write the entity summary for **{g['label']}** → `{g['path']}`"
    if g["type"] == "sources_page":
        return "Write the consolidated sources page → `content/sources.md`"
    if g["type"] == "timeline_page":
        return "Write the annotated timeline → `content/timeline.md`"
    return f"Address content gap: {g['label']}"


def render_brief(
    project: str,
    confirmed: list[dict],
    gaps: list[dict],
    patent_state: dict[str, dict],
    tm_state: dict[str, bool],
    unreviewed_count: int,
    top_cands: list[dict],
    prepared_at: str,
) -> str:
    """Build the full BRIEF.md content string."""

    # --- YAML frontmatter ---
    signals_available = [
        pno for pno, st in patent_state.items() if st["abstract"]
    ]
    figures_available = [
        pno for pno, st in patent_state.items() if st["figure"]
    ]
    enriched_trademarks = [
        sn for sn, has in tm_state.items() if has
    ]

    gap_yaml = "\n".join(
        f"  - {{type: {g['type']}, slug: {g['slug']}, priority: {g['priority']}}}"
        for g in gaps
    ) or "  []"

    signals_yaml = (
        "  [" + ", ".join(signals_available) + "]"
        if signals_available else "  []"
    )
    figures_yaml = (
        "  [" + ", ".join(figures_available) + "]"
        if figures_available else "  []"
    )
    enriched_yaml = (
        "  [" + ", ".join(f'"{s}"' for s in enriched_trademarks) + "]"
        if enriched_trademarks else "  []"
    )

    lines = [
        "---",
        f"project: {project}",
        f"prepared: {prepared_at}",
        f"confirmed_count: {len(confirmed)}",
        f"candidate_count_unreviewed: {unreviewed_count}",
        "content_gaps:",
        gap_yaml,
        "signals_available:",
        signals_yaml,
        "figures_available:",
        figures_yaml,
        "enriched_trademarks:",
        enriched_yaml,
        "---",
        "",
    ]

    # --- Section 1: Project State ---
    lines += ["## Project State", ""]
    if confirmed:
        lines.append(f"{len(confirmed)} confirmed pair(s):\n")
        seen_patents: set[str] = set()
        for m in confirmed:
            essay_exists = (
                Path(m["essay_path"]).exists()
                if m.get("essay_path") else False
            )
            essay_tag = " ✓ essay" if essay_exists else " — **no essay**"
            lines.append(
                f"- {m['trademark']} ↔ {m['patent_no']}  "
                f"({m.get('entity', '?')}){essay_tag}"
            )
            seen_patents.add(m["patent_no"])
    else:
        lines.append("No confirmed pairs yet.")
    lines.append("")

    # --- Section 2: Content Gaps ---
    lines += ["## Content Gaps", ""]
    if gaps:
        for g in gaps:
            lines.append(f"- **P{g['priority']}** {g['type']}: {g['label']}  →  `{g['path']}`")
    else:
        lines.append("No content gaps detected.")
    lines.append("")

    # --- Section 3: Candidate Highlights ---
    lines += [f"## Candidate Highlights  ({unreviewed_count} unreviewed above threshold)", ""]
    if top_cands:
        lines.append("Top unreviewed candidates by score:\n")
        lines.append("| Score | Patent | Trademark | Entity |")
        lines.append("|---|---|---|---|")
        for c in top_cands:
            lines.append(
                f"| {c.get('score', 0):.3f} "
                f"| {c['patent_no']} "
                f"| {c['trademark']} "
                f"| {c.get('entity', '?')} |"
            )
    else:
        lines.append("No unreviewed candidates above threshold.")
    lines.append("")

    # --- Section 4: Available Signals ---
    lines += ["## Available Signals", ""]
    if signals_available or figures_available:
        if signals_available:
            lines.append("**Abstracts available** (can be quoted in essays):")
            for pno in signals_available:
                lines.append(f"  - {pno}")
        if figures_available:
            lines.append("**Figures available** (can be described in essays):")
            for pno in figures_available:
                lines.append(f"  - {pno}")
    else:
        lines.append("No signal enrichment available yet. Run `markery patent signals <project>`.")
    lines.append("")

    # --- Section 5: Session Recommendation ---
    lines += ["## Session Recommendation", ""]
    lines.append(_session_recommendation(gaps))
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def prepare(project: str, min_score: float = 0.5) -> None:
    """Generate BRIEF.md for a project. Overwrites any existing brief."""
    proj = Project(project)
    if not proj.exists():
        raise ValueError(f"Project '{project}' not found at {proj.root}")

    prepared_at = datetime.now().isoformat(timespec="seconds")

    confirmed  = gather_confirmed(proj)
    for m in confirmed:
        slug  = m["trademark"].lower().replace(" ", "-")
        essay = proj.content / f"{slug}.md"
        m["essay_path"] = str(essay) if essay.exists() else None

    patent_nos = list(dict.fromkeys(m["patent_no"] for m in confirmed))
    serial_nos = list(dict.fromkeys(str(m["trademark_serial"]) for m in confirmed))

    pat_conn = hq.connect_patents()
    tm_conn  = hq.connect_trademarks()
    try:
        patent_state = gather_patent_state(pat_conn, patent_nos)
        tm_state     = gather_trademark_state(tm_conn, serial_nos)
    finally:
        pat_conn.close()
        tm_conn.close()

    gaps             = hq.content_gaps(project)
    unreviewed_count = count_unreviewed(proj, min_score)
    top_cands        = top_candidates(proj, min_score)

    content = render_brief(
        project=project,
        confirmed=confirmed,
        gaps=gaps,
        patent_state=patent_state,
        tm_state=tm_state,
        unreviewed_count=unreviewed_count,
        top_cands=top_cands,
        prepared_at=prepared_at,
    )

    proj.brief.write_text(content)
    print(f"BRIEF.md written → {proj.brief}")
    print(f"  {len(confirmed)} confirmed pairs  ·  {unreviewed_count} unreviewed candidates")
    print(f"  {len(gaps)} content gap(s)  ·  signals: {sum(1 for s in patent_state.values() if s['abstract'])}/{len(patent_nos)} patents")
