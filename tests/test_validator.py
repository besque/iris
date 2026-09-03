"""Run: .venv/bin/python -m pytest tests/ (or plain python, it has a main)."""

import os
import sys

import numpy as np
import rasterio
from rasterio.transform import from_bounds

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocessing.validator import to_rgb, validate_inputs  # noqa: E402

TMP = "/tmp/satquery_test"
os.makedirs(TMP, exist_ok=True)


def make_tif(name, bands, dtype, bounds=(77.0, 12.0, 77.1, 12.1), size=64):
    path = os.path.join(TMP, name)
    data = (np.random.rand(bands, size, size) * 100 + 1).astype(dtype)
    with rasterio.open(
        path, "w", driver="GTiff", height=size, width=size, count=bands,
        dtype=dtype, crs="EPSG:4326",
        transform=from_bounds(*bounds, size, size),
    ) as dst:
        dst.write(data)
    return path


def test_single_optical():
    p = make_tif("optical4band.tif", 4, "uint16")
    r = validate_inputs([p])
    assert r["config_type"] == "single_optical"


def test_single_sar():
    p = make_tif("scene_vv.tif", 1, "float32")
    r = validate_inputs([p])
    assert r["config_type"] == "single_sar"


def test_crossmodal_pair():
    opt = make_tif("optical.tif", 4, "uint16")
    sar = make_tif("sar_vv.tif", 1, "float32")
    r = validate_inputs([opt, sar])
    assert r["config_type"] == "crossmodal_pair"


def test_bitemporal_pair():
    t1 = make_tif("date1.tif", 4, "uint16")
    t2 = make_tif("date2.tif", 4, "uint16")
    r = validate_inputs([t1, t2])
    assert r["config_type"] == "bitemporal_pair"


def test_non_overlapping_pair_rejected():
    a = make_tif("here.tif", 4, "uint16", bounds=(77.0, 12.0, 77.1, 12.1))
    b = make_tif("elsewhere.tif", 4, "uint16", bounds=(10.0, 50.0, 10.1, 50.1))
    try:
        validate_inputs([a, b])
        assert False, "should have raised"
    except ValueError:
        pass


def test_to_rgb_shapes():
    opt = make_tif("conv_opt.tif", 4, "uint16")
    sar = make_tif("conv_sar_vv.tif", 1, "float32")
    for p in (opt, sar):
        arr = to_rgb(p)
        assert arr.shape == (64, 64, 3) and arr.dtype == np.uint8
    assert to_rgb(opt, target_size=(32, 32)).shape == (32, 32, 3)


if __name__ == "__main__":
    fns = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"pass: {fn.__name__}")
    print(f"\n{len(fns)} tests passed")
