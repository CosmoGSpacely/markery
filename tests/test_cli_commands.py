"""In-process happy-path coverage for read-only CLI commands.

Drives markery.cli.main() against the synthetic repo (config patched in-process
so the handler bodies count toward coverage). Read-only commands only — no
network, no LLM, no writes to the real tree.
"""

from __future__ import annotations

import sys

import pytest

from tests.fixtures.synthetic import build_synthetic_repo


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Synthetic repo with config patched across the modules these commands import."""
    r = build_synthetic_repo(tmp_path)

    import markery.common.config as cfg
    import markery.common.project as pm
    import markery.specialist.historian.status as status_mod
    import markery.common.project_cli as project_cli

    monkeypatch.setattr(cfg, "ROOT", r.root)
    monkeypatch.setattr(cfg, "SITE_ROOT", r.root / "site")
    monkeypatch.setattr(cfg, "ASSETS_DIR", r.assets_dir)
    monkeypatch.setattr(pm, "ROOT", r.root)
    monkeypatch.setattr(status_mod, "ROOT", r.root)
    monkeypatch.setattr(project_cli, "ROOT", r.root)
    for key in ("patents", "trademarks", "entities"):
        monkeypatch.setitem(cfg.DB, key, r.data_dir / f"{key}.duckdb")
    return r


def _run(monkeypatch, argv: list[str]) -> int:
    from markery.cli import main
    monkeypatch.setattr(sys, "argv", ["markery", *argv])
    try:
        main()
        return 0
    except SystemExit as e:
        return 0 if e.code is None else int(e.code)


def test_status(repo, monkeypatch, capsys):
    assert _run(monkeypatch, ["status"]) == 0
    out = capsys.readouterr().out
    assert "Markery Status" in out
    assert repo.project in out
    assert "case_file" in out  # DB table counts surfaced


def test_project_onboard(repo, monkeypatch, capsys):
    assert _run(monkeypatch, ["project", "onboard", repo.project]) == 0
    out = capsys.readouterr().out
    # Onboard surfaces the project's entity/variant/coverage state.
    assert "Synthex" in out or "synthex" in out.lower()


def test_historian_prepare(repo, monkeypatch, capsys):
    assert _run(monkeypatch, ["historian", "prepare", repo.project]) == 0
    out = capsys.readouterr().out
    assert "BRIEF.md" in out
    brief = repo.root / "projects" / repo.project / "BRIEF.md"
    assert brief.exists()


def test_matchmaker_list(repo, monkeypatch, capsys):
    assert _run(monkeypatch, ["matchmaker", "list"]) == 0
    out = capsys.readouterr().out
    assert "Synthex" in out


def test_matchmaker_register_dry_run_then_confirm(repo, monkeypatch, capsys):
    # Dry run proposes variants for a new canonical, writes nothing.
    assert _run(monkeypatch, ["matchmaker", "register", "Synthex Works",
                              "--min-score", "0.5"]) == 0
    out = capsys.readouterr().out
    assert "Dry run" in out and "patent_assignee" in out
    # Confirm writes the new entity.
    assert _run(monkeypatch, ["matchmaker", "register", "Synthex Works",
                              "--min-score", "0.5", "--confirm"]) == 0
    out = capsys.readouterr().out
    assert "created" in out


def test_matchmaker_register_people_confirm(repo, monkeypatch, capsys):
    assert _run(monkeypatch, ["matchmaker", "register-people", "--confirm"]) == 0
    out = capsys.readouterr().out
    assert "jane-synthex" in out
    assert "written" in out


def test_patent_coverage(repo, monkeypatch, capsys):
    assert _run(monkeypatch, ["patent", "coverage"]) == 0
    out = capsys.readouterr().out
    assert "patent coverage" in out
    assert "epo_ops" in out          # provenance source surfaced
    assert "provenance" in out


def test_patent_coverage_query_mode(repo, monkeypatch, capsys):
    # The class×year query the loops consult before fetching.
    rc = _run(monkeypatch, ["patent", "coverage", "--class", "G01B",
                            "--year-start", "1933", "--year-end", "1938"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "coverage: G01B" in out
    assert "fully covered" in out
    assert "missing windows" in out


def test_trademark_coverage(repo, monkeypatch, capsys):
    assert _run(monkeypatch, ["trademark", "coverage"]) == 0
    out = capsys.readouterr().out
    assert "trademark coverage" in out
    assert "live / dead" in out
    assert "uspto_bulk_csv" in out   # provenance source surfaced


def test_site_build_all_and_check_via_cli(repo, monkeypatch, capsys):
    # Exercise cmd_site build-all + check through the CLI dispatch.
    assert _run(monkeypatch, ["site", "build-all"]) == 0
    rc = _run(monkeypatch, ["site", "check", repo.project])
    out = capsys.readouterr().out
    assert "Site check" in out
    assert rc == 0  # portal exists → global-bar links resolve
