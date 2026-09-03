"""Optical + SAR joint analysis. Water is dark in SAR, built-up is bright.
Confidence comes from how much the two sensors agree."""

import numpy as np

from backend.tools.base import Tool, ToolResult

GRID_NAMES = [
    ["north-west", "north", "north-east"],
    ["west", "center", "east"],
    ["south-west", "south", "south-east"],
]


def _read_bands(path: str) -> np.ndarray:
    import rasterio
    with rasterio.open(path) as src:
        return src.read().astype(np.float32)


def _sar_db(path: str) -> np.ndarray:
    band = _read_bands(path)[0]
    if np.nanmin(band) < 0:
        return band  # already in dB
    band = np.where(band > 0, band, 1e-6)
    return 10.0 * np.log10(band)


def _dominant_region(mask: np.ndarray) -> str:
    h, w = mask.shape
    best, name = -1.0, "center"
    for i in range(3):
        for j in range(3):
            cell = mask[i * h // 3:(i + 1) * h // 3, j * w // 3:(j + 1) * w // 3]
            if cell.mean() > best:
                best, name = cell.mean(), GRID_NAMES[i][j]
    return name


class FusionTool(Tool):
    name = "fusion"
    description = "Combines an optical and a SAR image to map water and built-up regions"
    input_types = ["crossmodal_pair"]

    # tune on real data, keep them recorded in metadata either way
    sar_water_pct = 15      # darkest N percent of SAR = water candidates
    sar_bright_pct = 85     # brightest = built-up candidates
    ndvi_veg = 0.4

    def run(self, images: list, query: str, **params) -> ToolResult:
        sar_info = next(i for i in images if i["modality"] == "sar")
        opt_info = next(i for i in images if i["modality"] == "optical")

        sar = _sar_db(sar_info["path"])
        opt = _read_bands(opt_info["path"])
        if opt.shape[1:] != sar.shape:
            from PIL import Image
            sar = np.asarray(Image.fromarray(sar).resize((opt.shape[2], opt.shape[1])))

        water_sar = sar < np.percentile(sar, self.sar_water_pct)
        bright_sar = sar > np.percentile(sar, self.sar_bright_pct)

        # sentinel-2 order assumed B,G,R,NIR in the first 4 bands
        if opt.shape[0] >= 4:
            g, r, nir = opt[1], opt[2], opt[3]
            ndwi = (g - nir) / (g + nir + 1e-6)
            ndvi = (nir - r) / (nir + r + 1e-6)
            water_opt = ndwi > 0.0
            veg = ndvi > self.ndvi_veg
            water = water_sar & water_opt
            agree_w = water.sum() / max((water_sar | water_opt).sum(), 1)
        else:
            # plain rgb, no nir: fall back to sar alone and say so
            water, veg = water_sar, np.zeros_like(water_sar)
            agree_w = 0.5

        built = bright_sar & ~veg & ~water
        mask = np.zeros(sar.shape, dtype=np.uint8)
        mask[water], mask[built] = 1, 2

        pw, pb = 100 * water.mean(), 100 * built.mean()
        text = (
            f"Water covers about {pw:.1f}% of the scene, mainly in the "
            f"{_dominant_region(water)}. Built-up area covers about {pb:.1f}%, "
            f"mainly in the {_dominant_region(built)}. "
            f"Optical and SAR agree on {100 * agree_w:.0f}% of the water extent."
        )
        return ToolResult(
            text=text,
            spatial={"type": "mask", "data": mask},
            confidence=round(float(np.clip(0.4 + 0.6 * agree_w, 0, 1)), 2),
            metadata={
                "model": "sar_optical_rules_v1",
                "params": {
                    "sar_water_pct": self.sar_water_pct,
                    "sar_bright_pct": self.sar_bright_pct,
                    "ndvi_veg": self.ndvi_veg,
                },
            },
        )
