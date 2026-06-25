"""Phase 30 P3 — the discovery log (library/leads.jsonl), hermetic."""

from __future__ import annotations

import pytest

import markery.common.config as cfg
from markery.specialist.librarian import leads


@pytest.fixture
def library(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "ROOT", tmp_path)
    (tmp_path / "library").mkdir(parents=True)
    return tmp_path


def test_add_dedup_and_read(library):
    assert leads.add_lead("loc", "p1", title="Plow", project="tools", relevance=4) is True
    assert leads.add_lead("loc", "p1", title="dup") is False   # dedup by source+id
    assert leads.add_lead("ia", "x9", title="Other") is True
    rows = leads.read_leads()
    assert {r["source_id"] for r in rows} == {"p1", "x9"}
    assert rows[0]["relevance"] == 4 and rows[0]["status"] == "logged"
    assert rows[0]["discovered_at"]


def test_update_lead(library):
    leads.add_lead("loc", "p1", status="logged")
    assert leads.update_lead("loc", "p1", status="acquired", relevance=5) is True
    assert leads.update_lead("loc", "missing", status="dropped") is False
    row = leads.read_leads()[0]
    assert row["status"] == "acquired" and row["relevance"] == 5


def test_has_lead(library):
    assert leads.has_lead("loc", "p1") is False
    leads.add_lead("loc", "p1")
    assert leads.has_lead("loc", "p1") is True


def test_atomic_write_no_temp_leftover(library):
    leads.add_lead("loc", "p1")
    assert list((library / "library").glob(".leads-*")) == []
