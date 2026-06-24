"""Hermetic tests for image-enhancement transforms and the DB-backed gallery.

The Real-ESRGAN / opencv / vtracer paths live in the optional `enhance` extra;
tests that need them importorskip so the hermetic CI lane (dev extra only) runs
the Lanczos fallback and the gallery, and skips the heavy paths cleanly.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from tests.fixtures.synthetic import build_synthetic_repo


# ---------------------------------------------------------------------------
# upscale — Lanczos fallback (no realesrgan installed)
# ---------------------------------------------------------------------------

def test_upscale_lanczos_fallback():
    from markery.specialist.publisher.image_enhancement import upscale
    img = Image.new("RGB", (8, 6), (200, 100, 50))
    out, model = upscale.upscale(img)
    assert model == "lanczos-fallback"
    assert out.size == (32, 24)  # 4× each dimension


def test_weights_path_pure():
    from markery.specialist.publisher.image_enhancement import upscale
    p = upscale._weights_path("x4plus-anime")
    assert p.name.endswith(".pth")
    assert "anime" in p.name.lower()


# ---------------------------------------------------------------------------
# gallery — DB-backed HTML emission
# ---------------------------------------------------------------------------

def test_build_gallery_embeds_mark(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    from markery.specialist.publisher.image_enhancement import gallery
    out = tmp_path / "gallery.html"
    result = gallery.build_gallery(
        [str(repo.cand_serial)],
        out,
        title="Synthetic Marks",
        db_path=str(repo.db_tm),
    )
    assert result == out
    html = out.read_text(encoding="utf-8")
    assert "Synthetic Marks" in html
    assert "data:image/png;base64," in html  # the mark image embedded
    assert "SYNTHEX" in html


def test_build_gallery_skips_serial_without_image(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    from markery.specialist.publisher.image_enhancement import gallery
    out = tmp_path / "g2.html"
    # CONF_SERIAL has no mark_images row → no card, but the page still renders.
    gallery.build_gallery([str(repo.conf_serial)], out, db_path=str(repo.db_tm))
    html = out.read_text(encoding="utf-8")
    assert "data:image/png;base64," not in html


# ---------------------------------------------------------------------------
# binarize — needs opencv + vtracer (enhance extra)
# ---------------------------------------------------------------------------

def test_binarize_threshold_is_mono():
    pytest.importorskip("cv2")
    pytest.importorskip("vtracer")
    from markery.specialist.publisher.image_enhancement import binarize
    img = Image.new("RGB", (40, 40), (128, 128, 128))
    out = binarize.threshold(img)
    # adaptive threshold returns a single-channel image
    assert out.mode in ("L", "1")
    assert out.size == (40, 40)
