"""Tests for Phase 19 P4: D043 (per-project model field in project.json).
Tests for Phase 20 P1: prior_brand_serials gap-neutralisation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project_json(path: Path, extra: dict | None = None) -> Path:
    data = {"type": "match-review-essay"}
    if extra:
        data.update(extra)
    pjson = path / "project.json"
    pjson.write_text(json.dumps(data), encoding="utf-8")
    return pjson


# ---------------------------------------------------------------------------
# D043 — load_project reads the model field
# ---------------------------------------------------------------------------

class TestProjectModelField:
    def test_model_present_in_loaded_project(self, tmp_path):
        _make_project_json(tmp_path, {"model": "claude-haiku-4-5-20251001"})
        from markery.common.project import load_project
        proj = load_project(tmp_path)
        assert proj.model == "claude-haiku-4-5-20251001"

    def test_model_none_when_absent(self, tmp_path):
        _make_project_json(tmp_path)
        from markery.common.project import load_project
        proj = load_project(tmp_path)
        assert proj.model is None

    def test_env_already_set_not_overridden(self, tmp_path, monkeypatch):
        """When MARKERY_MODEL is already in the environment, project.json must not override it."""
        from markery.common.config import ROOT
        proj_name = "tmp-test-model-proj"
        proj_dir = ROOT / "projects" / proj_name
        proj_dir.mkdir(parents=True, exist_ok=True)
        try:
            _make_project_json(proj_dir, {"model": "claude-haiku-4-5-20251001"})
            monkeypatch.setenv("MARKERY_MODEL", "claude-sonnet-4-6")

            from markery.cli import _try_inject_project_model
            _try_inject_project_model([proj_name])

            assert os.environ["MARKERY_MODEL"] == "claude-sonnet-4-6"
        finally:
            import shutil
            shutil.rmtree(proj_dir, ignore_errors=True)

    def test_model_injected_into_env_when_set(self, tmp_path, monkeypatch):
        """When project.json has model and env is absent, _try_inject_project_model sets it."""
        from markery.common.config import ROOT
        proj_name = "tmp-test-model-inject"
        proj_dir = ROOT / "projects" / proj_name
        proj_dir.mkdir(parents=True, exist_ok=True)
        try:
            _make_project_json(proj_dir, {"model": "claude-haiku-4-5-20251001"})
            monkeypatch.delenv("MARKERY_MODEL", raising=False)

            from markery.cli import _try_inject_project_model
            _try_inject_project_model(["card", proj_name, "some-slug"])

            assert os.environ.get("MARKERY_MODEL") == "claude-haiku-4-5-20251001"
        finally:
            import shutil
            shutil.rmtree(proj_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Phase 20 P1 — prior_brand_serials gap-neutralisation
# ---------------------------------------------------------------------------

class TestPriorBrandSerials:
    def test_prior_brand_serials_loaded_from_project_json(self, tmp_path):
        _make_project_json(tmp_path, {"prior_brand_serials": ["71164631", "71289592"]})
        from markery.common.project import load_project
        proj = load_project(tmp_path)
        assert proj.prior_brand_serials == ["71164631", "71289592"]

    def test_prior_brand_serials_empty_when_absent(self, tmp_path):
        _make_project_json(tmp_path)
        from markery.common.project import load_project
        proj = load_project(tmp_path)
        assert proj.prior_brand_serials == []

    def test_date_score_negative_gap_neutralised_when_prior_brand(self):
        """A negative-gap pair returns 0.0 when prior_brand=True."""
        from markery.specialist.matchmaker.score import date_score
        # trademark filed before patent grant → normally negative
        grant = date(1927, 8, 9)
        filing = date(1922, 5, 29)
        raw = date_score(grant, filing)
        assert raw < 0.0
        neutralised = date_score(grant, filing, prior_brand=True)
        assert neutralised == 0.0

    def test_date_score_positive_gap_unchanged_when_prior_brand(self):
        """A positive-gap pair is not affected by prior_brand=True."""
        from markery.specialist.matchmaker.score import date_score
        grant = date(1922, 5, 29)
        filing = date(1927, 8, 9)
        normal = date_score(grant, filing)
        with_flag = date_score(grant, filing, prior_brand=True)
        assert normal == with_flag
        assert with_flag > 0.0

    def test_total_score_prior_brand_serial_in_set_neutralises_gap(self):
        """total_score with prior_brand=True gives gap_score ≥ 0.0 for negative-gap pair."""
        from markery.specialist.matchmaker.score import total_score
        grant = date(1927, 8, 9)
        filing = date(1922, 5, 29)
        score_normal = total_score(grant, filing, ["F41A"])
        score_prior = total_score(grant, filing, ["F41A"], prior_brand=True)
        assert score_prior > score_normal
        assert score_prior >= 0.0
