"""Tests for llm.call_batch — Batch API submit/poll/collect (mocked, no live API)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import markery.common.llm as llm


class _FakeBatches:
    def __init__(self, results):
        self._results = results
        self.created = None

    def create(self, requests):
        self.created = requests
        return SimpleNamespace(id="batch_test", processing_status="in_progress")

    def retrieve(self, _id):
        return SimpleNamespace(id="batch_test", processing_status="ended")

    def results(self, _id):
        return iter(self._results)


def _succeeded(custom_id, text, inp=100, out=20):
    msg = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=inp, output_tokens=out,
                              cache_read_input_tokens=0, cache_creation_input_tokens=0),
    )
    return SimpleNamespace(custom_id=custom_id,
                           result=SimpleNamespace(type="succeeded", message=msg))


def _errored(custom_id):
    return SimpleNamespace(custom_id=custom_id,
                           result=SimpleNamespace(type="errored"))


def test_call_batch_collects_succeeded_and_errored():
    fake_results = [_succeeded("a", "ANSWER A"), _errored("b")]
    fake_client = SimpleNamespace(messages=SimpleNamespace(batches=_FakeBatches(fake_results)))
    with patch.object(llm, "get_client", return_value=fake_client):
        out = llm.call_batch("claude-haiku-4-5", "SYS",
                             [("a", "q1"), ("b", "q2")], max_tokens=64, poll_interval=0)
    assert out["a"]["text"] == "ANSWER A"
    assert out["a"]["prompt_tokens"] == 100 and out["a"]["completion_tokens"] == 20
    assert out["b"] == {"error": "errored"}


def test_call_batch_builds_one_request_per_item():
    batches = _FakeBatches([_succeeded("x", "ok")])
    fake_client = SimpleNamespace(messages=SimpleNamespace(batches=batches))
    with patch.object(llm, "get_client", return_value=fake_client):
        llm.call_batch("claude-haiku-4-5", "SYS", [("x", "q")], max_tokens=8, poll_interval=0)
    assert len(batches.created) == 1
    assert batches.created[0]["custom_id"] == "x"


def test_call_batch_raises_without_client():
    with patch.object(llm, "get_client", return_value=None):
        try:
            llm.call_batch("m", "s", [("a", "q")], max_tokens=8)
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass
