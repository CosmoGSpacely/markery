"""Credential loading for Markery specialists."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str, hint: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise EnvironmentError(f"{key} not set in .env -- {hint}")
    return val


def load_epo_credentials() -> tuple[str, str]:
    """Return (consumer_key, consumer_secret) for EPO OPS OAuth2."""
    key    = _require_env("EPO_CONSUMER_KEY",    "register at https://developers.epo.org")
    secret = _require_env("EPO_CONSUMER_SECRET", "register at https://developers.epo.org")
    return key, secret


def load_tsdr_key() -> str:
    """Return USPTO API key for TSDR."""
    return _require_env("USPTO_API_KEY", "register at https://account.uspto.gov/api-manager/")


def load_odp_key() -> str:
    """Return the USPTO Open Data Portal API key (ID.me-linked) for text search.

    Distinct from the TSDR key: the ODP search API at api.uspto.gov needs an
    ID.me-verified account key passed as the X-API-KEY header. Get one at
    https://data.uspto.gov (USPTO.gov account + ID.me, then request an API key).
    """
    return _require_env("USPTO_ODP_API_KEY", "get an ODP key at https://data.uspto.gov (USPTO.gov + ID.me)")


def load_anthropic_key() -> str:
    """Return Anthropic API key for token counting and future inference."""
    return _require_env("ANTHROPIC_API_KEY", "register at https://console.anthropic.com")
