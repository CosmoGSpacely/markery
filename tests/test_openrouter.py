"""Tests for the OpenRouter provider wiring (mocked — no live API)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from markery.common import openrouter as orr


def _resp(status, payload):
    return SimpleNamespace(status_code=status, json=lambda: payload, text=str(payload))


# ── routing predicate ──────────────────────────────────────────────────────

class TestIsOpenRouter:
    def test_slug_is_openrouter(self):
        assert orr.is_openrouter_model("meta-llama/llama-3.3-70b-instruct:free")
        assert orr.is_openrouter_model("openai/gpt-oss-120b:free")

    def test_claude_is_not(self):
        assert not orr.is_openrouter_model("claude-haiku-4-5-20251001")
        assert not orr.is_openrouter_model("claude-sonnet-4-6")


# ── key minting ─────────────────────────────────────────────────────────────

class TestMint:
    def test_mint_parses_key_field(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_PROVISIONING_KEY", "prov-xyz")
        captured = {}

        def _post(url, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["auth"] = headers["Authorization"]
            captured["body"] = json
            return _resp(201, {"key": "sk-or-v1-RUNTIME", "data": {"hash": "h"}})

        with patch("requests.post", _post):
            secret = orr.mint_runtime_key(name="markery-runtime")
        assert secret == "sk-or-v1-RUNTIME"
        assert captured["url"].endswith("/keys")
        assert captured["auth"] == "Bearer prov-xyz"
        assert captured["body"]["name"] == "markery-runtime"

    def test_mint_without_provisioning_raises(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_PROVISIONING_KEY", raising=False)
        with patch.object(orr, "_provisioning_key", return_value=""):
            with pytest.raises(RuntimeError, match="PROVISIONING"):
                orr.mint_runtime_key()

    def test_mint_http_error_raises(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_PROVISIONING_KEY", "prov-xyz")
        with patch("requests.post", return_value=_resp(403, {"error": "nope"})):
            with pytest.raises(RuntimeError, match="403"):
                orr.mint_runtime_key()


# ── runtime-key resolution ──────────────────────────────────────────────────

class TestRuntimeKey:
    def test_explicit_env_wins(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-explicit")
        with patch.object(orr, "_cache_path", return_value=tmp_path / ".openrouter-key"):
            assert orr.runtime_key() == "sk-explicit"

    def test_cached_file_used(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        cache = tmp_path / ".openrouter-key"
        cache.write_text("sk-cached\n")
        with patch.object(orr, "_cache_path", return_value=cache):
            assert orr.runtime_key() == "sk-cached"

    def test_mint_when_nothing_cached(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_PROVISIONING_KEY", "prov-xyz")
        cache = tmp_path / ".openrouter-key"
        with (
            patch.object(orr, "_cache_path", return_value=cache),
            patch.object(orr, "mint_runtime_key", return_value="sk-minted"),
        ):
            assert orr.runtime_key() == "sk-minted"
        assert cache.read_text().strip() == "sk-minted"  # cached for next call

    def test_none_when_no_keys_and_mint_disabled(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with patch.object(orr, "_cache_path", return_value=tmp_path / "absent"):
            assert orr.runtime_key(allow_mint=False) is None


# ── chat ────────────────────────────────────────────────────────────────────

class TestChat:
    def test_chat_parses_content_and_usage(self):
        payload = {
            "choices": [{"message": {"content": " A trademark is a brand sign. "}}],
            "usage": {"prompt_tokens": 30, "completion_tokens": 9},
        }
        with (
            patch.object(orr, "runtime_key", return_value="sk-rt"),
            patch("requests.post", return_value=_resp(200, payload)),
        ):
            text, ptok, ctok = orr.chat("meta-llama/llama-3.3-70b-instruct:free",
                                        "sys", "user", max_tokens=64)
        assert text == "A trademark is a brand sign."
        assert ptok == 30 and ctok == 9

    def test_chat_without_key_raises(self):
        with patch.object(orr, "runtime_key", return_value=None):
            with pytest.raises(RuntimeError, match="runtime key"):
                orr.chat("x/y:free", "s", "u", max_tokens=8)

    def test_chat_non_retryable_error_raises_immediately(self):
        post = patch("requests.post", return_value=_resp(400, {"error": "bad"}))
        with patch.object(orr, "runtime_key", return_value="sk-rt"), post as mock_post:
            with pytest.raises(RuntimeError, match="400"):
                orr.chat("x/y:free", "s", "u", max_tokens=8)
        assert mock_post.call_count == 1  # 400 is not retried

    def test_chat_retries_on_429_then_succeeds(self):
        ok = {"choices": [{"message": {"content": "ok"}}],
              "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
        responses = [_resp(429, {"e": 1}), _resp(429, {"e": 1}), _resp(200, ok)]
        with (
            patch.object(orr, "runtime_key", return_value="sk-rt"),
            patch("time.sleep"),
            patch("requests.post", side_effect=responses) as mock_post,
        ):
            text, _, _ = orr.chat("x/y:free", "s", "u", max_tokens=8)
        assert text == "ok"
        assert mock_post.call_count == 3

    def test_chat_429_exhausts_retries_and_raises(self):
        with (
            patch.object(orr, "runtime_key", return_value="sk-rt"),
            patch("time.sleep"),
            patch("requests.post", return_value=_resp(429, {"e": 1})),
        ):
            with pytest.raises(RuntimeError, match="429"):
                orr.chat("x/y:free", "s", "u", max_tokens=8, max_retries=2)


# ── llm.call routing ────────────────────────────────────────────────────────

class TestLlmRouting:
    def test_call_routes_openrouter(self):
        from markery.common import llm
        with patch("markery.common.openrouter.chat",
                   return_value=("hello", 10, 3)) as mock_chat:
            out = llm.call("meta-llama/llama-3.3-70b-instruct:free",
                           "sys", "user", max_tokens=32)
        assert out == ("hello", 10, 3, 0, 0)
        mock_chat.assert_called_once()

    def test_call_batch_routes_openrouter_sequentially(self):
        from markery.common import llm
        with patch("markery.common.openrouter.chat",
                   side_effect=[("a", 1, 1), ("b", 2, 2)]):
            out = llm.call_batch("x/y:free", "sys",
                                 [("id1", "q1"), ("id2", "q2")], max_tokens=8)
        assert out["id1"]["text"] == "a"
        assert out["id2"]["completion_tokens"] == 2
        assert out["id1"]["cache_read_tokens"] == 0


# ── pricing & cache-warning ─────────────────────────────────────────────────

class TestFreePricingAndCache:
    def test_free_model_costs_zero_not_unknown(self):
        from markery.common.tokens_report import record_cost
        usd, unknown = record_cost({
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "prompt_tokens": 1_000_000, "completion_tokens": 1_000_000,
        })
        assert usd == 0.0 and not unknown

    def test_cache_warning_suppressed_for_openrouter(self):
        from markery.common.tokens import cache_health_warning
        assert cache_health_warning("meta-llama/llama-3.3-70b-instruct:free",
                                    n_calls=5, cache_read_tokens=0) is None

    def test_cache_warning_still_fires_for_claude(self):
        from markery.common.tokens import cache_health_warning
        assert cache_health_warning("claude-haiku-4-5", n_calls=5,
                                    cache_read_tokens=0) is not None
