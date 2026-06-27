"""Free-by-default model resolution (spawn-loop cost guard)."""

from __future__ import annotations

from markery.common import config


def test_resolve_model_free_by_default(monkeypatch):
    monkeypatch.delenv("MARKERY_MODEL", raising=False)
    assert config.resolve_model() == config.FREE_MODEL
    assert config.FREE_MODEL.endswith(":free")


def test_resolve_model_env_override(monkeypatch):
    monkeypatch.setenv("MARKERY_MODEL", "claude-opus-4-8")
    assert config.resolve_model() == "claude-opus-4-8"


def test_resolve_model_explicit_wins_over_env(monkeypatch):
    monkeypatch.setenv("MARKERY_MODEL", "claude-opus-4-8")
    assert config.resolve_model("xai:grok-2") == "xai:grok-2"


def test_resolve_model_explicit_over_free(monkeypatch):
    monkeypatch.delenv("MARKERY_MODEL", raising=False)
    assert config.resolve_model("openai:gpt-4o") == "openai:gpt-4o"
