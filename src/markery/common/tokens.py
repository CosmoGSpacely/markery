"""Token measurement utilities for Markery commands.

Usage:
    from markery.common.tokens import TokenRecord, count_output_tokens, emit

    t0 = time.monotonic()
    # ... run command, capture output text ...
    record = count_output_tokens(output_text)  # uses MARKERY_MODEL env var
    record.wall_ms = int((time.monotonic() - t0) * 1000)
    emit(record, specialist="historian", command="card", tokens_flag=args.tokens)
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class TokenRecord:
    model: str
    prompt_tokens: int
    completion_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    wall_ms: int


# Model-dependent minimum cacheable-prefix size (tokens). A cache_control
# marker on a shorter prefix is silently ignored — see common/llm.py.
# Source: Anthropic prompt-caching docs.
_CACHE_MIN_TOKENS: list[tuple[str, int]] = [
    ("claude-haiku-4-5", 4096),
    ("claude-opus-4", 4096),
    ("claude-sonnet-4-6", 2048),
    ("claude-haiku-3", 2048),  # matches haiku-3 and haiku-3-5
    ("claude-sonnet-3", 1024),
    ("claude-sonnet-4-5", 1024),
    ("claude-sonnet-4-1", 1024),
    ("claude-sonnet-4", 1024),
]


def cache_min_for(model: str) -> int:
    """Return the minimum cacheable-prefix size (tokens) for a model, default 4096."""
    base = model.split("~")[0]  # strip the ~estimate suffix
    for prefix, minimum in _CACHE_MIN_TOKENS:
        if base.startswith(prefix):
            return minimum
    return 4096  # conservative default — the highest current minimum


def cache_health_warning(
    model: str,
    n_calls: int,
    cache_read_tokens: int,
) -> str | None:
    """Return a warning if a multi-call run sharing a system prefix never hit cache.

    A run of ≥2 calls with a shared cached system prefix should read from cache on
    the 2nd+ call. If cache_read is 0 across the whole run, the prefix is almost
    certainly below the model's cacheable minimum, so caching is silently disabled.
    """
    if n_calls >= 2 and cache_read_tokens == 0:
        return (
            f"cache never hit across {n_calls} calls — system prefix is likely below "
            f"{model.split('~')[0]}'s {cache_min_for(model)}-token cacheable minimum; "
            f"prompt caching is silently disabled (cache_read=0)."
        )
    return None


def count_output_tokens(text: str, model: str | None = None) -> TokenRecord:
    """Count tokens in text using the Anthropic count_tokens endpoint.

    Requires ANTHROPIC_API_KEY. Falls back to a word-count estimate
    (word_count * 0.75) if the key is absent or the SDK is unavailable.
    """
    if model is None:
        from markery.common.config import DEFAULT_MODEL
        model = os.environ.get("MARKERY_MODEL", DEFAULT_MODEL)
    from markery.common.llm import get_client
    client = get_client()
    if client is not None:
        try:
            resp = client.messages.count_tokens(
                model=model,
                messages=[{"role": "user", "content": text}],
            )
            return TokenRecord(
                model=model,
                prompt_tokens=resp.input_tokens,
                completion_tokens=0,
                cache_read_tokens=0,
                cache_creation_tokens=0,
                wall_ms=0,
            )
        except Exception:
            pass

    # Fallback: word-count estimate, model name flagged as estimate
    estimated = int(len(text.split()) * 0.75)
    return TokenRecord(
        model=f"{model}~estimate",
        prompt_tokens=estimated,
        completion_tokens=0,
        cache_read_tokens=0,
        cache_creation_tokens=0,
        wall_ms=0,
    )


def _append_log(record: TokenRecord, specialist: str, command: str) -> None:
    log_path = os.environ.get("MARKERY_TOKEN_LOG", "").strip()
    if not log_path:
        return
    from datetime import datetime, timezone
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "specialist": specialist,
        "command": command,
        **asdict(record),
    }
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def emit(
    record: TokenRecord,
    *,
    specialist: str,
    command: str,
    tokens_flag: bool = False,
    n_calls: int = 1,
) -> None:
    """Log the record to MARKERY_TOKEN_LOG and/or print to stderr.

    n_calls is the number of API calls aggregated into this record. When >1,
    the calls share a cached system prefix and the 2nd+ should read from cache;
    a 0 cache_read across the run triggers a correctness warning (always shown).
    """
    _append_log(record, specialist, command)
    warning = cache_health_warning(record.model, n_calls, record.cache_read_tokens)
    if warning:
        print(f"[tokens] warning: {warning}", file=sys.stderr)
    if tokens_flag:
        parts = [
            f"prompt={record.prompt_tokens:,}",
            f"completion={record.completion_tokens:,}",
            f"cache_read={record.cache_read_tokens:,}",
        ]
        if record.wall_ms:
            parts.append(f"wall={record.wall_ms}ms")
        print(f"[tokens] {' '.join(parts)} ({record.model})", file=sys.stderr)
