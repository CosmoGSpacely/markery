"""OpenRouter provider integration (OpenAI-compatible chat completions).

Markery is model-agnostic; this module lets a project route specialist LLM calls
to an OpenRouter model (e.g. a free model) instead of Anthropic, to test the
agnosticism thesis on a non-Anthropic provider.

Routing rule (see common/llm.py): a model id containing "/" is an OpenRouter
slug (e.g. ``meta-llama/llama-3.3-70b-instruct:free``); a ``claude-*`` id is
Anthropic.

Key handling
------------
The account holder has a **provisioning (management) key**, which cannot make
inference calls — it only manages runtime keys via the Keys API. So:

    OPENROUTER_PROVISIONING_KEY   (.env, gitignored)  → mints a runtime key
    .openrouter-key               (repo root, gitignored) → caches the runtime key
    OPENROUTER_API_KEY            (.env, optional)   → use this runtime key directly

``runtime_key()`` resolves in that order: an explicit ``OPENROUTER_API_KEY``
wins; else the cached file; else one is minted from the provisioning key and
cached. Free models cost $0, so no spend limit is set by default.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

API_BASE = "https://openrouter.ai/api/v1"
# gpt-oss-120b:free verified responsive 2026-06-13; llama-3.3-70b:free and several
# others are intermittently rate-limited upstream (Venice) for free traffic.
DEFAULT_TEST_MODEL = "openai/gpt-oss-120b:free"
_RUNTIME_KEY_NAME = "markery-runtime"


def _cache_path() -> Path:
    from markery.common.config import ROOT
    return ROOT / ".openrouter-key"


def is_openrouter_model(model: str) -> bool:
    """True if `model` is an OpenRouter slug (provider/model form), not a Claude id."""
    return "/" in model


def _provisioning_key() -> str:
    key = os.environ.get("OPENROUTER_PROVISIONING_KEY", "").strip()
    if not key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        key = os.environ.get("OPENROUTER_PROVISIONING_KEY", "").strip()
    return key


def mint_runtime_key(name: str = _RUNTIME_KEY_NAME, limit: float | None = None) -> str:
    """Create a runtime inference key from the provisioning key via the Keys API.

    Returns the secret key string (``sk-or-v1-…``), shown only once by OpenRouter.
    Raises RuntimeError if no provisioning key is set or the request fails.
    """
    import requests

    prov = _provisioning_key()
    if not prov:
        raise RuntimeError(
            "OPENROUTER_PROVISIONING_KEY not set. Add your OpenRouter provisioning "
            "(management) key to .env."
        )
    body: dict = {"name": name}
    if limit is not None:
        body["limit"] = limit
    resp = requests.post(
        f"{API_BASE}/keys",
        headers={"Authorization": f"Bearer {prov}", "Content-Type": "application/json"},
        json=body,
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"OpenRouter key creation failed ({resp.status_code}): {resp.text[:300]}"
        )
    data = resp.json()
    secret = data.get("key", "")
    if not secret:
        raise RuntimeError(f"OpenRouter key response missing 'key' field: {data!r}")
    return secret


def runtime_key(allow_mint: bool = True) -> str | None:
    """Resolve a usable runtime inference key.

    Order: ``OPENROUTER_API_KEY`` env → cached ``.openrouter-key`` file → mint from
    the provisioning key (and cache it). Returns None if none available and minting
    is disabled or no provisioning key is set.
    """
    explicit = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if explicit:
        return explicit

    cache = _cache_path()
    if cache.exists():
        cached = cache.read_text(encoding="utf-8").strip()
        if cached:
            return cached

    if not allow_mint or not _provisioning_key():
        return None

    secret = mint_runtime_key()
    try:
        cache.write_text(secret + "\n", encoding="utf-8")
        cache.chmod(0o600)
    except OSError:
        pass
    return secret


def chat(
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float = 0.0,
    max_retries: int = 3,
) -> tuple[str, int, int]:
    """Send one chat-completion request to OpenRouter.

    Returns (text, prompt_tokens, completion_tokens). OpenRouter free models do
    not support Anthropic prompt caching, so there are no cache token fields.

    Transient upstream throttling (HTTP 429) and provider 5xx errors are retried
    with exponential backoff (1s, 2s, 4s) up to ``max_retries`` — free models are
    frequently rate-limited upstream, so a single 429 should not abort a run.
    Raises RuntimeError if no runtime key can be resolved or all attempts fail.
    """
    import time

    import requests

    key = runtime_key()
    if not key:
        raise RuntimeError(
            "No OpenRouter runtime key. Set OPENROUTER_API_KEY, or set "
            "OPENROUTER_PROVISIONING_KEY in .env and run 'markery model mint'."
        )
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
            f"{API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        if resp.status_code == 200:
            break
        if resp.status_code in (429, 500, 502, 503) and attempt < max_retries:
            time.sleep(2 ** attempt)
            continue
        raise RuntimeError(
            f"OpenRouter chat failed ({resp.status_code}): {resp.text[:300]}"
        )
    data = resp.json()
    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"OpenRouter response has no choices: {data!r}")
    text = (data["choices"][0]["message"]["content"] or "").strip()
    usage = data.get("usage", {}) or {}
    return (
        text,
        int(usage.get("prompt_tokens", 0) or 0),
        int(usage.get("completion_tokens", 0) or 0),
    )
