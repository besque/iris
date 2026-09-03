"""Checks uploaded images: format, modality, pair compatibility."""


def validate_inputs(file_paths: list[str]) -> dict:
    """Returns config_type, images, warnings.
    config_type: single_optical | single_sar | bitemporal_pair | crossmodal_pair
    """
    raise NotImplementedError
