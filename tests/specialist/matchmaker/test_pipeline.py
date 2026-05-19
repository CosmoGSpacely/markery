"""Unit tests for matchmaker pipeline state tracking."""

from __future__ import annotations

import json
from pathlib import Path

from markery.specialist.matchmaker.pipeline import (
    is_enriched,
    mark_enriched,
    mark_generated,
    mark_rescored,
    read_state,
)


def test_read_state_missing_file(tmp_path: Path):
    assert read_state(tmp_path / "no_such.json") == {}


def test_read_state_malformed_json(tmp_path: Path):
    p = tmp_path / "state.json"
    p.write_text("not json")
    assert read_state(p) == {}


def test_mark_generated_writes_fields(tmp_path: Path):
    p = tmp_path / "pipeline_state.json"
    mark_generated(p, candidate_count=100, scores=[0.3, 0.5, 0.7, 0.8])
    state = read_state(p)
    assert state["candidate_count"] == 100
    assert state["generated_at"] is not None
    assert state["enriched_at"] is None
    assert state["rescored_at"] is None
    assert state["enriched_count"] is None
    assert state["score_p50"] is not None
    assert state["score_p90"] is not None


def test_mark_generated_clears_enriched(tmp_path: Path):
    p = tmp_path / "pipeline_state.json"
    mark_generated(p, candidate_count=50, scores=[0.4])
    mark_enriched(p, enriched_count=50)
    assert is_enriched(p)
    # re-generate should clear enriched_at
    mark_generated(p, candidate_count=60, scores=[0.5])
    assert not is_enriched(p)


def test_mark_enriched_sets_timestamp(tmp_path: Path):
    p = tmp_path / "pipeline_state.json"
    mark_generated(p, candidate_count=10, scores=[0.5])
    assert not is_enriched(p)
    mark_enriched(p, enriched_count=10)
    assert is_enriched(p)
    state = read_state(p)
    assert state["enriched_count"] == 10
    assert state["rescored_at"] is None


def test_mark_enriched_clears_rescored(tmp_path: Path):
    p = tmp_path / "pipeline_state.json"
    mark_generated(p, candidate_count=10, scores=[0.5])
    mark_enriched(p, enriched_count=10)
    mark_rescored(p)
    assert read_state(p)["rescored_at"] is not None
    mark_enriched(p, enriched_count=10)
    assert read_state(p)["rescored_at"] is None


def test_mark_rescored_sets_timestamp(tmp_path: Path):
    p = tmp_path / "pipeline_state.json"
    mark_generated(p, candidate_count=5, scores=[0.6])
    mark_enriched(p, enriched_count=5)
    mark_rescored(p)
    state = read_state(p)
    assert state["rescored_at"] is not None


def test_is_enriched_false_when_missing(tmp_path: Path):
    assert not is_enriched(tmp_path / "no_such.json")


def test_percentile_empty_scores(tmp_path: Path):
    p = tmp_path / "pipeline_state.json"
    mark_generated(p, candidate_count=0, scores=[])
    state = read_state(p)
    assert state["score_p50"] is None
    assert state["score_p90"] is None


def test_state_file_is_valid_json(tmp_path: Path):
    p = tmp_path / "pipeline_state.json"
    mark_generated(p, candidate_count=3, scores=[0.4, 0.6, 0.8])
    mark_enriched(p, enriched_count=3)
    # must be parseable JSON with expected shape
    raw = json.loads(p.read_text())
    assert "generated_at" in raw
    assert "enriched_at" in raw
