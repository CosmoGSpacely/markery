"""In-process CLI dispatch + argparse-construction coverage.

Runs `markery.cli.main()` in-process (not via subprocess, so the parser-building
code counts toward coverage) for every subcommand's `--help`. `--help` exercises
each area's full argparse setup and the top-level dispatch table without touching
data or the network.
"""

from __future__ import annotations

import sys

import pytest

from markery.cli import main

# area → its subcommands (from `markery <area> --help`).
AREA_SUBCOMMANDS = {
    "patent": ["build", "fetch", "figures", "verify-credentials", "signals",
               "pull", "citations", "search", "coverage-check", "coverage"],
    "trademark": ["build", "enrich", "enrich-project", "load-events", "load-foreign",
                  "fetch", "entity-forward", "mark-status", "load-assignment",
                  "design-search", "search-tsdr", "inspect", "reparse",
                  "verify-credentials", "status", "coverage"],
    "matchmaker": ["build", "list", "status", "clear", "confirm", "unreject",
                   "suggest-variants", "validate-variants", "register", "register-people"],
    "historian": ["prepare", "card", "digest", "validate", "scaffold", "draft"],
    "librarian": ["search-sources", "discover", "wants", "wants-update", "acquire",
                  "enter", "raw-text", "extract", "review", "index", "search",
                  "list", "card", "media-search", "media-acquire", "media-list"],
    "site": ["build", "build-all", "check"],
    "wikipedia": ["draft", "candidates", "propose-edit", "submit", "from-essay",
                  "verify-credentials", "check-revision", "add-external-link", "replace"],
    "project": ["init", "adopt", "onboard"],
    "enhance": ["enhance", "batch", "gallery", "print"],
    "tokens": ["report"],
    "model": ["status", "mint", "test"],
}


def _run(monkeypatch, argv: list[str]) -> int:
    """Invoke main() with argv; return the exit code (0 if it returns normally)."""
    monkeypatch.setattr(sys, "argv", ["markery", *argv])
    try:
        main()
        return 0
    except SystemExit as e:
        return 0 if e.code is None else int(e.code)


def test_top_level_help(monkeypatch, capsys):
    assert _run(monkeypatch, ["--help"]) == 0
    assert "subcommands:" in capsys.readouterr().out


def test_no_args_prints_help(monkeypatch, capsys):
    assert _run(monkeypatch, []) == 0
    assert "usage: markery" in capsys.readouterr().out


def test_version(monkeypatch, capsys):
    assert _run(monkeypatch, ["--version"]) == 0
    assert "markery" in capsys.readouterr().out


def test_unknown_subcommand_exits_1(monkeypatch, capsys):
    assert _run(monkeypatch, ["nonsense-area"]) == 1
    assert "unknown subcommand" in capsys.readouterr().out


@pytest.mark.parametrize("area", sorted(AREA_SUBCOMMANDS))
def test_area_help(monkeypatch, area):
    # Each area's top --help builds its parser and exits 0.
    assert _run(monkeypatch, [area, "--help"]) == 0


@pytest.mark.parametrize(
    "area,sub",
    [(a, s) for a, subs in AREA_SUBCOMMANDS.items() for s in subs],
)
def test_subcommand_help(monkeypatch, area, sub):
    # Each subcommand's --help builds its sub-parser (args, options) and exits 0.
    assert _run(monkeypatch, [area, sub, "--help"]) == 0
