import math
from typing import Any


ALLOWED_GEOMETRY_TYPES = {
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
}


def classify_hazard_color(
    fos: float,
    blsr: float,
    ccsi: float,
    rts: float,
) -> str:
    """
    Classify the hazard zone color into 'red', 'yellow', or 'green'.

    Decision Logic:
        RED:
            Return 'red' if ANY condition is met:
            - fos < 1.0
            - ccsi > 70.0
            - rts >= 0.70

        YELLOW:
            Only if no RED condition is true, return 'yellow' if ANY condition is met:
            - 1.0 <= fos <= 1.5
            - 40.0 <= ccsi <= 70.0
            - 0.40 <= rts < 0.70
            - blsr >= 1.0

        GREEN:
            Return 'green' if none of the RED or YELLOW conditions are met.

    Scientific & Integration Provenance:
        - FOS thresholds (< 1.0 unstable, 1.0-1.5 marginal, > 1.5 stable) are source-supported.
        - CCSI > 70.0 is source-supported as high stress.
        - The complete combined FOS/BLSR/CCSI/RTS color matrix is a PROTOTYPE INTEGRATION CONVENTION
          and is NOT explicitly specified in the research documents.

    Args:
        fos (float): Factor of Safety (> 0.0).
        blsr (float): Built-up Load to Slope Ratio (>= 0.0).
        ccsi (float): Carrying Capacity Susceptibility Index in [0.0, 100.0].
        rts (float): Relocation Triage Score in [0.0, 1.0].

    Returns:
        str: 'red' | 'yellow' | 'green'
    """
    for name, val in [
        ("fos", fos),
        ("blsr", blsr),
        ("ccsi", ccsi),
        ("rts", rts),
    ]:
        if not isinstance(val, (int, float)):
            raise TypeError(f"{name} must be numeric.")
        if not math.isfinite(val):
            raise ValueError(f"{name} must be a finite number.")

    if fos <= 0.0:
        raise ValueError("fos must be strictly positive (> 0.0).")
    if blsr < 0.0:
        raise ValueError("blsr must be non-negative (>= 0.0).")
    if not (0.0 <= ccsi <= 100.0):
        raise ValueError("ccsi must be in range [0.0, 100.0].")
    if not (0.0 <= rts <= 1.0):
        raise ValueError("rts must be in range [0.0, 1.0].")

    # 1. RED evaluation (highest priority)
    if fos < 1.0 or ccsi > 70.0 or rts >= 0.70:
        return "red"

    # 2. YELLOW evaluation (evaluated only if no RED condition met)
    if (1.0 <= fos <= 1.5) or (40.0 <= ccsi <= 70.0) or (0.40 <= rts < 0.70) or (blsr >= 1.0):
        return "yellow"

    # 3. GREEN evaluation (all criteria within safe bounds)
    return "green"


def build_hazard_zone_feature(
    zone_id: str,
    geometry: dict[str, Any],
    fos: float,
    blsr: float,
    ccsi: float,
    rts: float,
    confidence_score: float,
    zone_color: str,
    terrain_mode: str,
    is_transitional: bool,
) -> dict[str, Any]:
    """
    Construct an RFC 7946 compliant GeoJSON Feature dictionary.

    Args:
        zone_id (str): Unique zone identifier (non-empty string).
        geometry (dict): GeoJSON geometry dictionary.
        fos (float): Factor of Safety.
        blsr (float): Built-up Load to Slope Ratio.
        ccsi (float): Carrying Capacity Susceptibility Index.
        rts (float): Relocation Triage Score (used for validation; not in output properties).
        confidence_score (float): Prediction confidence score (non-negative).
        zone_color (str): 'red' | 'yellow' | 'green'.
        terrain_mode (str): 'mountain' | 'plains'.
        is_transitional (bool): Transitional slope flag.

    Returns:
        dict: GeoJSON Feature dictionary conforming strictly to the 8-key property schema.
    """
    # Validate zone_id
    if not isinstance(zone_id, str) or not zone_id.strip():
        raise ValueError("zone_id must be a non-empty string.")

    # Validate geometry
    if not isinstance(geometry, dict):
        raise TypeError("geometry must be a dictionary.")
    geo_type = geometry.get("type")
    if not isinstance(geo_type, str) or geo_type not in ALLOWED_GEOMETRY_TYPES:
        raise ValueError(f"geometry['type'] must be one of {ALLOWED_GEOMETRY_TYPES}.")

    if geo_type == "GeometryCollection":
        if "geometries" not in geometry:
            raise ValueError("GeometryCollection must contain 'geometries'.")
        if not isinstance(geometry["geometries"], list):
            raise TypeError("GeometryCollection 'geometries' must be a list.")
    else:
        if "coordinates" not in geometry:
            raise ValueError(f"geometry of type '{geo_type}' must contain 'coordinates'.")

    # Validate numeric parameters
    for name, val in [
        ("fos", fos),
        ("blsr", blsr),
        ("ccsi", ccsi),
        ("rts", rts),
        ("confidence_score", confidence_score),
    ]:
        if not isinstance(val, (int, float)):
            raise TypeError(f"{name} must be numeric.")
        if not math.isfinite(val):
            raise ValueError(f"{name} must be a finite number.")

    if fos <= 0.0:
        raise ValueError("fos must be strictly positive (> 0.0).")
    if blsr < 0.0:
        raise ValueError("blsr must be non-negative (>= 0.0).")
    if not (0.0 <= ccsi <= 100.0):
        raise ValueError("ccsi must be in range [0.0, 100.0].")
    if not (0.0 <= rts <= 1.0):
        raise ValueError("rts must be in range [0.0, 1.0].")
    if confidence_score < 0.0:
        raise ValueError("confidence_score must be non-negative (>= 0.0).")

    # Validate enums & bools
    if zone_color not in ("red", "yellow", "green"):
        raise ValueError("zone_color must be 'red', 'yellow', or 'green'.")
    if terrain_mode not in ("mountain", "plains"):
        raise ValueError("terrain_mode must be 'mountain' or 'plains'.")
    if not isinstance(is_transitional, bool):
        raise TypeError("is_transitional must be a boolean.")

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "zone_id": zone_id,
            "fos": float(fos),
            "blsr": float(blsr),
            "ccsi": float(ccsi),
            "confidence_score": float(confidence_score),
            "zone_color": zone_color,
            "terrain_mode": terrain_mode,
            "is_transitional": is_transitional,
        },
    }


def generate_hazard_zones(
    zones_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate an RFC 7946 compliant GeoJSON FeatureCollection dictionary from zone records.

    Each record in zones_data must contain:
        - 'zone_id': str
        - 'geometry': dict
        - 'fos': float
        - 'blsr': float
        - 'ccsi': float
        - 'rts': float
        - 'confidence_score': float
        - 'terrain_mode': str
        - 'is_transitional': bool
        - Optional 'zone_color': str (if omitted, computed automatically via classify_hazard_color)

    Args:
        zones_data (list[dict]): List of zone input dictionaries.

    Returns:
        dict: GeoJSON FeatureCollection dictionary.
    """
    if not isinstance(zones_data, list):
        raise TypeError("zones_data must be a list.")

    if not zones_data:
        return {
            "type": "FeatureCollection",
            "features": [],
        }

    features = []
    required_keys = (
        "zone_id",
        "geometry",
        "fos",
        "blsr",
        "ccsi",
        "rts",
        "confidence_score",
        "terrain_mode",
        "is_transitional",
    )

    for idx, record in enumerate(zones_data):
        if not isinstance(record, dict):
            raise TypeError(f"Zone record at index {idx} must be a dictionary.")

        for key in required_keys:
            if key not in record:
                raise ValueError(f"Zone record at index {idx} missing required key '{key}'.")

        # Automatic color classification if not provided
        zone_color = record.get("zone_color")
        if zone_color is None:
            zone_color = classify_hazard_color(
                fos=record["fos"],
                blsr=record["blsr"],
                ccsi=record["ccsi"],
                rts=record["rts"],
            )

        feature = build_hazard_zone_feature(
            zone_id=record["zone_id"],
            geometry=record["geometry"],
            fos=record["fos"],
            blsr=record["blsr"],
            ccsi=record["ccsi"],
            rts=record["rts"],
            confidence_score=record["confidence_score"],
            zone_color=zone_color,
            terrain_mode=record["terrain_mode"],
            is_transitional=record["is_transitional"],
        )
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }
