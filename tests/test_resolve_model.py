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


# --- D077: model fallback chain --------------------------------------------

def test_model_chain_free_first_no_paid_by_default(monkeypatch):
    monkeypatch.delenv("MARKERY_MODEL", raising=False)
    monkeypatch.delenv("MARKERY_ALLOW_PAID", raising=False)
    chain = config.model_chain()
    assert chain == config.FREE_MODELS                  # free only, no paid backstop
    assert chain[0] == config.FREE_MODEL and len(chain) >= 2


def test_model_chain_paid_backstop_opt_in(monkeypatch):
    monkeypatch.delenv("MARKERY_MODEL", raising=False)
    monkeypatch.setenv("MARKERY_ALLOW_PAID", "1")
    monkeypatch.setenv("MARKERY_PAID_MODEL", "xai:grok-4")
    chain = config.model_chain()
    assert chain[:len(config.FREE_MODELS)] == config.FREE_MODELS
    assert chain[-1] == "xai:grok-4"                    # paid appended last, opt-in only


def test_model_chain_explicit_and_env_pin_single(monkeypatch):
    monkeypatch.setenv("MARKERY_ALLOW_PAID", "1")
    monkeypatch.setenv("MARKERY_MODEL", "claude-opus-4-8")
    assert config.model_chain() == ["claude-opus-4-8"]          # env pins exactly
    assert config.model_chain("xai:grok-2") == ["xai:grok-2"]   # explicit pins exactly


def test_call_chain_falls_back_then_succeeds(monkeypatch):
    from markery.common import llm
    calls = []

    def fake_call(model, system, user, max_tokens, cache_system=True):
        calls.append(model)
        if model == "free-a":
            raise RuntimeError("429 rate-limited")
        return ("ok", 10, 5, 0, 0)

    monkeypatch.setattr(llm, "call", fake_call)
    text, ptok, ctok, cr, cc, used = llm.call_chain(["free-a", "free-b"], "s", "u", 50)
    assert text == "ok" and used == "free-b"
    assert calls == ["free-a", "free-b"]                # tried a, fell back to b


def test_call_chain_raises_when_all_fail(monkeypatch):
    from markery.common import llm
    monkeypatch.setattr(llm, "call",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))
    import pytest
    with pytest.raises(RuntimeError):
        llm.call_chain(["free-a", "free-b"], "s", "u", 50)
