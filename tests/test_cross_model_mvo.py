"""Regression guard for the cross-model MVO benchmark (Phase 22 P3 / D061).

These tests do NOT make API calls. They protect two things:
  1. the harness's table renderer keeps its shape, and
  2. the committed benchmark results keep showing every model passing every
     MVO validator — i.e. the model-agnosticism claim stays proven in-repo.

The live benchmark itself is `tests/benchmarks/cross_model_mvo.py`, run manually
(it needs ANTHROPIC_API_KEY and costs a few cents); it writes a dated results
JSONL that this test reads.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_BENCH_DIR = Path(__file__).resolve().parents[1] / "tests" / "benchmarks"
_HARNESS = _BENCH_DIR / "cross_model_mvo.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("cross_model_mvo", _HARNESS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_render_table_shape():
    mod = _load_harness()
    table = mod.render_table({
        "claude-haiku-4-5-20251001": {
            "validator_pass": 6, "validator_total": 6,
            "prompt_tokens": 16721, "completion_tokens": 3861,
            "cache_read_tokens": 0, "usd": 0.036,
        },
    })
    assert table.startswith("| Model |")
    assert "6/6" in table
    assert "$0.0360" in table
    assert "`claude-haiku-4-5-20251001`" in table


def test_fixtures_span_all_three_projects():
    mod = _load_harness()
    projects = {p for p, _ in mod.FIXTURES}
    assert projects == {"information-systems", "radio-pioneers", "animal-marks-1930"}
    assert len(mod.MODELS) >= 2


def _latest_results() -> Path | None:
    files = sorted(_BENCH_DIR.glob("cross-model-mvo-*.jsonl"))
    return files[-1] if files else None


@pytest.mark.skipif(_latest_results() is None,
                    reason="no committed cross-model benchmark results yet")
def test_committed_results_show_full_validator_pass():
    """The proven property: in the latest committed run, every model passed
    every MVO validator. If a future run regresses, this fails loudly."""
    summary = json.loads(_latest_results().read_text().splitlines()[0])["summary"]
    assert len(summary) >= 2, "benchmark must cover ≥2 models"
    for model, s in summary.items():
        assert s["validator_total"] > 0
        assert s["validator_pass"] == s["validator_total"], (
            f"{model}: {s['validator_pass']}/{s['validator_total']} validators passed"
        )
