"""Provider routing and a shared OpenAI-compatible chat client.

Markery is model-agnostic. A specialist asks for a model by id; this module
decides which provider serves it and (for the OpenAI-compatible providers)
makes the call. Anthropic is handled separately in common/llm.py via the
official SDK.

Routing (``route``)
-------------------
    claude-*                         → anthropic   (Anthropic SDK, in llm.py)
    openai:<model>                   → openai      (api.openai.com)
    xai:<model> / grok-*             → xai         (api.x.ai)
    <vendor>/<model>[:tag]           → openrouter  (openrouter.ai; key minted)
    gpt-* / o1-* / o3-* / o4-* …      → openai
    (anything else)                  → anthropic

Explicit ``openai:``/``xai:`` prefixes always win and are stripped before the
call. OpenRouter slugs are distinguished by the ``/`` (e.g.
``openai/gpt-oss-120b:free`` is OpenRouter, ``openai:gpt-4o`` is direct OpenAI).

OpenAI and xAI use a plain ``OPENAI_API_KEY`` / ``XAI_API_KEY`` from the
environment (.env). OpenRouter's runtime-key minting lives in
common/openrouter.py and is invoked by ``openrouter.chat``.
"""

from __future__ import annotations

import os

OPENAI_BASE = "https://api.openai.com/v1"
XAI_BASE = "https://api.x.ai/v1"

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_XAI_MODEL = "grok-3"


def _env_key(name: str) -> str:
    """Read an API key from the environment, loading .env on first miss."""
    val = os.environ.get(name, "").strip()
    if not val:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        val = os.environ.get(name, "").strip()
    return val


def route(model: str) -> str:
    """Return the provider name serving `model`: anthropic|openai|xai|openrouter."""
    m = model.split("~")[0]  # tolerate the ~estimate suffix
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("openai:"):
        return "openai"
    if m.startswith("xai:") or m.startswith("grok"):
        return "xai"
    if "/" in m:
        return "openrouter"
    if m.startswith(("gpt", "o1", "o3", "o4", "chatgpt")):
        return "openai"
    return "anthropic"


def strip_provider_prefix(model: str) -> str:
    """Drop an explicit ``openai:``/``xai:`` prefix; pass other ids through."""
    for prefix in ("openai:", "xai:"):
        if model.startswith(prefix):
            return model[len(prefix):]
    return model


def openai_compatible_chat(
    provider_label: str,
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float = 0.0,
    max_retries: int = 3,
    extra_headers: dict | None = None,
) -> tuple[str, int, int]:
    """POST one chat completion to any OpenAI-compatible endpoint.

    Returns (text, prompt_tokens, completion_tokens). Retries 429/5xx with
    exponential backoff (1s, 2s, 4s) up to ``max_retries``. Raises RuntimeError
    on a missing key, a non-retryable HTTP error, or exhausted retries.
    """
    import time

    import requests

    if not api_key:
        raise RuntimeError(f"{provider_label}: API key not set.")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    resp = None
    for attempt in range(max_retries + 1):
        resp = requests.post(
            f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120,
        )
        if resp.status_code == 200:
            break
        if resp.status_code in (429, 500, 502, 503) and attempt < max_retries:
            time.sleep(2 ** attempt)
            continue
        raise RuntimeError(
            f"{provider_label} chat failed ({resp.status_code}): {resp.text[:300]}"
        )
    data = resp.json()
    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"{provider_label} response has no choices: {data!r}")
    text = (data["choices"][0]["message"]["content"] or "").strip()
    usage = data.get("usage", {}) or {}
    return (
        text,
        int(usage.get("prompt_tokens", 0) or 0),
        int(usage.get("completion_tokens", 0) or 0),
    )


def openai_chat(model: str, system: str, user: str, max_tokens: int,
                temperature: float = 0.0) -> tuple[str, int, int]:
    """Call the OpenAI API directly (model id may carry an ``openai:`` prefix)."""
    return openai_compatible_chat(
        "OpenAI", OPENAI_BASE, _env_key("OPENAI_API_KEY"),
        strip_provider_prefix(model), system, user, max_tokens, temperature,
    )


def xai_chat(model: str, system: str, user: str, max_tokens: int,
             temperature: float = 0.0) -> tuple[str, int, int]:
    """Call the xAI (Grok) API directly (model id may carry an ``xai:`` prefix)."""
    return openai_compatible_chat(
        "xAI", XAI_BASE, _env_key("XAI_API_KEY"),
        strip_provider_prefix(model), system, user, max_tokens, temperature,
    )


def key_status() -> dict[str, bool]:
    """Return which direct-provider API keys are present (for `markery model status`)."""
    return {
        "openai": bool(_env_key("OPENAI_API_KEY")),
        "xai": bool(_env_key("XAI_API_KEY")),
    }
