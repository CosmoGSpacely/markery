"""Project root resolution and shared database paths.

Project type definitions and path contracts have moved to
markery.common.project. Import Project from there.
"""

from __future__ import annotations

import os
from pathlib import Path


def _find_root() -> Path:
    """Resolve the project root.

    Honour MARKERY_ROOT if set (used by hermetic tests to point the CLI at a
    synthetic repo); otherwise walk up from this file until pyproject.toml.
    """
    env = os.environ.get("MARKERY_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not locate project root (no pyproject.toml found)")


ROOT = _find_root()

# Unified site root: the Markery portal and every project's nested site live here.
SITE_ROOT = ROOT / "site"

# The paid model used only when a caller explicitly opts in (--model or
# MARKERY_MODEL). The dated ID is pinned for reproducibility.
# Note: Haiku 4.5's cacheable-prefix minimum is 4096 tokens (see common/llm.py).
DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# Free-by-default model for unattended/agentic steps so the spawn loop and
# high-volume scoring never silently bill a paid model. Verified responsive
# (matches openrouter.DEFAULT_TEST_MODEL). Opt into a paid model per-call with
# --model or per-session with MARKERY_MODEL.
FREE_MODEL = "openai/gpt-oss-120b:free"

# Ordered free models tried in turn (D077): if the first is rate-limited upstream,
# a different free model/provider often is not — so the agentic loops self-heal
# while staying free. FREE_MODEL is first (kept in sync).
FREE_MODELS = [
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]


def resolve_model(explicit: str | None = None) -> str:
    """Which single LLM to use: explicit arg > MARKERY_MODEL env > FREE_MODEL.

    Free-by-default. This is the single resolution point for callers that need
    exactly one model; agentic loops use model_chain() for rate-limit resilience.
    """
    if explicit:
        return explicit
    return os.environ.get("MARKERY_MODEL") or FREE_MODEL


def model_chain(explicit: str | None = None) -> list[str]:
    """Ordered models to try (D077 rate-limit resilience): explicit > MARKERY_MODEL
    > free chain (+ an opt-in paid backstop).

    An explicit --model or MARKERY_MODEL is honoured exactly (no surprise fallback).
    Otherwise the free models are tried in order; a paid backstop is appended only
    when MARKERY_ALLOW_PAID is set (default off → unattended loops stay free or
    degrade gracefully, never silently bill). The paid model is MARKERY_PAID_MODEL
    or DEFAULT_MODEL.
    """
    if explicit:
        return [explicit]
    env = os.environ.get("MARKERY_MODEL")
    if env:
        return [env]
    chain = list(FREE_MODELS)
    if os.environ.get("MARKERY_ALLOW_PAID"):
        chain.append(os.environ.get("MARKERY_PAID_MODEL") or DEFAULT_MODEL)
    return chain

# Data directory holding the corpus DBs. Honour MARKERY_DATA_DIR if set (hermetic
# tests point this at a synthetic-fixture dir); otherwise it is ROOT/data.
_DATA_DIR = (
    Path(os.environ["MARKERY_DATA_DIR"]).expanduser().resolve()
    if os.environ.get("MARKERY_DATA_DIR")
    else ROOT / "data"
)

DB = {
    "patents":    _DATA_DIR / "patents.duckdb",
    "trademarks": _DATA_DIR / "trademarks.duckdb",
    "entities":   _DATA_DIR / "entities.duckdb",
}

# The canonical registry (data/entities.duckdb) is gitignored like the corpus DBs,
# but — unlike the rebuildable corpus — it holds irreplaceable curation. Its
# durability/diff artifact is a deterministic, git-tracked CSV export regenerated
# on every registry write (Phase 34, Decision 1). Lives at repo root, always tracked.
REGISTRY_DIR = ROOT / "registry"

# Record-image assets (mark drawings, patent figures) live as files alongside the
# DBs (Phase 28 P3 — externalized from BLOBs). The DB rows reference paths relative
# to this directory.
ASSETS_DIR = _DATA_DIR / "assets"

_SETUP_HINTS = {
    "patents":    "Run 'markery patent build' to populate patents.duckdb.",
    "trademarks": "Run 'markery trademark build' to populate trademarks.duckdb.",
    "entities":   "Copy or create data/entities.duckdb with the entity registry.",
}


def require_db(name: str) -> "Path":
    """Return the DB path for name, or exit with a clear setup hint.

    Call this at CLI entry points before opening a DuckDB connection.
    """
    import sys
    path = DB[name]
    if not path.exists():
        print(
            f"Database '{name}' not found at {path}.\n"
            f"{_SETUP_HINTS.get(name, 'Check SETUP.md for instructions.')}",
            file=sys.stderr,
        )
        sys.exit(1)
    return path
