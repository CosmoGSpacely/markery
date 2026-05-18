from datetime import date
from markery.specialist.matchmaker.score import date_score, class_score, total_score


def test_patent_before_trademark_is_positive():
    grant  = date(1939, 3, 28)
    filing = date(1939, 4, 7)
    assert date_score(grant, filing) > 0


def test_trademark_before_patent_is_negative():
    grant  = date(1930, 1, 1)
    filing = date(1925, 1, 1)
    score  = date_score(grant, filing)
    assert score < 0
    assert score > -0.4


def test_class_score_fires_for_product_class():
    assert class_score(["B42F"]) == 0.3
    assert class_score(["B42D"]) == 0.3
    assert class_score(["G06C", "B42F"]) == 0.3


def test_class_score_zero_for_unrelated_class():
    assert class_score(["A01B"]) == 0.0
    assert class_score([]) == 0.0


def test_maximum_total_score_is_0_80():
    same_day = date(1939, 4, 7)
    score = total_score(same_day, same_day, ["B42F"])
    assert score == 0.80


def test_none_dates_return_zero():
    assert date_score(None, None) == 0.0
    assert date_score(date(1930, 1, 1), None) == 0.0
    assert date_score(None, date(1930, 1, 1)) == 0.0
