import math


def determine_terrain_mode(
    mean_slope: float,
) -> tuple[str, bool]:
    """
    Determine the operating terrain mode and transitional status from mean terrain slope.

    Scientific Geomorphic Rules:
        - mean_slope < 5.0  -> ("plains", False)
        - mean_slope > 15.0 -> ("mountain", False)
        - 5.0 <= mean_slope <= 15.0 -> Transitional band (is_transitional = True)

    Integration Convention for 2-value terrain_mode Contract:
        - 5.0 <= mean_slope < 10.0  -> ("plains", True)
        - 10.0 <= mean_slope <= 15.0 -> ("mountain", True)

    Args:
        mean_slope (float): Mean terrain slope in degrees (>= 0.0).

    Returns:
        tuple[str, bool]: (terrain_mode, is_transitional) where terrain_mode is 'mountain' | 'plains'.
    """
    if not isinstance(mean_slope, (int, float)):
        raise TypeError("mean_slope must be numeric.")
    if not math.isfinite(mean_slope):
        raise ValueError("mean_slope must be a finite number.")
    if mean_slope < 0.0:
        raise ValueError("mean_slope must be non-negative (>= 0.0).")

    if mean_slope < 5.0:
        return ("plains", False)
    elif mean_slope > 15.0:
        return ("mountain", False)
    else:
        # Transitional band: 5.0 <= mean_slope <= 15.0
        if mean_slope >= 10.0:
            return ("mountain", True)
        else:
            return ("plains", True)
