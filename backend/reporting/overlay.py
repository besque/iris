"""Draws tool evidence (boxes or masks) onto an image."""

import numpy as np
from PIL import Image, ImageDraw

# mask value -> rgb. fusion: 1 water, 2 built-up. change: 1 changed.
PALETTES = {
    "fusion": {1: (0, 90, 255), 2: (255, 140, 0)},
    "change": {1: (255, 40, 40)},
}


def draw_boxes(img: Image.Image, boxes, label: str = "") -> Image.Image:
    out = img.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    for x1, y1, x2, y2 in boxes:
        d.rectangle([x1, y1, x2, y2], outline=(255, 40, 40), width=max(2, out.width // 200))
        if label:
            d.text((x1 + 3, y1 + 3), label, fill=(255, 255, 255))
    return out


def draw_mask(img: Image.Image, mask: np.ndarray, palette: dict, alpha: float = 0.55) -> Image.Image:
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    if mask.shape != rgb.shape[:2]:
        mask = np.asarray(Image.fromarray(mask.astype(np.uint8)).resize((rgb.shape[1], rgb.shape[0]), Image.NEAREST))
    for value, color in palette.items():
        sel = mask == value
        rgb[sel] = (1 - alpha) * rgb[sel] + alpha * np.array(color, dtype=np.float32)
    return Image.fromarray(rgb.clip(0, 255).astype(np.uint8))
