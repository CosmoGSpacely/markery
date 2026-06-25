"""Phase 30 P6 — discovery-loop on/off state (hermetic)."""

from __future__ import annotations

import pytest

import markery.common.config as cfg
from markery.specialist.historian import discovery


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "ROOT", tmp_path)
    (tmp_path / "library").mkdir(parents=True)
    return tmp_path


def test_default_state_when_absent(lib):
    st = discovery.read_state()
    assert st["enabled"] is False and st["relevance_floor"] == 3
    assert "loc" in st["sources"]


def test_set_enabled_persists_and_overrides(lib):
    discovery.set_enabled(True, sources=["chronam"], relevance_floor=4,
                          projects=["tools"])
    st = discovery.read_state()
    assert st["enabled"] is True and st["sources"] == ["chronam"]
    assert st["relevance_floor"] == 4 and st["projects"] == ["tools"]
    discovery.set_enabled(False)
    assert discovery.read_state()["enabled"] is False
    # overrides preserved across an off toggle (only enabled changed)
    assert discovery.read_state()["sources"] == ["chronam"]


def test_mark_tick_sets_timestamp(lib):
    assert discovery.read_state()["last_tick"] is None
    discovery.mark_tick()
    assert discovery.read_state()["last_tick"]


def test_atomic_write_no_temp_leftover(lib):
    discovery.set_enabled(True)
    assert list((lib / "library").glob(".discovery-*")) == []
