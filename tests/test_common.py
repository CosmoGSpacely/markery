"""Tests for common layer: auth, project, config."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# common/auth.py
# ---------------------------------------------------------------------------

def test_load_epo_credentials_returns_values(monkeypatch):
    monkeypatch.setenv("EPO_CONSUMER_KEY",    "testkey")
    monkeypatch.setenv("EPO_CONSUMER_SECRET", "testsecret")
    from markery.common.auth import load_epo_credentials
    key, secret = load_epo_credentials()
    assert key    == "testkey"
    assert secret == "testsecret"


def test_load_epo_credentials_raises_when_missing(monkeypatch):
    monkeypatch.delenv("EPO_CONSUMER_KEY",    raising=False)
    monkeypatch.delenv("EPO_CONSUMER_SECRET", raising=False)
    from markery.common.auth import load_epo_credentials
    with pytest.raises(EnvironmentError, match="EPO_CONSUMER_KEY"):
        load_epo_credentials()


def test_load_tsdr_key_returns_value(monkeypatch):
    monkeypatch.setenv("USPTO_API_KEY", "myapikey")
    from markery.common.auth import load_tsdr_key
    assert load_tsdr_key() == "myapikey"


def test_load_tsdr_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("USPTO_API_KEY", raising=False)
    from markery.common.auth import load_tsdr_key
    with pytest.raises(EnvironmentError, match="USPTO_API_KEY"):
        load_tsdr_key()


# ---------------------------------------------------------------------------
# common/project.py
# ---------------------------------------------------------------------------

def _make_project(tmp_path: Path, name: str = "test-proj",
                  project_type: str = "match-review-essay") -> Path:
    root = tmp_path / "projects" / name
    (root / "matches").mkdir(parents=True)
    (root / "project.json").write_text(
        json.dumps({"type": project_type}) + "\n"
    )
    return root


def _patch_project_root(tmp_path: Path):
    import markery.common.project as proj_mod
    return patch.object(proj_mod, "ROOT", tmp_path)


def test_load_project_returns_typed_project(tmp_path):
    _make_project(tmp_path)
    from markery.common.project import load_project, ProjectType
    with _patch_project_root(tmp_path):
        proj = load_project(tmp_path / "projects" / "test-proj")
    assert proj.type == ProjectType.MATCH_REVIEW_ESSAY
    assert proj.name == "test-proj"


def test_load_project_raises_for_missing_json(tmp_path):
    root = tmp_path / "no-json"
    root.mkdir()
    from markery.common.project import load_project
    with pytest.raises(FileNotFoundError, match="project.json"):
        load_project(root)


def test_load_project_raises_for_unknown_type(tmp_path):
    root = tmp_path / "bad-type"
    root.mkdir()
    (root / "project.json").write_text(json.dumps({"type": "nonexistent-type"}))
    from markery.common.project import load_project
    with pytest.raises(ValueError, match="Unknown project type"):
        load_project(root)


def test_load_project_raises_for_missing_type_field(tmp_path):
    root = tmp_path / "no-type-field"
    root.mkdir()
    (root / "project.json").write_text(json.dumps({"other": "value"}))
    from markery.common.project import load_project
    with pytest.raises(ValueError, match="missing the 'type' field"):
        load_project(root)


def test_require_project_exits_for_missing_dir(tmp_path, capsys):
    from markery.common.project import require_project
    with _patch_project_root(tmp_path):
        with pytest.raises(SystemExit):
            require_project("nonexistent")
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_require_project_exits_for_missing_project_json(tmp_path, capsys):
    root = tmp_path / "projects" / "orphan"
    root.mkdir(parents=True)
    from markery.common.project import require_project
    with _patch_project_root(tmp_path):
        with pytest.raises(SystemExit):
            require_project("orphan")
    captured = capsys.readouterr()
    assert "project.json" in captured.err


def test_require_project_returns_project_on_success(tmp_path):
    _make_project(tmp_path)
    from markery.common.project import require_project, ProjectType
    with _patch_project_root(tmp_path):
        proj = require_project("test-proj")
    assert proj.type == ProjectType.MATCH_REVIEW_ESSAY


def test_detect_project_type_match_review_essay(tmp_path):
    root = tmp_path / "proj"
    (root / "matches").mkdir(parents=True)
    (root / "matches" / "confirmed.jsonl").write_text("")
    from markery.common.project import detect_project_type, ProjectType
    assert detect_project_type(root) == ProjectType.MATCH_REVIEW_ESSAY


def test_detect_project_type_gallery_exploration(tmp_path):
    root = tmp_path / "proj"
    (root / "essays").mkdir(parents=True)
    from markery.common.project import detect_project_type, ProjectType
    assert detect_project_type(root) == ProjectType.GALLERY_EXPLORATION


def test_detect_project_type_returns_none_for_empty(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    from markery.common.project import detect_project_type
    assert detect_project_type(root) is None


def test_project_path_properties_match_review_essay(tmp_path):
    _make_project(tmp_path)
    from markery.common.project import load_project
    with _patch_project_root(tmp_path):
        proj = load_project(tmp_path / "projects" / "test-proj")
    assert proj.candidates.name == "candidates.jsonl"
    assert proj.confirmed.name  == "confirmed.jsonl"
    assert proj.content.name    == "content"


def test_project_path_type_guard_raises_for_wrong_type(tmp_path):
    _make_project(tmp_path, project_type="gallery-exploration")
    from markery.common.project import load_project
    with _patch_project_root(tmp_path):
        proj = load_project(tmp_path / "projects" / "test-proj")
    with pytest.raises(TypeError, match="match-review-essay"):
        _ = proj.candidates


def test_validate_patent_no_accepts_valid(capsys):
    from markery.common.project import validate_patent_no
    assert validate_patent_no("US1261167A") == "US1261167A"
    assert validate_patent_no("us1261167a") == "US1261167A"


def test_validate_patent_no_rejects_malformed(capsys):
    from markery.common.project import validate_patent_no
    with pytest.raises(SystemExit):
        validate_patent_no("1261167")
    captured = capsys.readouterr()
    assert "Invalid patent number" in captured.err


def test_validate_serial_no_accepts_valid():
    from markery.common.project import validate_serial_no
    assert validate_serial_no("71246709") == "71246709"


def test_validate_serial_no_rejects_malformed(capsys):
    from markery.common.project import validate_serial_no
    with pytest.raises(SystemExit):
        validate_serial_no("abc123")
    captured = capsys.readouterr()
    assert "Invalid serial number" in captured.err


# ---------------------------------------------------------------------------
# common/config.py
# ---------------------------------------------------------------------------

def test_db_paths_are_under_data_dir():
    from markery.common.config import DB, ROOT
    for name, path in DB.items():
        assert path.parent == ROOT / "data", f"{name} DB not in data/"
        assert path.suffix == ".duckdb"


def test_require_db_exits_for_missing_file(tmp_path, capsys):
    import markery.common.config as cfg_mod
    original = cfg_mod.DB.copy()
    cfg_mod.DB["patents"] = tmp_path / "nonexistent.duckdb"
    try:
        from markery.common.config import require_db
        with pytest.raises(SystemExit):
            require_db("patents")
    finally:
        cfg_mod.DB["patents"] = original["patents"]
    captured = capsys.readouterr()
    assert "patents" in captured.err


def test_require_db_returns_path_when_exists(tmp_path):
    import markery.common.config as cfg_mod
    fake_db = tmp_path / "test.duckdb"
    fake_db.write_bytes(b"")
    original = cfg_mod.DB.copy()
    cfg_mod.DB["patents"] = fake_db
    try:
        from markery.common.config import require_db
        result = require_db("patents")
    finally:
        cfg_mod.DB["patents"] = original["patents"]
    assert result == fake_db
