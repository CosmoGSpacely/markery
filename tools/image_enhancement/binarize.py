"""Adaptive threshold and vtracer SVG vectorization for trademark images."""

from __future__ import annotations

import io
import re

import cv2
import numpy as np
import vtracer
from PIL import Image

_PATH_RE = re.compile(r"<path\b")

# Marks with more paths than this after vectorization are too complex for a
# clean SVG — illustrations with fine crosshatching routinely exceed this.
SVG_COMPLEXITY_LIMIT = 800


def threshold(img: Image.Image) -> Image.Image:
    """Convert to crisp B&W via adaptive Gaussian thresholding."""
    gray = np.array(img.convert("L"))
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10,
    )
    return Image.fromarray(binary)


def vectorize(img: Image.Image, complexity_limit: int = SVG_COMPLEXITY_LIMIT) -> str | None:
    """
    Attempt to vectorize a (preferably B&W) PIL Image to an SVG string.

    Returns None when the result exceeds complexity_limit paths, which
    indicates the mark has too much fine illustration detail to produce a
    clean, usable vector — save as PNG instead.
    """
    buf = io.BytesIO()
    img.convert("L").save(buf, format="PNG")

    svg_str = vtracer.convert_raw_image_to_svg(
        buf.getvalue(),
        img_format="png",
        colormode="binary",
        hierarchical="stacked",
        mode="spline",
        filter_speckle=4,
        corner_threshold=60,
        length_threshold=4.0,
        splice_threshold=45,
        path_precision=3,
    )

    if len(_PATH_RE.findall(svg_str)) > complexity_limit:
        return None
    return svg_str
