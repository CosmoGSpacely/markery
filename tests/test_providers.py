"""Tests for provider routing and the direct OpenAI / xAI connections (mocked)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from markery.common import providers as prv


def _resp(status, payload):
    return SimpleNamespace(status_code=status, json=lambda: payload, text=str(payload))


# ── route() ─────────────────────────────────────────────────────────────────

class TestRoute:
    @pytest.mark.parametrize("model,provider", [
        ("claude-haiku-4-5-20251001", "anthropic"),
        ("claude-sonnet-4-6", "anthropic"),
        ("openai:gpt-4o", "openai"),
        ("gpt-4o-mini", "openai"),
        ("o3-mini", "openai"),
        ("chatgpt-4o-latest", "openai"),
        ("xai:grok-3", "xai"),
        ("grok-4", "xai"),
        ("meta-llama/llama-3.3-70b-instruct:free", "openrouter"),
        ("openai/gpt-oss-120b:free", "openrouter"),
        ("something-unknown", "anthropic"),
    ])
    def test_route(self, model, provider):
        assert prv.route(model) == provider

    def test_openai_prefix_beats_slash_ambiguity(self):
        # explicit direct-OpenAI prefix uses ':', OpenRouter vendor uses '/'
        assert prv.route("openai:gpt-4o") == "openai"
        assert prv.route("openai/gpt-oss-120b:free") == "openrouter"

    def test_estimate_suffix_tolerated(self):
        assert prv.route("gpt-4o~estimate") == "openai"


class TestStripPrefix:
    def test_strips_known_prefixes(self):
        assert prv.strip_provider_prefix("openai:gpt-4o") == "gpt-4o"
        assert prv.strip_provider_prefix("xai:grok-3") == "grok-3"

    def test_passes_through_others(self):
        assert prv.strip_provider_prefix("gpt-4o") == "gpt-4o"
        assert prv.strip_provider_prefix("meta-llama/x:free") == "meta-llama/x:free"


# ── direct provider chat ────────────────────────────────────────────────────

class TestOpenAIChat:
    def test_calls_openai_endpoint_and_parses(self):
        payload = {"choices": [{"message": {"content": "hi"}}],
                   "usage": {"prompt_tokens": 5, "completion_tokens": 2}}
        captured = {}

        def _post(url, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["auth"] = headers["Authorization"]
            captured["model"] = json["model"]
            return _resp(200, payload)

        with (
            patch.object(prv, "_env_key", return_value="sk-openai"),
            patch("requests.post", _post),
        ):
            text, p, c = prv.openai_chat("openai:gpt-4o", "s", "u", max_tokens=16)
        assert (text, p, c) == ("hi", 5, 2)
        assert captured["url"] == "https://api.openai.com/v1/chat/completions"
        assert captured["auth"] == "Bearer sk-openai"
        assert captured["model"] == "gpt-4o"  # prefix stripped

    def test_missing_key_raises(self):
        with patch.object(prv, "_env_key", return_value=""):
            with pytest.raises(RuntimeError, match="OpenAI"):
                prv.openai_chat("gpt-4o", "s", "u", max_tokens=8)


class TestXAIChat:
    def test_calls_xai_endpoint_and_strips_prefix(self):
        payload = {"choices": [{"message": {"content": "grok"}}],
                   "usage": {"prompt_tokens": 7, "completion_tokens": 3}}
        captured = {}

        def _post(url, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["model"] = json["model"]
            return _resp(200, payload)

        with (
            patch.object(prv, "_env_key", return_value="xai-key"),
            patch("requests.post", _post),
        ):
            text, p, c = prv.xai_chat("xai:grok-3", "s", "u", max_tokens=16)
        assert text == "grok"
        assert captured["url"] == "https://api.x.ai/v1/chat/completions"
        assert captured["model"] == "grok-3"


class TestGenericRetry:
    def test_retries_then_raises(self):
        with patch("time.sleep"), patch("requests.post", return_value=_resp(503, {"e": 1})) as mp:
            with pytest.raises(RuntimeError, match="503"):
                prv.openai_compatible_chat("OpenAI", prv.OPENAI_BASE, "k", "gpt-4o",
                                           "s", "u", max_tokens=8, max_retries=1)
        assert mp.call_count == 2  # initial + 1 retry


class TestKeyStatus:
    def test_reflects_env(self):
        with patch.object(prv, "_env_key", side_effect=lambda n: "x" if n == "OPENAI_API_KEY" else ""):
            st = prv.key_status()
        assert st["openai"] is True and st["xai"] is False


# ── llm.call dispatch to direct providers ───────────────────────────────────

class TestLlmDispatch:
    def test_call_routes_openai(self):
        from markery.common import llm
        with patch("markery.common.providers.openai_chat",
                   return_value=("oai", 4, 1)) as m:
            out = llm.call("gpt-4o-mini", "s", "u", max_tokens=8)
        assert out == ("oai", 4, 1, 0, 0)
        m.assert_called_once()

    def test_call_routes_xai(self):
        from markery.common import llm
        with patch("markery.common.providers.xai_chat",
                   return_value=("grok", 6, 2)) as m:
            out = llm.call("grok-3", "s", "u", max_tokens=8)
        assert out == ("grok", 6, 2, 0, 0)
        m.assert_called_once()

    def test_call_batch_loops_for_openai(self):
        from markery.common import llm
        with patch("markery.common.providers.openai_chat",
                   side_effect=[("a", 1, 1), ("b", 2, 2)]):
            out = llm.call_batch("gpt-4o-mini", "s",
                                 [("i1", "q1"), ("i2", "q2")], max_tokens=8)
        assert out["i1"]["text"] == "a" and out["i2"]["completion_tokens"] == 2
