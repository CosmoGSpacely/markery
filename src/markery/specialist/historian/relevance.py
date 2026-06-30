"""Discovery relevance scoring (Phase 30 P3).

Scores how relevant a discovered item (a candidate book/photo/clipping title +
optional snippet) is to a project, using the same free-model + structured-output
pattern as ``historian card --infer``. The discovery loop calls this to route a
lead: high score → acquire/queue, low → log-and-drop. Deterministic plumbing
(context assembly, parsing) is unit-tested; the model call is mocked.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from markery.common.config import model_chain
from markery.common.project import Project

_SYSTEM = (
    "You are the Markery historian assessing whether a discovered source is "
    "relevant to a research project about specific companies and their "
    "patents/trademarks. Reply in exactly this format:\n"
    "SCORE: <1-5>\nREASONING: <one or two sentences>\n"
    "5 = directly about a project entity or its products; 1 = unrelated."
)


def _project_context(project: str) -> str:
    """Assemble a compact project description: entities + research question."""
    proj = Project(project)
    parts: list[str] = [f"Project: {project}"]
    ents_csv = proj.root / "entities.csv"
    if ents_csv.exists():
        names = []
        with ents_csv.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("canonical_name"):
                    names.append(row["canonical_name"])
        if names:
            parts.append("Companies: " + ", ".join(names))
    rq = proj.root / "content" / "research-question.md"
    if rq.exists():
        parts.append("Research question: " + rq.read_text(encoding="utf-8").strip()[:500])
    return "\n".join(parts)


def parse_score(text: str) -> dict:
    score_m = re.search(r"^SCORE:\s*([1-5])", text, re.IGNORECASE | re.MULTILINE)
    reason_m = re.search(r"^REASONING:\s*(.+)", text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return {
        "score": int(score_m.group(1)) if score_m else 0,
        "reasoning": reason_m.group(1).strip() if reason_m else text.strip(),
    }


def score_relevance(project: str, title: str, text: str = "",
                    model: str | None = None) -> dict:
    """Return {score: 0-5, reasoning} for a candidate item against a project.

    score 0 means the model output was unparseable (caller treats as low).
    Tries the free model chain (D077) for rate-limit resilience; an explicit
    `model` is honoured exactly."""
    from markery.common.llm import call_chain
    user = (
        f"{_project_context(project)}\n\n"
        f"Candidate source —\nTitle: {title}\n"
        + (f"Snippet: {text[:800]}\n" if text else "")
        + "\nHow relevant is this candidate to the project?"
    )
    resp_text, *_ = call_chain(model_chain(model), _SYSTEM, user, 200)
    return parse_score(resp_text)
