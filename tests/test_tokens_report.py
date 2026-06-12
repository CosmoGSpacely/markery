"""Tests for `markery tokens report` aggregation and the cache-health warning."""

from __future__ import annotations

import json

import pytest

from markery.common.tokens_report import (
    record_cost,
    load_records,
    build_report,
    _cache_hit_rate,
    _sum_fields,
)
from markery.common.tokens import cache_min_for, cache_health_warning


# ── pricing / cost ────────────────────────────────────────────────────────

def test_record_cost_haiku():
    rec = {"model": "claude-haiku-4-5-20251001",
           "prompt_tokens": 1_000_000, "completion_tokens": 0,
           "cache_read_tokens": 0, "cache_creation_tokens": 0}
    usd, unknown = record_cost(rec)
    assert not unknown
    assert usd == pytest.approx(1.0)  # $1/1M input


def test_record_cost_sonnet_with_cache():
    rec = {"model": "claude-sonnet-4-6",
           "prompt_tokens": 1_000_000, "completion_tokens": 1_000_000,
           "cache_read_tokens": 1_000_000, "cache_creation_tokens": 1_000_000}
    usd, _ = record_cost(rec)
    # 3 (prompt) + 15 (completion) + 0.30 (read 0.1x) + 3.75 (write 1.25x)
    assert usd == pytest.approx(3.0 + 15.0 + 0.30 + 3.75)


def test_record_cost_unknown_model_flags():
    usd, unknown = record_cost({"model": "gpt-4", "prompt_tokens": 100})
    assert unknown and usd == 0.0


def test_batch_record_costs_half():
    """Batch API bills at 50% — a batch record must cost exactly half the live one."""
    base = {"model": "claude-haiku-4-5", "prompt_tokens": 1_000_000,
            "completion_tokens": 1_000_000, "cache_read_tokens": 0,
            "cache_creation_tokens": 0}
    live, _ = record_cost(base)
    batch, _ = record_cost({**base, "batch": True})
    assert batch == pytest.approx(live * 0.5)


# ── aggregation ───────────────────────────────────────────────────────────

def test_load_records_missing_file(tmp_path):
    assert load_records(tmp_path / "nope.jsonl") == []


def test_cache_hit_rate():
    totals = {"prompt_tokens": 6000, "cache_read_tokens": 4000, "cache_creation_tokens": 0}
    assert _cache_hit_rate(totals) == pytest.approx(0.4)


def test_build_report_totals_and_grouping(tmp_path):
    log = tmp_path / "t.jsonl"
    recs = [
        {"specialist": "historian", "command": "draft", "model": "claude-haiku-4-5",
         "prompt_tokens": 2000, "completion_tokens": 800,
         "cache_read_tokens": 0, "cache_creation_tokens": 0},
        {"specialist": "librarian", "command": "extract", "model": "claude-sonnet-4-6",
         "prompt_tokens": 5000, "completion_tokens": 1000,
         "cache_read_tokens": 4000, "cache_creation_tokens": 0},
    ]
    log.write_text("\n".join(json.dumps(r) for r in recs))
    loaded = load_records(log)
    assert len(loaded) == 2
    report = build_report(loaded, group_by="command")
    assert "records:" in report
    assert "By command:" in report
    assert "draft" in report and "extract" in report


def test_build_report_empty():
    assert "No token records" in build_report([])


# ── cache-health warning ──────────────────────────────────────────────────

def test_cache_min_for_models():
    assert cache_min_for("claude-haiku-4-5-20251001") == 4096
    assert cache_min_for("claude-sonnet-4-6") == 2048
    assert cache_min_for("claude-sonnet-4-5") == 1024
    assert cache_min_for("some-unknown-model") == 4096  # conservative default


def test_cache_warning_fires_on_uncached_multicall():
    w = cache_health_warning("claude-haiku-4-5-20251001", n_calls=5, cache_read_tokens=0)
    assert w is not None
    assert "4096" in w


def test_cache_warning_silent_on_single_call():
    assert cache_health_warning("claude-haiku-4-5", n_calls=1, cache_read_tokens=0) is None


def test_cache_warning_silent_when_cache_hit():
    assert cache_health_warning("claude-haiku-4-5", n_calls=5, cache_read_tokens=4096) is None
