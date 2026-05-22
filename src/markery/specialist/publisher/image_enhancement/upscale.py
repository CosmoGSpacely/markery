"""Real-ESRGAN upscaler for historical trademark scans."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

WEIGHTS_DIR = Path(__file__).parent / "weights"

MODELS: dict[str, dict] = {
    "x4plus": {
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        "scale": 4,
        "num_block": 23,
    },
    # Trained on anime/line art — better for pen-and-ink trademark drawings
    "x4plus-anime": {
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
        "scale": 4,
        "num_block": 6,
    },
}


def _weights_path(model_name: str) -> Path:
    filename = MODELS[model_name]["url"].split("/")[-1]
    return WEIGHTS_DIR / filename


def _ensure_weights(model_name: str) -> Path:
    path = _weights_path(model_name)
    if not path.exists():
        WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        url = MODELS[model_name]["url"]
        print(f"Downloading {model_name} weights from {url} …")
        urllib.request.urlretrieve(url, path)
        print(f"  Saved to {path}")
    return path


def upscale(img: Image.Image, model_name: str = "x4plus-anime") -> tuple[Image.Image, str]:
    """Upscale a PIL Image 4×. Returns (upscaled_image, model_used).

    Uses Real-ESRGAN when realesrgan/basicsr are installed; falls back to
    Pillow LANCZOS otherwise. model_used is 'lanczos-fallback' on the
    fallback path so callers can report which path ran.
    """
    try:
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer
    except ImportError:
        print("realesrgan/basicsr not installed — using Lanczos 4× fallback")
        w, h = img.size
        return img.resize((w * 4, h * 4), Image.LANCZOS), "lanczos-fallback"

    if model_name not in MODELS:
        raise ValueError(f"Unknown model '{model_name}'. Choose from: {list(MODELS)}")

    weights = _ensure_weights(model_name)
    spec = MODELS[model_name]

    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=spec["num_block"],
        num_grow_ch=32,
        scale=spec["scale"],
    )
    upsampler = RealESRGANer(
        scale=spec["scale"],
        model_path=str(weights),
        model=model,
        tile=256,
        tile_pad=10,
        pre_pad=0,
        half=False,
    )

    img_bgr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    output_bgr, _ = upsampler.enhance(img_bgr, outscale=spec["scale"])
    return Image.fromarray(cv2.cvtColor(output_bgr, cv2.COLOR_BGR2RGB)), model_name
