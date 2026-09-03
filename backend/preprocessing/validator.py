"""Checks uploaded images: format, modality, pair compatibility."""

import os

import numpy as np

RASTER_EXTS = {".tif", ".tiff"}
PLAIN_EXTS = {".png", ".jpg", ".jpeg"}
SAR_NAME_HINTS = ("sar", "s1", "vv", "vh", "risat", "eos04", "sentinel1", "sentinel-1")


def _open_info(path: str) -> dict:
    """Returns band count, dtype, size, geo bounds and crs if present."""
    ext = os.path.splitext(path)[1].lower()
    if ext in RASTER_EXTS:
        import rasterio
        with rasterio.open(path) as src:
            return {
                "path": path, "bands": src.count, "dtype": src.dtypes[0],
                "size": (src.height, src.width),
                "crs": str(src.crs) if src.crs else None,
                "bounds": tuple(src.bounds) if src.crs else None,
            }
    if ext in PLAIN_EXTS:
        from PIL import Image
        with Image.open(path) as im:
            return {
                "path": path, "bands": len(im.getbands()), "dtype": "uint8",
                "size": (im.height, im.width), "crs": None, "bounds": None,
            }
    raise ValueError(f"unsupported format: {path} (need GeoTIFF/TIFF/PNG/JPEG)")


def detect_modality(info: dict) -> tuple[str, str]:
    """Returns (modality, reason). Heuristics, good enough for today."""
    name = os.path.basename(info["path"]).lower()
    if any(h in name for h in SAR_NAME_HINTS):
        return "sar", f"filename hint in '{name}'"
    if info["bands"] <= 2 and info["dtype"] != "uint8":
        return "sar", f"{info['bands']} band(s), dtype {info['dtype']}"
    if info["bands"] <= 2:
        return "sar", f"{info['bands']} band(s)"
    return "optical", f"{info['bands']} bands"


def _bounds_overlap(a, b) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def validate_inputs(file_paths: list[str]) -> dict:
    """Returns {config_type, images, warnings}. Raises ValueError on bad input."""
    if not 1 <= len(file_paths) <= 2:
        raise ValueError(f"expected 1 or 2 images, got {len(file_paths)}")

    warnings = []
    infos = [_open_info(p) for p in file_paths]
    for info in infos:
        info["modality"], reason = detect_modality(info)
        warnings.append(f"{os.path.basename(info['path'])}: {info['modality']} ({reason})")

    if len(infos) == 1:
        config = f"single_{infos[0]['modality']}"
        return {"config_type": config, "images": infos, "warnings": warnings}

    a, b = infos
    if a["bounds"] and b["bounds"]:
        if a["crs"] != b["crs"]:
            warnings.append(f"CRS differs: {a['crs']} vs {b['crs']}")
        elif not _bounds_overlap(a["bounds"], b["bounds"]):
            raise ValueError("the two images do not cover the same area")
    else:
        warnings.append("no geo metadata on both images, assuming co-registered")
    if a["size"] != b["size"]:
        warnings.append(f"sizes differ {a['size']} vs {b['size']}, second will be resized")

    if a["modality"] != b["modality"]:
        config = "crossmodal_pair"
    else:
        config = "bitemporal_pair"
    return {"config_type": config, "images": infos, "warnings": warnings}


def to_rgb(path: str, target_size: tuple[int, int] | None = None) -> np.ndarray:
    """Any supported image to uint8 HxWx3 for the VLM tools."""
    ext = os.path.splitext(path)[1].lower()
    if ext in PLAIN_EXTS:
        from PIL import Image
        im = Image.open(path).convert("RGB")
        if target_size:
            im = im.resize((target_size[1], target_size[0]))
        return np.asarray(im)

    import rasterio
    with rasterio.open(path) as src:
        data = src.read().astype(np.float32)

    if data.shape[0] >= 3:
        # sentinel-2 band order is B,G,R in the first bands, so take 3,2,1 as RGB
        rgb = data[[2, 1, 0]] if data.shape[0] > 3 else data[[0, 1, 2]]
    else:
        band = data[0]
        band = np.where(band > 0, band, np.nan)
        band = 10.0 * np.log10(band, out=np.full_like(band, np.nan), where=band > 0)
        rgb = np.stack([band] * 3)

    out = np.zeros_like(rgb)
    for i in range(3):
        ch = rgb[i]
        lo, hi = np.nanpercentile(ch, 2), np.nanpercentile(ch, 98)
        out[i] = np.clip((ch - lo) / (hi - lo + 1e-6), 0, 1)
    arr = (np.nan_to_num(np.moveaxis(out, 0, -1)) * 255).astype(np.uint8)

    if target_size and arr.shape[:2] != target_size:
        from PIL import Image
        arr = np.asarray(Image.fromarray(arr).resize((target_size[1], target_size[0])))
    return arr
