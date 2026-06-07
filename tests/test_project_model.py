"""Tests for Phase 19 P4: D043 (per-project model field in project.json)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


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
