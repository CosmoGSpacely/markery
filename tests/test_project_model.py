"""Tests for Phase 19 P4: D043 (per-project model field in project.json).
Tests for Phase 20 P1: prior_brand_serials gap-neutralisation.
Tests for Phase 21 P3: project onboard command.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from unittest.mock import patch

import duckdb
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


# ---------------------------------------------------------------------------
# Phase 21 P3 — D027: markery project onboard
# ---------------------------------------------------------------------------

def _setup_onboard_dbs(tmp_path: Path, pat_assignee: str = "TEST CORP") -> dict:
    """Create minimal DuckDB files for onboard tests. Returns {key: path}."""
    pat_db = tmp_path / "patents.duckdb"
    tm_db  = tmp_path / "trademarks.duckdb"
    ent_db = tmp_path / "entities.duckdb"

    conn = duckdb.connect(str(pat_db))
    conn.execute(
        "CREATE TABLE patents (patent_no VARCHAR, title VARCHAR, app_dt DATE, "
        "grant_dt DATE, abstract VARCHAR, assignee_name VARCHAR, "
        "assignee_city VARCHAR, assignee_state VARCHAR)"
    )
    if pat_assignee:
        conn.execute(
            "INSERT INTO patents VALUES ('US1234567A', 'Widget', NULL, NULL, NULL, ?, NULL, NULL)",
            [pat_assignee],
        )
    conn.close()

    conn = duckdb.connect(str(tm_db))
    conn.execute(
        "CREATE TABLE owner (serial_no INTEGER, own_name VARCHAR, own_seq INTEGER)"
    )
    conn.close()

    conn = duckdb.connect(str(ent_db))
    conn.execute(
        "CREATE TABLE company_entity (entity_id INTEGER PRIMARY KEY, "
        "canonical_name VARCHAR, entity_type VARCHAR, industry VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE entity_name_variant (variant_id INTEGER PRIMARY KEY, "
        "entity_id INTEGER, variant_name VARCHAR, source VARCHAR)"
    )
    conn.close()

    return {"patents": pat_db, "trademarks": tm_db, "entities": ent_db}


def _make_project(proj_root: Path, entity_name: str = "Test Corp",
                   variant_name: str = "TEST CORP", source: str = "patent_assignee") -> None:
    proj_root.mkdir(parents=True, exist_ok=True)
    (proj_root / "entities.csv").write_text(
        "entity_id,canonical_name,entity_type,industry\n"
        f"1,{entity_name},manufacturer,test\n",
        encoding="utf-8",
    )
    (proj_root / "variants.csv").write_text(
        "entity_id,variant_name,source\n"
        f"1,{variant_name},{source}\n",
        encoding="utf-8",
    )
    (proj_root / "project.json").write_text(
        json.dumps({"type": "match-review-essay", "class_hints": ["H01J"]}),
        encoding="utf-8",
    )


def _run_onboard(project_name: str, proj_root: Path, db_paths: dict):
    from markery.common import project_cli
    import markery.common.config as cfg_mod
    import markery.common.project as proj_mod

    # ROOT needs to be the parent of projects/<name>
    fake_root = proj_root.parent.parent

    args = argparse.Namespace(project=project_name)
    with (
        patch.object(cfg_mod, "ROOT", fake_root),
        patch.object(proj_mod, "ROOT", fake_root),
        patch.object(project_cli, "ROOT", fake_root),
        patch.dict(cfg_mod.DB, db_paths),
    ):
        project_cli.cmd_onboard(args)


class TestOnboard:
    def test_passes_for_correctly_configured_project(self, tmp_path, capsys):
        db_paths = _setup_onboard_dbs(tmp_path)
        proj_root = tmp_path / "projects" / "test-proj"
        _make_project(proj_root)

        _run_onboard("test-proj", proj_root, db_paths)

        out = capsys.readouterr().out
        assert "Onboarding PASSED" in out
        assert "FAIL" not in out

    def test_fails_when_variant_has_zero_matches(self, tmp_path):
        db_paths = _setup_onboard_dbs(tmp_path, pat_assignee="REAL CORP")
        proj_root = tmp_path / "projects" / "test-proj"
        _make_project(proj_root, variant_name="MISSING CORP")

        with pytest.raises(SystemExit) as exc:
            _run_onboard("test-proj", proj_root, db_paths)
        assert exc.value.code == 1

    def test_fail_message_mentions_zero_match_variant(self, tmp_path, capsys):
        db_paths = _setup_onboard_dbs(tmp_path, pat_assignee="REAL CORP")
        proj_root = tmp_path / "projects" / "test-proj"
        _make_project(proj_root, variant_name="MISSING CORP")

        with pytest.raises(SystemExit):
            _run_onboard("test-proj", proj_root, db_paths)

        out = capsys.readouterr().out
        assert "NO MATCH" in out
        assert "Onboarding FAILED" in out

    def test_fails_when_entity_id_conflicts_with_different_canonical(self, tmp_path, capsys):
        db_paths = _setup_onboard_dbs(tmp_path)
        # Pre-populate entities DB with entity_id=1 under a different name
        conn = duckdb.connect(str(db_paths["entities"]))
        conn.execute("INSERT INTO company_entity VALUES (1, 'Other Corp', NULL, NULL)")
        conn.close()

        proj_root = tmp_path / "projects" / "test-proj"
        _make_project(proj_root, entity_name="Test Corp")

        with pytest.raises(SystemExit) as exc:
            _run_onboard("test-proj", proj_root, db_paths)
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "ID conflict" in out

    def test_passes_when_entity_id_matches_same_canonical(self, tmp_path, capsys):
        db_paths = _setup_onboard_dbs(tmp_path)
        # Same entity already in DB (re-onboarding same project)
        conn = duckdb.connect(str(db_paths["entities"]))
        conn.execute("INSERT INTO company_entity VALUES (1, 'Test Corp', NULL, NULL)")
        conn.close()

        proj_root = tmp_path / "projects" / "test-proj"
        _make_project(proj_root, entity_name="Test Corp")

        _run_onboard("test-proj", proj_root, db_paths)

        out = capsys.readouterr().out
        assert "Onboarding PASSED" in out

    def test_fails_when_entities_csv_missing(self, tmp_path):
        db_paths = _setup_onboard_dbs(tmp_path)
        proj_root = tmp_path / "projects" / "test-proj"
        proj_root.mkdir(parents=True)
        # No entities.csv

        with pytest.raises(SystemExit) as exc:
            _run_onboard("test-proj", proj_root, db_paths)
        assert exc.value.code == 1

    def test_coverage_counts_shown_in_output(self, tmp_path, capsys):
        db_paths = _setup_onboard_dbs(tmp_path, pat_assignee="TEST CORP")
        proj_root = tmp_path / "projects" / "test-proj"
        _make_project(proj_root)

        _run_onboard("test-proj", proj_root, db_paths)

        out = capsys.readouterr().out
        assert "patents=" in out
        assert "trademarks=" in out
