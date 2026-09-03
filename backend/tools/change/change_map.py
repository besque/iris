"""Classical change map: where do two aligned images differ. No model needed."""

import numpy as np
from PIL import Image, ImageFilter

GRID_NAMES = [
    ["north-west", "north", "north-east"],
    ["west", "center", "east"],
    ["south-west", "south", "south-east"],
]


BLUR = 3        # px, hides tiny misregistration between dates
CLEAN = 11      # median filter size on the mask, kills speckle


def _gray(img: Image.Image, size) -> np.ndarray:
    g = img.convert("L").resize(size).filter(ImageFilter.GaussianBlur(BLUR))
    return np.asarray(g, dtype=np.float32)


def _otsu(values: np.ndarray) -> float:
    hist, edges = np.histogram(values, bins=256, range=(0, 255))
    centers = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = w0[-1] - w0
    m0 = np.cumsum(hist * centers) / np.maximum(w0, 1)
    m1 = (np.cumsum((hist * centers)[::-1])[::-1]) / np.maximum(w1, 1)
    between = w0[:-1] * w1[:-1] * (m0[:-1] - m1[:-1]) ** 2
    return float(centers[np.argmax(between)])


def dominant_region(mask: np.ndarray) -> str:
    h, w = mask.shape
    best, name = -1.0, "center"
    for i in range(3):
        for j in range(3):
            cell = mask[i * h // 3:(i + 1) * h // 3, j * w // 3:(j + 1) * w // 3]
            if cell.mean() > best:
                best, name = cell.mean(), GRID_NAMES[i][j]
    return name


def _edges(gray: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(gray)
    mag = np.hypot(gx, gy)
    return mag / (np.percentile(mag, 99) + 1e-6) * 255


def change_map(img_a: Image.Image, img_b: Image.Image, method: str = "edges",
               min_threshold: float = 25.0) -> dict:
    """Returns mask (bool HxW), percent changed, and where the change concentrates.
    'edges' ignores seasonal colour shifts and reacts to new structures; 'intensity' is the plain diff."""
    size = img_a.size
    a, b = _gray(img_a, size), _gray(img_b, size)
    # normalise brightness so a sunnier second image does not read as change
    b = (b - b.mean()) * (a.std() / (b.std() + 1e-6)) + a.mean()
    if method == "edges":
        a, b = _edges(a), _edges(b)
    diff = np.abs(a - b)
    thr = max(_otsu(np.clip(diff, 0, 255)), min_threshold)
    mask = diff > thr
    mask = np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MedianFilter(CLEAN))) > 127
    pct = float(100 * mask.mean())
    return {
        "mask": mask,
        "percent": round(pct, 1),
        "region": dominant_region(mask) if pct > 0.5 else "none",
        "threshold": round(thr, 1),
    }
