"""Tests for Phase 6C: semantic_score() and extended total_score()."""

from __future__ import annotations

from datetime import date

from markery.specialist.matchmaker.score import (
    semantic_score,
    total_score,
    SEMANTIC_CAP,
)


# ---------------------------------------------------------------------------
# semantic_score
# ---------------------------------------------------------------------------

def test_semantic_score_all_zero_when_no_signals():
    assert semantic_score() == 0.0


def test_semantic_score_title_hit_adds_020():
    assert semantic_score(title_name_hit=True) == 0.20


def test_semantic_score_abstract_hit_adds_010():
    assert semantic_score(abstract_name_hit=True) == 0.10


def test_semantic_score_goods_title_overlap_above_threshold_adds_010():
    assert semantic_score(goods_title_overlap=0.10) == 0.10


def test_semantic_score_goods_title_overlap_below_threshold_is_zero():
    assert semantic_score(goods_title_overlap=0.04) == 0.0


def test_semantic_score_goods_abstract_overlap_above_threshold_adds_005():
    assert semantic_score(goods_abstract_overlap=0.10) == 0.05


def test_semantic_score_goods_abstract_overlap_at_threshold_is_zero():
    # > 0.05 fires; == 0.05 does not
    assert semantic_score(goods_abstract_overlap=0.05) == 0.0


def test_semantic_score_all_signals_sum_to_045():
    result = semantic_score(
        title_name_hit=True,
        abstract_name_hit=True,
        goods_title_overlap=0.20,
        goods_abstract_overlap=0.20,
    )
    assert result == 0.45


def test_semantic_cap_constant_is_025():
    assert SEMANTIC_CAP == 0.25


# ---------------------------------------------------------------------------
# total_score — backward compatibility
# ---------------------------------------------------------------------------

def test_total_score_no_signals_same_as_before():
    grant  = date(1918, 4, 2)
    filing = date(1921, 6, 7)
    score_old = total_score(grant, filing, ["B42F"])
    score_new = total_score(grant, filing, ["B42F"],
                            title_name_hit=False, abstract_name_hit=False,
                            goods_title_overlap=0.0, goods_abstract_overlap=0.0)
    assert score_old == score_new


def test_total_score_maximum_without_signals_is_080():
    same_day = date(1939, 4, 7)
    assert total_score(same_day, same_day, ["B42F"]) == 0.80


def test_total_score_title_hit_adds_semantic_bonus():
    grant  = date(1918, 4, 2)
    filing = date(1921, 6, 7)
    base   = total_score(grant, filing, ["B42F"])
    with_hit = total_score(grant, filing, ["B42F"], title_name_hit=True)
    assert with_hit > base
    assert round(with_hit - base, 4) == 0.20


def test_total_score_semantic_bonus_capped_at_025():
    same_day = date(1939, 4, 7)
    # All signals fire: raw bonus = 0.45, capped at 0.25
    score = total_score(
        same_day, same_day, ["B42F"],
        title_name_hit=True,
        abstract_name_hit=True,
        goods_title_overlap=0.20,
        goods_abstract_overlap=0.20,
    )
    assert score == round(0.80 + 0.25, 4)


def test_total_score_none_dates_semantic_still_applies():
    score = total_score(None, None, [], title_name_hit=True)
    assert score == 0.20


def test_total_score_result_is_rounded_to_4_decimals():
    grant  = date(1918, 4, 2)
    filing = date(1921, 6, 7)
    score  = total_score(grant, filing, [], goods_title_overlap=0.10)
    assert score == round(score, 4)
