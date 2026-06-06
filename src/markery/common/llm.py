"""Shared LLM client and call helpers.

Single client construction site for Markery. All specialist commands that
call Claude go through here so provider changes require editing one file.

    from markery.common.llm import get_client, call

    client = get_client()           # returns None if key absent
    text, ptok, ctok = call(model, system, user, max_tokens)
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
) -> tuple[str, int, int]:
    """Send one message to the LLM. Returns (text, prompt_tokens, completion_tokens)."""
    client = get_client()
    if client is None:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set or anthropic package not installed. "
            "Set ANTHROPIC_API_KEY in .env and run: pip install anthropic"
        )
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip(), resp.usage.input_tokens, resp.usage.output_tokens
