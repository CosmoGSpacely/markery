"""Aggregate a MARKERY_TOKEN_LOG JSONL file into a cost summary.

Backs `markery tokens report`. Reads the per-call records written by
`markery.common.tokens.emit`, sums token fields, computes the cache-hit rate,
and estimates USD cost at current per-model pricing.

Cost model (per Anthropic pricing): uncached prompt tokens at the input rate,
cache writes at 1.25× input, cache reads at 0.10× input, completion at the
output rate.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

# (input $/1M, output $/1M). Matched by model-ID prefix; longest-prefix wins.
_PRICING: list[tuple[str, tuple[float, float]]] = [
    ("claude-opus-4",     (5.0, 25.0)),
    ("claude-sonnet-4-6", (3.0, 15.0)),
    ("claude-sonnet-4-5", (3.0, 15.0)),
    ("claude-sonnet-4",   (3.0, 15.0)),
    ("claude-haiku-4-5",  (1.0,  5.0)),
    ("claude-haiku-3-5",  (0.80, 4.0)),
    ("claude-haiku-3",    (0.25, 1.25)),
]

_CACHE_WRITE_MULT = 1.25
_CACHE_READ_MULT = 0.10

_FIELDS = ("prompt_tokens", "completion_tokens",
           "cache_read_tokens", "cache_creation_tokens")


def _rate(model: str) -> tuple[float, float] | None:
    base = model.split("~")[0]  # strip the ~estimate suffix
    best: tuple[float, float] | None = None
    best_len = -1
    for prefix, rate in _PRICING:
        if base.startswith(prefix) and len(prefix) > best_len:
            best, best_len = rate, len(prefix)
    return best


def record_cost(rec: dict) -> tuple[float, bool]:
    """Return (usd, unknown_pricing) for one record."""
    rate = _rate(rec.get("model", ""))
    if rate is None:
        return 0.0, True
    inp, out = rate
    usd = (
        rec.get("prompt_tokens", 0) * inp
        + rec.get("cache_creation_tokens", 0) * inp * _CACHE_WRITE_MULT
        + rec.get("cache_read_tokens", 0) * inp * _CACHE_READ_MULT
        + rec.get("completion_tokens", 0) * out
    ) / 1_000_000
    return usd, False


def load_records(log_path: str | os.PathLike) -> list[dict]:
    p = Path(log_path)
    if not p.exists():
        return []
    records = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _sum_fields(records: list[dict]) -> dict[str, int]:
    totals = {f: 0 for f in _FIELDS}
    for r in records:
        for f in _FIELDS:
            totals[f] += r.get(f, 0)
    return totals


def _cache_hit_rate(totals: dict[str, int]) -> float:
    cached = totals["cache_read_tokens"]
    denom = totals["prompt_tokens"] + totals["cache_read_tokens"] + totals["cache_creation_tokens"]
    return (cached / denom) if denom else 0.0


def build_report(records: list[dict], group_by: str | None = None) -> str:
    """Return a human-readable token/cost report."""
    if not records:
        return "No token records found. Set MARKERY_TOKEN_LOG and run a command that calls the API."

    totals = _sum_fields(records)
    total_cost = 0.0
    any_unknown = False
    for r in records:
        usd, unknown = record_cost(r)
        total_cost += usd
        any_unknown = any_unknown or unknown

    lines: list[str] = []
    lines.append(f"records:            {len(records):>12,}")
    lines.append(f"prompt (uncached):  {totals['prompt_tokens']:>12,}")
    lines.append(f"cache_read:         {totals['cache_read_tokens']:>12,}")
    lines.append(f"cache_creation:     {totals['cache_creation_tokens']:>12,}")
    lines.append(f"completion:         {totals['completion_tokens']:>12,}")
    lines.append(f"cache hit rate:     {_cache_hit_rate(totals) * 100:>11.1f}%")
    lines.append(f"estimated cost:     {'$' + format(total_cost, '.4f'):>12}")
    if any_unknown:
        lines.append("  (some records had an unrecognised model ID — priced at $0)")

    if group_by:
        valid = {"specialist", "command", "model"}
        if group_by not in valid:
            lines.append(f"\n(unknown --by '{group_by}'; valid: {', '.join(sorted(valid))})")
            return "\n".join(lines)
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in records:
            groups[str(r.get(group_by, "—"))].append(r)
        lines.append(f"\nBy {group_by}:")
        header = f"  {'key':<22}{'prompt':>12}{'completion':>12}{'cache_read':>12}{'cost':>12}"
        lines.append(header)
        for key in sorted(groups):
            g = groups[key]
            gt = _sum_fields(g)
            gcost = sum(record_cost(r)[0] for r in g)
            lines.append(
                f"  {key[:22]:<22}{gt['prompt_tokens']:>12,}"
                f"{gt['completion_tokens']:>12,}{gt['cache_read_tokens']:>12,}"
                f"{'$' + format(gcost, '.4f'):>12}"
            )

    return "\n".join(lines)


def report_main(rest: list[str]) -> None:
    """CLI: markery tokens report [--log PATH] [--by specialist|command|model]."""
    import argparse

    parser = argparse.ArgumentParser(prog="markery tokens report")
    parser.add_argument("--log", metavar="PATH", default=None,
                        help="Token log path (default: $MARKERY_TOKEN_LOG)")
    parser.add_argument("--by", metavar="FIELD", default=None,
                        choices=["specialist", "command", "model"],
                        help="Group the breakdown by specialist, command, or model")
    args = parser.parse_args(rest)

    log_path = args.log or os.environ.get("MARKERY_TOKEN_LOG", "").strip()
    if not log_path:
        print("No token log specified. Pass --log PATH or set MARKERY_TOKEN_LOG.")
        return

    records = load_records(log_path)
    print(f"Token report — {log_path}\n")
    print(build_report(records, group_by=args.by))
