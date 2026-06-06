"""Shared LLM client and call helpers.

Single client construction site for Markery. All specialist commands that
call Claude go through here so provider changes require editing one file.

    from markery.common.llm import get_client, call

    client = get_client()           # returns None if key absent
    text, ptok, ctok, cr, cc = call(model, system, user, max_tokens)

cache_system=True (default) wraps the system prompt in a cache_control block.
The block must be ≥1024 tokens for the cache to activate; shorter prompts are
accepted but silently not cached. cache_read and cache_creation are 0 when
the API does not support or honour caching for a given call.
"""

from __future__ import annotations

import os


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
