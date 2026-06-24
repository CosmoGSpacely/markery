#!/usr/bin/env python3
"""Phase 14 P4 — Free-model run benchmark.

Sends historian and gallery-review workflow prompts to claude-haiku-4-5-20251001
and validates that responses do not hallucinate structured data (serial numbers,
patent numbers). Results are written to p4-haiku-<date>.jsonl.

Usage:
    python tests/benchmarks/p4_haiku_run.py

Requires ANTHROPIC_API_KEY in environment or .env.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT  = Path(__file__).resolve().parents[2]
BENCH_DIR  = Path(__file__).parent
MODEL      = "claude-haiku-4-5-20251001"
TODAY      = datetime.now(timezone.utc).strftime("%Y-%m-%d")
LOG_PATH   = BENCH_DIR / f"p4-haiku-{TODAY}.jsonl"

PERSONA_PATH = REPO_ROOT / "src/markery/specialist/historian/persona/identity.md"
ESSAY_PATH   = REPO_ROOT / "projects/annual-design-review/essays/chicago-pneumatic-cp.md"

HISTORIAN_CARD_SLUGS = [
    "remington-us2168802a",
    "rand-us2159415a",
    "favorite-us1527374a",
]

TASK_HISTORIAN = """You have been given a project digest and three candidate cards.

For each candidate card:
1. State whether the patent-trademark correspondence is plausible (yes / no / uncertain).
2. In one sentence, identify the strongest supporting evidence or the most significant concern.
3. Note the date gap and whether it is consistent with normal product-development timelines.

Use only the data in the cards. Do not invent facts not present in the input."""

TASK_GALLERY = """You have been given a research essay about a USPTO trademark filing.

Write a two-sentence Wikipedia talk-page note proposing coverage of this mark.
The note should:
- Name the company and the filing date.
- State what makes this mark historically notable.
- Cite the USPTO serial number.

Use only facts from the essay. Do not invent sources."""


# ---------------------------------------------------------------------------

def _run_cmd(*args: str) -> str:
    result = subprocess.run(list(args), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[error] command failed: {' '.join(args)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def _count_tokens(client, text: str) -> int:
    resp = client.messages.count_tokens(
        model=MODEL,
        messages=[{"role": "user", "content": text}],
    )
    return resp.input_tokens


def _call_haiku(client, system: str, user: str) -> tuple[str, int, int, int]:
    """Returns (response_text, prompt_tokens, completion_tokens, wall_ms)."""
    t0 = time.monotonic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    wall_ms = int((time.monotonic() - t0) * 1000)
    text = resp.content[0].text
    return text, resp.usage.input_tokens, resp.usage.output_tokens, wall_ms


def _extract_serials(text: str) -> list[str]:
    return re.findall(r'\b7[01]\d{6}\b', text)


def _extract_patents(text: str) -> list[str]:
    return re.findall(r'\bUS\d{6,8}[A-Z]\b', text)


def _validate_no_hallucinations(response: str, allowed_serials: set[str], allowed_patents: set[str]) -> tuple[bool, list[str]]:
    found_serials  = set(_extract_serials(response))
    found_patents  = set(_extract_patents(response))
    alien_serials  = found_serials - allowed_serials
    alien_patents  = found_patents - allowed_patents
    issues = []
    if alien_serials:
        issues.append(f"alien serials: {sorted(alien_serials)}")
    if alien_patents:
        issues.append(f"alien patents: {sorted(alien_patents)}")
    return len(issues) == 0, issues


def _log(entry: dict) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------

def run_historian_workflow(client) -> dict:
    print("\n── Historian workflow (card/digest) ──")

    persona    = PERSONA_PATH.read_text(encoding="utf-8")
    digest_out = _run_cmd("markery", "historian", "digest", "information-systems", "--top", "3")
    cards      = {slug: _run_cmd("markery", "historian", "card", "information-systems", slug, "--out", "-")
                  for slug in HISTORIAN_CARD_SLUGS}

    user_content = "\n\n".join([
        "## PROJECT DIGEST\n" + digest_out.strip(),
        *[f"## {slug.upper()}\n" + card.strip() for slug, card in cards.items()],
        "## TASK\n" + TASK_HISTORIAN,
    ])

    # Count context tokens
    context_tokens = _count_tokens(client, user_content)
    print(f"  context prompt tokens:  {context_tokens:,}")

    # Inference call
    response, prompt_tok, completion_tok, wall_ms = _call_haiku(client, persona, user_content)
    print(f"  inference prompt tokens:  {prompt_tok:,}")
    print(f"  completion tokens:        {completion_tok:,}")
    print(f"  wall ms:                  {wall_ms:,}")

    # Validation
    allowed_serials = set(_extract_serials(user_content))
    allowed_patents = set(_extract_patents(user_content))
    passed, issues = _validate_no_hallucinations(response, allowed_serials, allowed_patents)

    print(f"  hallucination check:      {'PASS' if passed else 'FAIL'}")
    if issues:
        for issue in issues:
            print(f"    [!] {issue}")

    result = {
        "workflow": "historian",
        "model": MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context_prompt_tokens": context_tokens,
        "inference_prompt_tokens": prompt_tok,
        "completion_tokens": completion_tok,
        "wall_ms": wall_ms,
        "hallucination_pass": passed,
        "hallucination_issues": issues,
        "response_preview": response[:300],
    }
    _log(result)
    return result


def run_gallery_workflow(client) -> dict:
    print("\n── Gallery/Wikipedia workflow ──")

    persona = PERSONA_PATH.read_text(encoding="utf-8")
    essay   = ESSAY_PATH.read_text(encoding="utf-8")

    user_content = f"## ESSAY\n{essay.strip()}\n\n## TASK\n{TASK_GALLERY}"

    # Count context tokens
    context_tokens = _count_tokens(client, user_content)
    print(f"  context prompt tokens:  {context_tokens:,}")

    # Inference call
    response, prompt_tok, completion_tok, wall_ms = _call_haiku(client, persona, user_content)
    print(f"  inference prompt tokens:  {prompt_tok:,}")
    print(f"  completion tokens:        {completion_tok:,}")
    print(f"  wall ms:                  {wall_ms:,}")

    # Validation: serial in essay should appear in response; no alien serials
    allowed_serials = set(_extract_serials(essay))
    allowed_patents = set(_extract_patents(essay))
    passed, issues = _validate_no_hallucinations(response, allowed_serials, allowed_patents)

    print(f"  hallucination check:      {'PASS' if passed else 'FAIL'}")
    if issues:
        for issue in issues:
            print(f"    [!] {issue}")

    result = {
        "workflow": "gallery",
        "model": MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context_prompt_tokens": context_tokens,
        "inference_prompt_tokens": prompt_tok,
        "completion_tokens": completion_tok,
        "wall_ms": wall_ms,
        "hallucination_pass": passed,
        "hallucination_issues": issues,
        "response_preview": response[:300],
    }
    _log(result)
    return result


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("ANTHROPIC_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    print(f"Model: {MODEL}")
    print(f"Log:   {LOG_PATH}")

    h = run_historian_workflow(client)
    g = run_gallery_workflow(client)

    print("\n── Summary ──")
    print(f"  Historian  prompt={h['inference_prompt_tokens']:,}  "
          f"completion={h['completion_tokens']:,}  "
          f"hallucination={'PASS' if h['hallucination_pass'] else 'FAIL'}")
    print(f"  Gallery    prompt={g['inference_prompt_tokens']:,}  "
          f"completion={g['completion_tokens']:,}  "
          f"hallucination={'PASS' if g['hallucination_pass'] else 'FAIL'}")

    all_pass = h["hallucination_pass"] and g["hallucination_pass"]
    print(f"\nP4 GATE: {'PASS' if all_pass else 'FAIL'}")


if __name__ == "__main__":
    main()
