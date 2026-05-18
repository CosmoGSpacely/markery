"""Unit tests for publisher queries pure functions."""

from __future__ import annotations

from datetime import date

from markery.specialist.publisher.queries import get_entity_stats


def _tm(entity_id: int, year: int) -> dict:
    return {"entity_id": entity_id, "filing_dt": date(year, 1, 1)}


def _pat(entity_id: int, year: int) -> dict:
    return {"entity_id": entity_id, "grant_dt": date(year, 6, 15)}


def _match(entity_id: int) -> dict:
    return {"entity_id": entity_id}


def test_get_entity_stats_counts():
    tms     = [_tm(1, 1920), _tm(1, 1925), _tm(2, 1930)]
    patents = [_pat(1, 1922), _pat(2, 1928), _pat(2, 1935)]
    matches = [_match(1), _match(1), _match(2)]

    stats = get_entity_stats([1, 2], tms, patents, matches)

    assert stats[1]["trademark_count"] == 2
    assert stats[1]["patent_count"]    == 1
    assert stats[1]["match_count"]     == 2
    assert stats[2]["trademark_count"] == 1
    assert stats[2]["patent_count"]    == 2
    assert stats[2]["match_count"]     == 1


def test_get_entity_stats_year_range():
    tms     = [_tm(1, 1915), _tm(1, 1938)]
    patents = [_pat(1, 1920)]

    stats = get_entity_stats([1], tms, patents, [])

    assert stats[1]["active_from"] == 1915
    assert stats[1]["active_to"]   == 1938


def test_get_entity_stats_empty_lists():
    stats = get_entity_stats([1, 2], [], [], [])

    for eid in (1, 2):
        assert stats[eid]["trademark_count"] == 0
        assert stats[eid]["patent_count"]    == 0
        assert stats[eid]["match_count"]     == 0
        assert stats[eid]["active_from"]     is None
        assert stats[eid]["active_to"]       is None
