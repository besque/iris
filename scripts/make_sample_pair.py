"""Makes a synthetic Sentinel-1/Sentinel-2 style pair with a lake and a town.
Used by tests and as bundled demo data until real samples are downloaded."""

import os

import numpy as np
import rasterio
from rasterio.transform import from_bounds

SIZE = 120


def _write(path, data):
    with rasterio.open(
        path, "w", driver="GTiff", height=SIZE, width=SIZE, count=data.shape[0],
        dtype=str(data.dtype), crs="EPSG:4326",
        transform=from_bounds(77.0, 12.0, 77.1, 12.1, SIZE, SIZE),
    ) as dst:
        dst.write(data)
    return path


def make_pair(out_dir: str) -> tuple[str, str]:
    """Returns (optical_path, sar_path)."""
    os.makedirs(out_dir, exist_ok=True)
    lake = np.zeros((SIZE, SIZE), bool)
    lake[:40, :40] = True
    town = np.zeros((SIZE, SIZE), bool)
    town[80:, 80:] = True

    sar = np.full((1, SIZE, SIZE), 0.1, np.float32)
    sar[0][lake] = 0.001
    sar[0][town] = 2.0

    opt = np.full((4, SIZE, SIZE), 1500, np.uint16)  # b, g, r, nir
    opt[3][:, :] = 3000
    opt[1][lake], opt[3][lake] = 2500, 500
    opt[3][town], opt[2][town] = 800, 2000

    return (
        _write(os.path.join(out_dir, "sample_s2.tif"), opt),
        _write(os.path.join(out_dir, "sample_s1_vv.tif"), sar),
    )


if __name__ == "__main__":
    print(make_pair("data/samples"))
