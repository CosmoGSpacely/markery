#!/usr/bin/env python3
"""Cross-model MVO benchmark (Phase 22 P3 / D061).

Proves the model-agnosticism claim in DESIGN.md §Model-Agnosticism by executing
the model-agnostic-tier historian tasks under ≥2 models over a fixed fixture set
and asserting each output passes its MVO validator:

  - `markery historian card --infer`  → structured RECOMMENDATION/SCORE/REASONING
  - `markery historian draft`         → essay that passes `historian validate` (8/8)

The pass/fail gate is the proof: any model whose output passes the deterministic
DB-backed validator is producing correct, contamination-free factual content. A
per-model cost/quality table is written to cross-model-mvo-<date>.jsonl and
printed as Markdown for DESIGN.md.

Usage:
    python tests/benchmarks/cross_model_mvo.py

Requires ANTHROPIC_API_KEY in environment or .env. Makes live API calls
(2 models × 3 fixtures × {infer, draft} = 12 calls). Cost is a few cents.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH_DIR = Path(__file__).parent
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
RESULTS_PATH = BENCH_DIR / f"cross-model-mvo-{TODAY}.jsonl"

# Two models spanning the price/capability range. Haiku is the default; Sonnet
# is the natural "second house model" the agnosticism claim must survive. Pass
# --models to override (e.g. a cross-provider OpenRouter/OpenAI/xAI comparison).
MODELS = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
]


def _short_name(model: str) -> str:
    """Filesystem-safe short tag for a model id (for draft provenance files)."""
    if "haiku" in model:
        return "haiku"
    if "sonnet" in model:
        return "sonnet"
    return re.sub(r"[^a-z0-9.]+", "-", model.lower()).strip("-")

# One confirmed pair from each of the three existing projects. Each has a
# committed scaffold/essay at content/<slug>.md and a resolvable candidate card.
FIXTURES = [
    ("information-systems", "soundex-us1261167a"),
    ("radio-pioneers",      "sterilamp-us2168861a"),
    ("animal-marks-1930",   "john-deere-moline-ill-us979019a"),
]


def _run(args: list[str], env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["markery", *args],
        cwd=REPO_ROOT, env=env,
        capture_output=True, text=True,
    )


def _infer(project: str, slug: str, model: str, env: dict) -> dict:
    """Run `historian card --infer`; pass = a structured recommendation parsed."""
    cp = _run(["historian", "card", project, slug, "--infer", "--model", model], env)
    out = cp.stdout + cp.stderr
    m = re.search(r"recommendation=(\w+)\s+score=(\d+)", out)
    return {
        "task": "card.infer",
        "passed": bool(m) and cp.returncode == 0,
        "recommendation": m.group(1) if m else None,
        "score": int(m.group(2)) if m else None,
    }


def _draft_and_validate(project: str, slug: str, model: str, env: dict) -> dict:
    """Run `historian draft` then `historian validate` on the draft. pass = 0 fails."""
    draft_rel = f"projects/{project}/content/{slug}-draft.md"
    draft_abs = REPO_ROOT / draft_rel
    pre_existed = draft_abs.exists()

    dcp = _run(["historian", "draft", project, slug, "--model", model], env)
    if dcp.returncode != 0 or not draft_abs.exists():
        return {"task": "draft.validate", "passed": False,
                "checks_passed": 0, "checks_total": 0,
                "error": (dcp.stderr or dcp.stdout)[:200]}

    # Preserve this model's draft for provenance before the next model overwrites it.
    prov_dir = BENCH_DIR / "drafts" / TODAY
    prov_dir.mkdir(parents=True, exist_ok=True)
    short = _short_name(model)
    (prov_dir / f"{slug}.{short}.md").write_text(
        draft_abs.read_text(encoding="utf-8"), encoding="utf-8")

    vcp = _run(["historian", "validate", project, slug, "--essay", draft_rel], env)
    checks = re.findall(r"^\s*(PASS|FAIL)\b", vcp.stdout, re.MULTILINE)
    passed = sum(1 for c in checks if c == "PASS")

    # Clean up the transient content/<slug>-draft.md if we created it.
    if not pre_existed:
        draft_abs.unlink(missing_ok=True)

    return {
        "task": "draft.validate",
        "passed": vcp.returncode == 0,
        "checks_passed": passed,
        "checks_total": len(checks),
    }


def _provider_ready(model: str) -> tuple[bool, str]:
    """Return (ready, reason) — whether the provider key for `model` is present."""
    from markery.common.providers import route, _env_key
    from markery.common.llm import get_client
    provider = route(model)
    if provider == "anthropic":
        return (get_client() is not None, "ANTHROPIC_API_KEY / anthropic SDK")
    if provider == "openrouter":
        from markery.common.openrouter import runtime_key
        return (runtime_key(allow_mint=False) is not None, "OpenRouter runtime key")
    if provider == "openai":
        return (bool(_env_key("OPENAI_API_KEY")), "OPENAI_API_KEY")
    if provider == "xai":
        return (bool(_env_key("XAI_API_KEY")), "XAI_API_KEY")
    return (True, "")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Cross-model MVO benchmark")
    parser.add_argument("--models", nargs="+", default=MODELS,
                        help="Model ids to compare (any provider). Default: the P3 two-model set.")
    parser.add_argument("--infer-only", action="store_true",
                        help="Run only card --infer (skip the draft+validate step)")
    parser.add_argument("--label", default="cross-model-mvo",
                        help="Output filename stem. Use a distinct label (e.g. "
                             "'cross-provider') for runs where partial validator "
                             "failure is expected, to keep the P3 regression guard "
                             "(which globs cross-model-mvo-*.jsonl) separate.")
    args = parser.parse_args()
    results_path = BENCH_DIR / f"{args.label}-{TODAY}.jsonl"

    models: list[str] = []
    for m in args.models:
        ready, reason = _provider_ready(m)
        if ready:
            models.append(m)
        else:
            print(f"  skipping {m}: provider not ready ({reason})", file=sys.stderr)
    if not models:
        print("No runnable models — check provider keys.", file=sys.stderr)
        return 1

    token_log = Path(tempfile.mkstemp(suffix=".jsonl", prefix="xmvo-")[1])
    base_env = {**os.environ, "MARKERY_TOKEN_LOG": str(token_log)}

    records: list[dict] = []
    for model in models:
        for project, slug in FIXTURES:
            print(f"  {model:<32} {project}/{slug}")
            infer = _infer(project, slug, model, base_env)
            results = [infer]
            if not args.infer_only:
                results.append(_draft_and_validate(project, slug, model, base_env))
            for r in results:
                records.append({"model": model, "project": project, "slug": slug, **r})
                flag = "ok " if r["passed"] else "FAIL"
                print(f"      [{flag}] {r['task']}"
                      + (f"  ({r.get('recommendation')}/{r.get('score')})"
                         if r["task"] == "card.infer" else
                         f"  ({r.get('checks_passed')}/{r.get('checks_total')})"))

    # Aggregate token cost per model from the live token log.
    from markery.common.tokens_report import load_records, _sum_fields, record_cost
    token_records = load_records(token_log)
    token_log.unlink(missing_ok=True)

    by_model: dict[str, dict] = {}
    for model in models:
        runs = [r for r in records if r["model"] == model]
        passed = sum(1 for r in runs if r["passed"])
        tr = [t for t in token_records if t.get("model", "").startswith(model.split("~")[0])]
        totals = _sum_fields(tr)
        cost = sum(record_cost(t)[0] for t in tr)
        by_model[model] = {
            "validator_pass": passed,
            "validator_total": len(runs),
            "prompt_tokens": totals["prompt_tokens"],
            "completion_tokens": totals["completion_tokens"],
            "cache_read_tokens": totals["cache_read_tokens"],
            "usd": cost,
        }

    # Write per-run results JSONL.
    with open(results_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"benchmark": "cross-model-mvo", "date": TODAY,
                             "fixtures": [f"{p}/{s}" for p, s in FIXTURES],
                             "summary": by_model}) + "\n")
        for r in records:
            fh.write(json.dumps(r) + "\n")

    print(f"\nResults → {results_path}\n")
    print(render_table(by_model))
    return 0


def render_table(by_model: dict[str, dict]) -> str:
    """Markdown cost/quality table for DESIGN.md."""
    lines = [
        "| Model | Validator pass | Prompt tok | Completion tok | Cache read | Est. cost |",
        "|---|---|---|---|---|---|",
    ]
    for model, s in by_model.items():
        lines.append(
            f"| `{model}` | {s['validator_pass']}/{s['validator_total']} "
            f"| {s['prompt_tokens']:,} | {s['completion_tokens']:,} "
            f"| {s['cache_read_tokens']:,} | ${s['usd']:.4f} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
