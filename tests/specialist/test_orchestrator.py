"""Tests for specialist/orchestrator.py — cross-specialist dispatch."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


def _make_project(tmp_path: Path, project_type: str = "match-review-essay") -> Path:
    """Create a minimal project structure under tmp_path/projects/<name>."""
    proj_root = tmp_path / "projects" / "test-proj"
    matches = proj_root / "matches"
    matches.mkdir(parents=True)
    (proj_root / "project.json").write_text(
        json.dumps({"type": project_type}) + "\n"
    )
    return proj_root


def test_enrich_signal_fields_delegates_to_patent_signals(tmp_path):
    proj_root = _make_project(tmp_path)
    candidates = proj_root / "matches" / "candidates.jsonl"
    candidates.write_text("")

    import markery.common.config as cfg_mod
    original = cfg_mod.ROOT
    cfg_mod.ROOT = tmp_path
    try:
        with patch(
            "markery.specialist.patent.signals.enrich_candidates", return_value=5
        ) as mock:
            from markery.specialist.orchestrator import enrich_signal_fields
            result = enrich_signal_fields(candidates)
    finally:
        cfg_mod.ROOT = original

    mock.assert_called_once_with(candidates)
    assert result == 5


def test_enrich_signal_fields_returns_zero_for_missing_file(tmp_path):
    proj_root = _make_project(tmp_path)
    candidates = proj_root / "matches" / "nonexistent.jsonl"

    import markery.common.config as cfg_mod
    original = cfg_mod.ROOT
    cfg_mod.ROOT = tmp_path
    try:
        with patch(
            "markery.specialist.patent.signals.enrich_candidates", return_value=0
        ) as mock:
            from markery.specialist.orchestrator import enrich_signal_fields
            result = enrich_signal_fields(candidates)
    finally:
        cfg_mod.ROOT = original

    mock.assert_called_once_with(candidates)
    assert result == 0


def test_enrich_signal_fields_passes_path_unchanged(tmp_path):
    proj_root = _make_project(tmp_path)
    candidates = proj_root / "matches" / "candidates.jsonl"
    received: list[Path] = []

    def _capture(path):
        received.append(path)
        return 0

    import markery.common.config as cfg_mod
    original = cfg_mod.ROOT
    cfg_mod.ROOT = tmp_path
    try:
        with patch("markery.specialist.patent.signals.enrich_candidates", side_effect=_capture):
            from markery.specialist.orchestrator import enrich_signal_fields
            enrich_signal_fields(candidates)
    finally:
        cfg_mod.ROOT = original

    assert received == [candidates]


def test_enrich_signal_fields_rejects_wrong_project_type(tmp_path):
    proj_root = _make_project(tmp_path, project_type="gallery-exploration")
    candidates = proj_root / "matches" / "candidates.jsonl"

    import markery.common.config as cfg_mod
    original = cfg_mod.ROOT
    cfg_mod.ROOT = tmp_path
    try:
        from markery.specialist.orchestrator import enrich_signal_fields
        raised = False
        try:
            enrich_signal_fields(candidates)
        except TypeError:
            raised = True
    finally:
        cfg_mod.ROOT = original

    assert raised, "Expected TypeError for wrong project type"


def test_project_type_returns_declared_type(tmp_path):
    proj_root = _make_project(tmp_path, project_type="match-review-essay")

    import markery.common.config as cfg_mod
    original = cfg_mod.ROOT
    cfg_mod.ROOT = tmp_path
    try:
        from markery.specialist.orchestrator import project_type
        from markery.common.project import ProjectType
        result = project_type(proj_root)
    finally:
        cfg_mod.ROOT = original

    assert result == ProjectType.MATCH_REVIEW_ESSAY


def test_project_type_raises_for_missing_project_json(tmp_path):
    proj_root = tmp_path / "no-project-json"
    proj_root.mkdir()

    from markery.specialist.orchestrator import project_type
    try:
        project_type(proj_root)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass
