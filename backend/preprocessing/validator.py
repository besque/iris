"""Input validation & compatibility checking.

Before the agent sees anything, this module must answer:
- How many images? What format (GeoTIFF/TIFF/PNG/JPEG)?
- What modality (optical/multispectral vs SAR)? Band count/metadata hints.
- For pairs: same geographic area? Same size/CRS? Co-registered?
- Classify the input configuration:
    "single_optical" | "single_sar" | "bitemporal_pair" | "crossmodal_pair"
"""


def validate_inputs(file_paths: list[str]) -> dict:
    """Returns {config_type, images: [...], warnings: [...]} or raises a clear error."""
    raise NotImplementedError
