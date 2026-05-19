"""Tests for specialist/orchestrator.py — cross-specialist dispatch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def test_enrich_signal_fields_delegates_to_patent_signals(tmp_path):
    p = tmp_path / "candidates.jsonl"
    p.write_text("")
    with patch(
        "markery.specialist.patent.signals.enrich_candidates", return_value=5
    ) as mock:
        from markery.specialist.orchestrator import enrich_signal_fields
        result = enrich_signal_fields(p)
    mock.assert_called_once_with(p)
    assert result == 5


def test_enrich_signal_fields_returns_zero_for_missing_file(tmp_path):
    """Missing candidates file → patent signals returns 0."""
    p = tmp_path / "nonexistent.jsonl"
    with patch(
        "markery.specialist.patent.signals.enrich_candidates", return_value=0
    ) as mock:
        from markery.specialist.orchestrator import enrich_signal_fields
        result = enrich_signal_fields(p)
    mock.assert_called_once_with(p)
    assert result == 0


def test_enrich_signal_fields_passes_path_unchanged(tmp_path):
    """Path object is forwarded to the patent specialist without modification."""
    p = tmp_path / "candidates.jsonl"
    received: list[Path] = []

    def _capture(path):
        received.append(path)
        return 0

    with patch("markery.specialist.patent.signals.enrich_candidates", side_effect=_capture):
        from markery.specialist.orchestrator import enrich_signal_fields
        enrich_signal_fields(p)

    assert received == [p]
