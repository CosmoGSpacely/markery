"""Tests for `markery wikipedia candidates` and `propose-edit` (Phase 24 P3 tooling)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import markery.common.config as cfg_mod
import markery.common.project as project_mod
from markery.specialist.publisher.wikipedia import cli as wiki_cli


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scaffold(tmp_path: Path, name: str, confirmed: list[dict],
              essays: dict[str, str] | None = None,
              project_json: dict | None = None) -> Path:
    """Create projects/<name>/ with project.json, confirmed.jsonl, and essays."""
    root = tmp_path / "projects" / name
    (root / "matches").mkdir(parents=True)
    (root / "content").mkdir(parents=True)
    (root / "project.json").write_text(
        json.dumps(project_json or {"type": "match-review-essay"}), encoding="utf-8")
    with (root / "matches" / "confirmed.jsonl").open("w", encoding="utf-8") as fh:
        for rec in confirmed:
            fh.write(json.dumps(rec) + "\n")
    for fname, text in (essays or {}).items():
        (root / "content" / fname).write_text(text, encoding="utf-8")
    return root


def _patched(tmp_path: Path):
    return [
        patch.object(cfg_mod, "ROOT", tmp_path),
        patch.object(wiki_cli, "ROOT", tmp_path),
        patch.object(project_mod, "ROOT", tmp_path),
    ]


# ---------------------------------------------------------------------------
# _candidate_slug
# ---------------------------------------------------------------------------

def test_candidate_slug_word_mark():
    rec = {"trademark": "JOHN DEERE MOLINE, ILL.", "patent_no": "US979019A"}
    assert wiki_cli._candidate_slug(rec) == "john-deere-moline-ill-us979019a"


def test_candidate_slug_figurative():
    rec = {"trademark": None, "patent_no": "US1419306A"}
    assert wiki_cli._candidate_slug(rec) == "figurative-us1419306a"


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------

def test_candidates_lists_pairs_with_essay_flag(tmp_path, capsys):
    _scaffold(
        tmp_path, "p",
        confirmed=[
            {"trademark": "SOUNDEX", "patent_no": "US1261167A",
             "trademark_serial": 71246709, "entity": "Remington Rand"},
            {"trademark": None, "patent_no": "US1419306A",
             "trademark_serial": 71185153, "entity": "L.S. Starrett Company"},
        ],
        essays={"soundex-us1261167a.md": "essay"},  # only the first has an essay
    )
    with _patched(tmp_path)[0], _patched(tmp_path)[1], _patched(tmp_path)[2]:
        wiki_cli.cmd_candidates("p")
    out = capsys.readouterr().out
    assert "soundex-us1261167a" in out
    assert "figurative-us1419306a" in out
    assert "(figurative)" in out          # null mark rendered safely
    # essay present for soundex, absent for the figurative one
    soundex_line = next(l for l in out.splitlines() if "soundex-us1261167a" in l)
    figurative_line = next(l for l in out.splitlines() if "figurative-us1419306a" in l)
    assert "yes" in soundex_line
    assert "NO" in figurative_line


def test_candidates_marks_already_submitted(tmp_path, capsys):
    root = _scaffold(
        tmp_path, "p",
        confirmed=[{"trademark": "SOUNDEX", "patent_no": "US1261167A",
                    "trademark_serial": 71246709, "entity": "Rand"}],
    )
    (root / "wikipedia").mkdir()
    (root / "wikipedia" / "submissions.jsonl").write_text(
        json.dumps({"serial_no": "71246709", "article": "Soundex"}) + "\n",
        encoding="utf-8")
    with _patched(tmp_path)[0], _patched(tmp_path)[1], _patched(tmp_path)[2]:
        wiki_cli.cmd_candidates("p")
    out = capsys.readouterr().out
    assert "✓" in out


# ---------------------------------------------------------------------------
# propose-edit
# ---------------------------------------------------------------------------

_ESSAY = """---
title: "JOHN DEERE MOLINE, ILL. — US979019A"
trademark_serial: 71055630
trademark: "JOHN DEERE MOLINE, ILL."
tm_owner: "DEERE & COMPANY"
---
## The Connection
Owner-and-era correspondence.
"""


def test_propose_edit_uses_project_model_and_writes_file(tmp_path, capsys):
    _scaffold(
        tmp_path, "p",
        confirmed=[{"trademark": "JOHN DEERE MOLINE, ILL.", "patent_no": "US979019A",
                    "trademark_serial": 71055630, "entity": "Deere"}],
        essays={"john-deere-moline-ill-us979019a.md": _ESSAY},
        project_json={"type": "match-review-essay", "model": "openai/gpt-oss-120b:free"},
    )
    captured = {}

    def fake_call(model, system, user, max_tokens, **kw):
        captured["model"] = model
        captured["system"] = system
        captured["user"] = user
        return ("John Deere Moline, Ill. sentence.<ref>x</ref>\nSUMMARY: add", 100, 20, 0, 0)

    with _patched(tmp_path)[0], _patched(tmp_path)[1], _patched(tmp_path)[2], \
         patch("markery.common.llm.call", fake_call):
        wiki_cli.cmd_propose_edit("p", "john-deere-moline-ill-us979019a",
                                  "John Deere", None)

    # model came from project.json
    assert captured["model"] == "openai/gpt-oss-120b:free"
    # essay text was fed to the model; system enforces normal-case / no-embodiment rules
    assert "JOHN DEERE MOLINE, ILL." in captured["user"]
    assert "NORMAL CASE" in captured["system"]
    assert "embodied" in captured["system"]
    # proposal saved
    out_file = (tmp_path / "projects" / "p" / "wikipedia"
                / "john-deere-moline-ill-us979019a-propose.wiki")
    assert out_file.exists()
    assert "John Deere Moline, Ill." in out_file.read_text()


def test_propose_edit_model_override(tmp_path):
    _scaffold(
        tmp_path, "p",
        confirmed=[{"trademark": "X", "patent_no": "US1A",
                    "trademark_serial": 1, "entity": "E"}],
        essays={"x-us1a.md": _ESSAY},
        project_json={"type": "match-review-essay", "model": "claude-haiku-4-5"},
    )
    seen = {}

    def fake_call(model, system, user, max_tokens, **kw):
        seen["model"] = model
        return ("s\nSUMMARY: s", 1, 1, 0, 0)

    with _patched(tmp_path)[0], _patched(tmp_path)[1], _patched(tmp_path)[2], \
         patch("markery.common.llm.call", fake_call):
        wiki_cli.cmd_propose_edit("p", "x-us1a", "Article",
                                  "openai/gpt-oss-120b:free")
    assert seen["model"] == "openai/gpt-oss-120b:free"  # override beat project.json


def test_propose_edit_missing_essay_exits(tmp_path):
    _scaffold(
        tmp_path, "p",
        confirmed=[{"trademark": "X", "patent_no": "US1A",
                    "trademark_serial": 1, "entity": "E"}],
    )
    with _patched(tmp_path)[0], _patched(tmp_path)[1], _patched(tmp_path)[2], \
         pytest.raises(SystemExit):
        wiki_cli.cmd_propose_edit("p", "x-us1a", "Article", None)
