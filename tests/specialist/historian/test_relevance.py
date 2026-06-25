"""Phase 30 P3 — discovery relevance scoring (hermetic; model call mocked)."""

from __future__ import annotations

import pytest

import markery.common.config as cfg
import markery.common.project as pm
from markery.specialist.historian import relevance


def test_parse_score_well_formed():
    out = relevance.parse_score("SCORE: 4\nREASONING: Directly about Synthex gauges.")
    assert out["score"] == 4 and "Synthex" in out["reasoning"]


def test_parse_score_unparseable_is_zero():
    out = relevance.parse_score("I'm not sure how to rate this.")
    assert out["score"] == 0 and out["reasoning"]


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "ROOT", tmp_path)
    monkeypatch.setattr(pm, "ROOT", tmp_path)
    proj = tmp_path / "projects" / "tools"
    (proj / "content").mkdir(parents=True)
    (proj / "entities.csv").write_text(
        "entity_id,canonical_name\n1,Synthex Manufacturing Company\n")
    (proj / "content" / "research-question.md").write_text(
        "How did precision-tool firms brand their gauges?")
    return "tools"


def test_score_relevance_builds_context_and_parses(project, monkeypatch):
    captured = {}

    def _fake_call(model, system, user, max_tokens):
        captured["system"] = system
        captured["user"] = user
        return ("SCORE: 5\nREASONING: It is about Synthex gauges.", 0, 0, 0, 0)

    monkeypatch.setattr("markery.common.llm.call", _fake_call)
    out = relevance.score_relevance("tools", "A History of Synthex Gauges",
                                    text="...precision measurement...")
    assert out["score"] == 5
    # Context carried the project's entity + research question into the prompt.
    assert "Synthex Manufacturing Company" in captured["user"]
    assert "research question" in captured["user"].lower()
    assert "A History of Synthex Gauges" in captured["user"]
