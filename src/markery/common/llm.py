"""Shared LLM client and call helpers.

Single client construction site for Markery. All specialist commands that
call Claude go through here so provider changes require editing one file.

    from markery.common.llm import get_client, call

    client = get_client()           # returns None if key absent
    text, ptok, ctok, cr, cc = call(model, system, user, max_tokens)

cache_system=True (default) wraps the system prompt in a cache_control block.
The cacheable-prefix minimum is **model-dependent** — a marker on a shorter
prefix is silently ignored (no error, just cache_creation/cache_read = 0):

    Haiku 4.5, Opus 4.5–4.8   4096 tokens
    Sonnet 4.6, Haiku 3/3.5   2048 tokens
    Sonnet 3.7–4.5            1024 tokens

Markery's default model is Haiku 4.5 (4096-token minimum); the specialist
system prompts are ~2K tokens, so caching does NOT currently activate on the
default model — cache_read is 0 on every call. See `markery tokens report`
(D059) and the cache-verification warning in common/tokens.py.
"""

from __future__ import annotations

import os
import time


def get_client():
    """Return an anthropic.Anthropic client, or None if key is absent."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        return None


def call(
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    cache_system: bool = True,
) -> tuple[str, int, int, int, int]:
    """Send one message to the LLM.

    Returns (text, prompt_tokens, completion_tokens, cache_read_tokens, cache_creation_tokens).
    cache_read and cache_creation are 0 when caching is disabled or the prompt is too short.
    """
    client = get_client()
    if client is None:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set or anthropic package not installed. "
            "Set ANTHROPIC_API_KEY in .env and run: pip install anthropic"
        )
    if cache_system:
        system_param = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
    else:
        system_param = system

    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_param,
        messages=[{"role": "user", "content": user}],
    )
    cache_read   = getattr(resp.usage, "cache_read_input_tokens",   0) or 0
    cache_create = getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
    return (
        resp.content[0].text.strip(),
        resp.usage.input_tokens,
        resp.usage.output_tokens,
        cache_read,
        cache_create,
    )


def call_batch(
    model: str,
    system: str,
    items: list[tuple[str, str]],
    max_tokens: int,
    cache_system: bool = True,
    poll_interval: int = 15,
    timeout: int = 3600,
) -> dict[str, dict]:
    """Submit independent single-turn requests as one Batch API job (50% price).

    `items` is a list of (custom_id, user_text). All requests share `system`.
    Returns a dict keyed by custom_id; each value is either
      {text, prompt_tokens, completion_tokens, cache_read_tokens, cache_creation_tokens}
    on success, or {error: <type>} on failure. Use the Batch API for bulk,
    latency-tolerant work (librarian extract over chunks, historian infer over a
    queue) — it bills at 50% of standard token price. See common/tokens_report.

    Blocks until the batch ends (most finish within minutes; max 24h). Raises
    RuntimeError on missing client or if the batch does not end within `timeout`.
    """
    client = get_client()
    if client is None:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set or anthropic package not installed."
        )
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    sys_param = (
        [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if cache_system else system
    )
    requests = [
        Request(
            custom_id=cid,
            params=MessageCreateParamsNonStreaming(
                model=model, max_tokens=max_tokens, system=sys_param,
                messages=[{"role": "user", "content": text}],
            ),
        )
        for cid, text in items
    ]
    batch = client.messages.batches.create(requests=requests)

    deadline = time.monotonic() + timeout
    while True:
        b = client.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended":
            break
        if time.monotonic() > deadline:
            raise RuntimeError(f"batch {batch.id} did not end within {timeout}s")
        time.sleep(poll_interval)

    out: dict[str, dict] = {}
    for result in client.messages.batches.results(batch.id):
        cid = result.custom_id
        if result.result.type == "succeeded":
            msg = result.result.message
            text = next((blk.text for blk in msg.content if blk.type == "text"), "")
            u = msg.usage
            out[cid] = {
                "text": text.strip(),
                "prompt_tokens": u.input_tokens,
                "completion_tokens": u.output_tokens,
                "cache_read_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
                "cache_creation_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
            }
        else:
            out[cid] = {"error": result.result.type}
    return out
