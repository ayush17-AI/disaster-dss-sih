import math


def calculate_fos(
    beta: float,
    z: float,
    c_prime: float,
    phi_prime: float,
    m: float,
    q: float,
    gamma_sat: float,
    gamma_w: float,
) -> float:
    """
    Calculate the Factor of Safety (FOS) for slope stability using the infinite slope model with surcharge.

    Formula:
        FOS = [c' + ((gamma_sat * z + q) - m * gamma_w * z) * cos^2(beta) * tan(phi')]
              / [(gamma_sat * z + q) * sin(beta) * cos(beta)]

    Args:
        beta (float): Slope angle (degrees).
        z (float): Soil depth (m).
        c_prime (float): Effective cohesion (kPa).
        phi_prime (float): Effective friction angle (degrees).
        m (float): Groundwater ratio (dimensionless, 0.0 to 1.0).
        q (float): Construction/surcharge load (kPa).
        gamma_sat (float): Saturated unit weight of soil (kN/m^3).
        gamma_w (float): Unit weight of water (kN/m^3).

    Returns:
        float: Calculated FOS value.

    Implementation Conventions:
        - IMPLEMENTATION CONVENTION - NOT SPECIFIED IN PROJECT DOCUMENTS: When beta == 0.0 (flat slope),
          driving shear stress is zero, returning float('inf').
    """
    if z < 0:
        raise ValueError("Soil depth z must be non-negative.")
    if beta < 0 or beta >= 90:
        raise ValueError("Slope angle beta must be in range [0, 90) degrees.")
    if phi_prime < 0 or phi_prime >= 90:
        raise ValueError("Friction angle phi_prime must be in range [0, 90) degrees.")
    if m < 0:
        raise ValueError("Groundwater ratio m must be non-negative.")
    if q < 0:
        raise ValueError("Surcharge load q must be non-negative.")
    if c_prime < 0:
        raise ValueError("Effective cohesion c_prime must be non-negative.")
    if gamma_sat <= 0:
        raise ValueError("Saturated unit weight gamma_sat must be strictly positive.")
    if gamma_w <= 0:
        raise ValueError("Water unit weight gamma_w must be strictly positive.")

    # Mathematical boundary convention for flat slope
    if beta == 0.0:
        return float("inf")

    beta_rad = math.radians(beta)
    phi_rad = math.radians(phi_prime)

    total_overburden = gamma_sat * z + q
    if total_overburden <= 0:
        return float("inf")

    cos_beta = math.cos(beta_rad)
    sin_beta = math.sin(beta_rad)
    cos2_beta = cos_beta * cos_beta

    effective_normal_term = total_overburden - (m * gamma_w * z)

    resisting_force = c_prime + effective_normal_term * cos2_beta * math.tan(phi_rad)
    driving_force = total_overburden * sin_beta * cos_beta

    if driving_force <= 0:
        return float("inf")

    return float(resisting_force / driving_force)


def calculate_blsr(
    buildings: list[dict],
    safe_soil_bearing_capacity: float,
    habitable_land_area: float,
) -> float:
    """
    Calculate the Built-up Load to Slope Ratio (BLSR) from heterogeneous building structures.

    Formula:
        BLSR = SUM(building_footprint_area_i * storeys_i * construction_type_weight_i)
               / (safe_bearing_capacity_of_soil * habitable_land_area)

    Args:
        buildings (list[dict]): List of building records. Each dictionary must contain:
            - 'footprint_area' (float): Building footprint area (m^2).
            - 'storeys' (float): Number of storeys.
            - 'construction_type_weight' (float): Material/structural weight factor.
        safe_soil_bearing_capacity (float): Safe soil bearing capacity (kPa or kN/m^2).
        habitable_land_area (float): Habitable land area of the zone (m^2).

    Returns:
        float: Calculated BLSR value. Returns 0.0 if buildings list is empty.

    Implementation Conventions:
        - IMPLEMENTATION CONVENTION - NOT SPECIFIED IN PROJECT DOCUMENTS: Empty buildings list
          evaluates to numerator = 0.0, returning 0.0.
    """
    if safe_soil_bearing_capacity <= 0:
        raise ValueError("safe_soil_bearing_capacity must be strictly positive.")
    if habitable_land_area <= 0:
        raise ValueError("habitable_land_area must be strictly positive.")

    if not buildings:
        return 0.0

    numerator = 0.0
    required_keys = ("footprint_area", "storeys", "construction_type_weight")

    for idx, b in enumerate(buildings):
        if not isinstance(b, dict):
            raise TypeError(f"Building record at index {idx} must be a dictionary.")
        for key in required_keys:
            if key not in b:
                raise ValueError(f"Building record at index {idx} missing required key '{key}'.")
            val = b[key]
            if not isinstance(val, (int, float)):
                raise TypeError(f"Building record at index {idx} key '{key}' must be numeric.")
            if val < 0:
                raise ValueError(f"Building record at index {idx} key '{key}' must be non-negative.")

        numerator += float(b["footprint_area"]) * float(b["storeys"]) * float(b["construction_type_weight"])

    denominator = safe_soil_bearing_capacity * habitable_land_area

    return float(numerator / denominator)

def calculate_rts(
    tti_hours: float,
    svi: float,
    blsr: float,
    demo_exposure: float,
) -> float:
    """
    Calculate the Relocation Triage Score (RTS) for habitation evacuation ranking.

    Formula:
        RTS = 0.35 * tti_score + 0.25 * SVI + 0.20 * struct_load + 0.20 * demo_exposure

    Component Normalization (Integration Specification):
        - tti_score: min(1.0, 12.0 / max(1.0, tti_hours))
        - struct_load: min(1.0, blsr / 2.0)
        - SVI: directly in range [0.0, 1.0]
        - demo_exposure: directly in range [0.0, 1.0]

    Args:
        tti_hours (float): Time to inundation / impact in hours (> 0.0).
        svi (float): Social Vulnerability Index in [0.0, 1.0].
        blsr (float): Built-up Load to Slope Ratio (>= 0.0).
        demo_exposure (float): Demographic Exposure metric in [0.0, 1.0].

    Returns:
        float: Calculated RTS score in range [0.0, 1.0] (sorted descending for priority).
    """
    for name, val in [
        ("tti_hours", tti_hours),
        ("svi", svi),
        ("blsr", blsr),
        ("demo_exposure", demo_exposure),
    ]:
        if not isinstance(val, (int, float)):
            raise TypeError(f"{name} must be numeric.")
        if not math.isfinite(val):
            raise ValueError(f"{name} must be a finite number.")

    if tti_hours <= 0.0:
        raise ValueError("tti_hours must be strictly positive (> 0.0).")
    if not (0.0 <= svi <= 1.0):
        raise ValueError("svi must be in range [0.0, 1.0].")
    if blsr < 0.0:
        raise ValueError("blsr must be non-negative (>= 0.0).")
    if not (0.0 <= demo_exposure <= 1.0):
        raise ValueError("demo_exposure must be in range [0.0, 1.0].")

    tti_score = min(1.0, 12.0 / max(1.0, tti_hours))
    struct_load = min(1.0, blsr / 2.0)

    rts = (
        0.35 * tti_score
        + 0.25 * svi
        + 0.20 * struct_load
        + 0.20 * demo_exposure
    )

    return float(rts)

def calculate_confidence(
    s_res: float,
    s_source: float,
    s_prox: float,
) -> float:
    """
    Calculate the composite confidence score for hazard predictions.

    Formula:
        Confidence = 0.40 * S_res + 0.35 * S_source + 0.25 * S_prox

    Args:
        s_res (float): Resolution compatibility score.
        s_source (float): Reliability of soil data source.
        s_prox (float): Proximity / reliability of rainfall observation.

    Returns:
        float: Calculated weighted composite confidence score.

    Scientific Traceability:
        - Exact linear composite weights (0.40, 0.35, 0.25) from Team Blueprint / Research Dossier.
        - INPUT RANGE NOT SPECIFIED IN PROJECT DOCUMENTS.
        - OUTPUT SCALING NOT SPECIFIED IN PROJECT DOCUMENTS.
    """
    if not (
        isinstance(s_res, (int, float))
        and isinstance(s_source, (int, float))
        and isinstance(s_prox, (int, float))
    ):
        raise TypeError("Confidence inputs s_res, s_source, and s_prox must be numeric.")

    if not (
        math.isfinite(s_res)
        and math.isfinite(s_source)
        and math.isfinite(s_prox)
    ):
        raise ValueError("Confidence inputs s_res, s_source, and s_prox must be finite numbers.")

    return float(0.40 * s_res + 0.35 * s_source + 0.25 * s_prox)


def calculate_ccsi(
    fos: float,
    blsr: float,
    drainage_congestion_index: float,
    deformation_rate_mm_yr: float,
    terrain_mode: str,
) -> float:
    """
    Calculate the Carrying Capacity Susceptibility Index (CCSI).

    Formula:
        CCSI = (w1 * norm_inv_fos + w2 * norm_blsr + w3 * drainage_congestion_index + w4 * norm_def) * 100.0

    Terrain-specific weights (Integration Specification):
        - 'mountain': w1=0.40, w2=0.30, w3=0.15, w4=0.15
        - 'plains':   w1=0.10, w2=0.25, w3=0.50, w4=0.15

    Normalization Rules:
        - FOS risk: 1.0 if fos <= 0.5; 0.0 if fos >= 2.0; (2.0 - fos) / 1.5 otherwise.
        - BLSR: min(1.0, blsr / 2.0).
        - DCI: directly in range [0.0, 1.0].
        - Deformation: min(1.0, abs(deformation_rate_mm_yr) / 100.0).

    Args:
        fos (float): Factor of safety (> 0.0).
        blsr (float): Built-up load to slope ratio (>= 0.0).
        drainage_congestion_index (float): Drainage congestion index in [0.0, 1.0].
        deformation_rate_mm_yr (float): Surface deformation rate in mm/yr.
        terrain_mode (str): Operating terrain mode, exactly 'mountain' or 'plains'.

    Returns:
        float: Calculated CCSI value in range [0.0, 100.0]. Values > 70.0 indicate high stress.
    """
    if not isinstance(terrain_mode, str) or terrain_mode not in ("mountain", "plains"):
        raise ValueError("terrain_mode must be exactly 'mountain' or 'plains'.")

    for name, val in [
        ("fos", fos),
        ("blsr", blsr),
        ("drainage_congestion_index", drainage_congestion_index),
        ("deformation_rate_mm_yr", deformation_rate_mm_yr),
    ]:
        if not isinstance(val, (int, float)):
            raise TypeError(f"{name} must be numeric.")
        if not math.isfinite(val):
            raise ValueError(f"{name} must be a finite number.")

    if fos <= 0.0:
        raise ValueError("fos must be strictly positive (> 0.0).")
    if blsr < 0.0:
        raise ValueError("blsr must be non-negative (>= 0.0).")
    if not (0.0 <= drainage_congestion_index <= 1.0):
        raise ValueError("drainage_congestion_index must be in range [0.0, 1.0].")

    if terrain_mode == "mountain":
        w1, w2, w3, w4 = 0.40, 0.30, 0.15, 0.15
    else:  # "plains"
        w1, w2, w3, w4 = 0.10, 0.25, 0.50, 0.15

    # 1. FOS risk normalization
    if fos <= 0.5:
        norm_inv_fos = 1.0
    elif fos >= 2.0:
        norm_inv_fos = 0.0
    else:
        norm_inv_fos = (2.0 - fos) / 1.5

    # 2. BLSR normalization
    norm_blsr = min(1.0, blsr / 2.0)

    # 3. DCI (already in [0.0, 1.0])
    norm_dci = drainage_congestion_index

    # 4. Deformation normalization
    norm_def = min(1.0, abs(deformation_rate_mm_yr) / 100.0)

    ccsi_normalized = (
        w1 * norm_inv_fos
        + w2 * norm_blsr
        + w3 * norm_dci
        + w4 * norm_def
    )

    return float(ccsi_normalized * 100.0)
