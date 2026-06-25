"""Tests for annual design-mark review pages (Phase 24 P4)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from markery.specialist.publisher.render import reviews, render_portal
from markery.specialist.publisher import queries as q


@pytest.fixture()
def stub_marks(monkeypatch):
    def fake_design_marks(year, month):
        # Two marks per month; one with an image, one without.
        return [
            {"serial": f"7{year}{month:02d}1", "mark": "EAGLE", "filing": date(year, month, 4),
             "owner": "Acme Co.", "state": "NY", "goods": "boots and shoes", "has_img": True},
            {"serial": f"7{year}{month:02d}2", "mark": "", "filing": date(year, month, 9),
             "owner": "Beta Inc.", "state": "IL", "goods": "", "has_img": False},
        ]
    monkeypatch.setattr(reviews, "design_marks", fake_design_marks)
    monkeypatch.setattr(q, "get_mark_image_bytes", lambda sn: b"\x89PNG fake")


def test_render_review_year_creates_landing_and_months(tmp_path, stub_marks):
    path, summary, written = reviews.render_review_year(1930, tmp_path, "annual-design-review")
    assert path == tmp_path / "annual-design-review" / "1930" / "index.html"
    # 12 monthly pages + the landing exist
    for mm in range(1, 13):
        assert (tmp_path / "annual-design-review" / "1930" / f"{mm:02d}.html").exists()
    html = path.read_text()
    assert "<h1>1930 Design-Mark Review</h1>" in html
    assert html.count('class="review-month"') == 12
    # 24 marks total (2/month), 12 with images
    assert summary["count"] == 24
    assert summary["with_images"] == 12
    assert summary["url"] == "annual-design-review/1930/index.html"
    assert summary["thumb_src"].startswith("annual-design-review/1930/img/")
    assert len(written) == 12  # one image written per month


def test_year_landing_has_sibling_year_nav(tmp_path, stub_marks):
    reviews.render_review_year(1929, tmp_path, "annual-design-review",
                              sibling_years=[1928, 1929, 1930])
    html = (tmp_path / "annual-design-review" / "1929" / "index.html").read_text()
    assert "review-yearnav" in html
    assert 'href="../1928/index.html">1928' in html      # sibling link
    assert 'href="../1930/index.html">1930' in html
    assert '<span class="review-year-current">1929</span>' in html  # current, not linked


def test_review_month_page_depth_and_back_link(tmp_path, stub_marks):
    reviews.render_review_year(1930, tmp_path, "annual-design-review")
    july = (tmp_path / "annual-design-review" / "1930" / "07.html").read_text()
    assert "<h1>July 1930</h1>" in july
    assert july.count('class="card"') == 2
    assert 'src="img/' in july                     # image relative to month dir
    # month navigation: link back to the year landing + prev/next month
    assert 'href="index.html">1930 review' in july
    assert 'review-monthnav' in july
    assert 'href="06.html">← June' in july and 'href="08.html">August →' in july
    # filing date and goods/services on the design-mark cards
    assert "Filed July 04, 1930" in july
    assert "boots and shoes" in july
    # depth 2 → site root is two levels up; no project bar on review pages
    assert 'class="site-title" href="../../index.html"' in july
    assert '<div class="project-bar">' not in july


def test_portal_renders_review_cards(tmp_path):
    reviews_summary = [{
        "year": 1930, "url": "reviews/1930/index.html",
        "title": "1930 Design-Mark Review", "count": 240, "with_images": 240,
        "thumb_src": "reviews/1930/img/71930011.png",
    }]
    html = render_portal(tmp_path, [], [], reviews=reviews_summary).read_text()
    assert "Design-Mark Reviews" in html
    assert 'href="reviews/1930/index.html"' in html
    assert "240 design marks" in html
