"""Tests for focus_serials rendering in render_trademark_gallery."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import markery.common.config as _cfg_mod
import markery.common.project as _proj_mod
from markery.specialist.publisher.render import render_trademark_gallery


def _tm(serial_no: str, mark_name: str, entity_name: str, entity_id: int) -> dict:
    return {
        "serial_no": serial_no,
        "mark_name": mark_name,
        "filing_dt": None,
        "status_cd": None,
        "entity_name": entity_name,
        "entity_id": entity_id,
        "image_available": False,
        "draw_cd": None,
        "goods": "",
    }


def _entity(entity_id: int, canonical_name: str) -> dict:
    return {
        "entity_id": entity_id,
        "canonical_name": canonical_name,
        "slug": canonical_name.lower().replace(" ", "-").replace(",", "").replace(".", ""),
        "entity_type": None,
        "industry": None,
    }


ENTITIES = [
    _entity(1, "Goodyear"),
    _entity(2, "Mack Trucks"),
    _entity(3, "General Motors"),
]

TRADEMARKS = [
    _tm("71273695", "EAGLE",    "Goodyear",  1),
    _tm("71247861", "BULLDOG",  "Mack Trucks", 2),
    _tm("71199224", "(design)", "General Motors", 3),
]

FOCUS_SERIALS: set[int] = {71273695, 71247861}


@pytest.fixture()
def out_dir(tmp_path: Path) -> Path:
    project_dir = tmp_path / "projects" / "test-proj"
    project_dir.mkdir(parents=True)
    (project_dir / "content").mkdir()
    with patch.object(_cfg_mod, "ROOT", tmp_path), \
         patch.object(_proj_mod, "ROOT", tmp_path):
        yield tmp_path / "out"


def _render(out_dir: Path, focus_serials=None, trademarks=TRADEMARKS) -> str:
    with patch.object(_cfg_mod, "ROOT", out_dir.parent), \
         patch.object(_proj_mod, "ROOT", out_dir.parent):
        project_dir = out_dir.parent / "projects" / "test-proj"
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "content").mkdir(exist_ok=True)
        render_trademark_gallery(
            project="test-proj",
            entities=ENTITIES,
            trademarks=trademarks,
            matches=[],
            entity_colors={1: "#a00", 2: "#0a0", 3: "#00a"},
            out_dir=out_dir,
            focus_serials=focus_serials,
        )
    html = (out_dir / "trademarks.html").read_text(encoding="utf-8")
    return html


class TestFocusSerialsGallery:
    def test_focus_section_title_present(self, tmp_path):
        html = _render(tmp_path, focus_serials=FOCUS_SERIALS)
        assert "Project Marks" in html

    def test_entity_section_title_present(self, tmp_path):
        html = _render(tmp_path, focus_serials=FOCUS_SERIALS)
        assert "All Entity Trademarks" in html

    def test_focus_card_class_applied(self, tmp_path):
        html = _render(tmp_path, focus_serials=FOCUS_SERIALS)
        assert "card--focus" in html

    def test_focus_badge_present(self, tmp_path):
        html = _render(tmp_path, focus_serials=FOCUS_SERIALS)
        assert "focus-badge" in html

    def test_all_marks_section_absent_when_focus_set(self, tmp_path):
        html = _render(tmp_path, focus_serials=FOCUS_SERIALS)
        assert ">All Marks<" not in html

    def test_focus_serials_appear_in_project_section(self, tmp_path):
        html = _render(tmp_path, focus_serials=FOCUS_SERIALS)
        project_marks_idx = html.index("Project Marks")
        entity_tms_idx = html.index("All Entity Trademarks")
        eagle_idx = html.index("sn-71273695")
        bulldog_idx = html.index("sn-71247861")
        assert project_marks_idx < eagle_idx < entity_tms_idx
        assert project_marks_idx < bulldog_idx < entity_tms_idx

    def test_non_focus_serial_appears_in_entity_section(self, tmp_path):
        html = _render(tmp_path, focus_serials=FOCUS_SERIALS)
        entity_tms_idx = html.index("All Entity Trademarks")
        gm_idx = html.index("sn-71199224")
        assert gm_idx > entity_tms_idx

    def test_project_marks_chip_present(self, tmp_path):
        html = _render(tmp_path, focus_serials=FOCUS_SERIALS)
        assert "project marks" in html


class TestNoFocusSerialsGallery:
    def test_all_marks_section_present(self, tmp_path):
        html = _render(tmp_path, focus_serials=None)
        assert "All Marks" in html

    def test_project_marks_section_absent(self, tmp_path):
        html = _render(tmp_path, focus_serials=None)
        assert "Project Marks" not in html

    def test_no_focus_card_class(self, tmp_path):
        html = _render(tmp_path, focus_serials=None)
        assert 'class="card card--focus"' not in html

    def test_no_focus_badge(self, tmp_path):
        html = _render(tmp_path, focus_serials=None)
        assert 'class="focus-badge"' not in html

    def test_all_serials_rendered(self, tmp_path):
        html = _render(tmp_path, focus_serials=None)
        assert "sn-71273695" in html
        assert "sn-71247861" in html
        assert "sn-71199224" in html


class TestCardDetails:
    def test_placeholder_shows_word_mark_not_serial(self, tmp_path):
        # SITE-REVIEW #2/#14: no image -> the placeholder shows the word mark,
        # not the meaningless serial number.
        html = _render(tmp_path)
        assert '<div class="card-image-placeholder">EAGLE</div>' in html
        assert '<div class="card-image-placeholder">71273695</div>' not in html

    def test_entity_badge_links_to_entity_page(self, tmp_path):
        # SITE-REVIEW #5: the entity pill links to the company page.
        html = _render(tmp_path)
        assert '<a class="entity-badge" href="entities/goodyear.html">Goodyear</a>' in html

    def test_drawing_code_labeled(self, tmp_path):
        # SITE-REVIEW #15: the drawing code carries an explicit label.
        marks = [dict(_tm("71273695", "EAGLE", "Goodyear", 1), draw_cd="5T07")]
        html = _render(tmp_path, trademarks=marks)
        assert "Drawing Code 5T07" in html

    def test_goods_full_text_in_title_attr(self, tmp_path):
        # SITE-REVIEW #12: the full goods text is preserved in a title tooltip.
        long_goods = "automobile tires and inner tubes " * 6
        marks = [dict(_tm("71273695", "EAGLE", "Goodyear", 1), goods=long_goods)]
        html = _render(tmp_path, trademarks=marks)
        assert f'title="{long_goods}"' in html

    def test_active_nav_marks_trademarks(self, tmp_path):
        # SITE-REVIEW #10: the current section is marked active in the nav.
        html = _render(tmp_path)
        assert '<a href="trademarks.html" class="active" aria-current="page">' in html

    def test_empty_gallery_shows_empty_state(self, tmp_path):
        html = _render(tmp_path, trademarks=[])
        assert "empty-state" in html
        assert "No trademarks recorded" in html
