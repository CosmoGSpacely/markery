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


def count_output_tokens(text: str, model: str | None = None) -> TokenRecord:
    """Count tokens in text using the Anthropic count_tokens endpoint.

    Requires ANTHROPIC_API_KEY. Falls back to a word-count estimate
    (word_count * 0.75) if the key is absent or the SDK is unavailable.
    """
    if model is None:
        model = os.environ.get("MARKERY_MODEL", "claude-haiku-4-5-20251001")
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
) -> None:
    """Log the record to MARKERY_TOKEN_LOG and/or print to stderr."""
    _append_log(record, specialist, command)
    if tokens_flag:
        parts = [
            f"prompt={record.prompt_tokens:,}",
            f"completion={record.completion_tokens:,}",
            f"cache_read={record.cache_read_tokens:,}",
        ]
        if record.wall_ms:
            parts.append(f"wall={record.wall_ms}ms")
        print(f"[tokens] {' '.join(parts)} ({record.model})", file=sys.stderr)
