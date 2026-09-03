import math

def calculate_fos(beta: float, z: float, c_prime: float, phi_prime: float, m: float, q: float) -> float:
    """
    Calculate the Factor of Safety (FOS) using Infinite Slope Stability equation.
    m: saturation ratio (0.0 to 1.0)
    q: surcharge load (kPa)
    """
    gamma = 20.0  # Unit weight of soil (kN/m^3)
    gamma_w = 9.81  # Unit weight of water (kN/m^3)
    beta_rad = math.radians(beta)
    phi_rad = math.radians(phi_prime)

    normal_stress_total = (gamma * z + q) * (math.cos(beta_rad) ** 2)
    pore_pressure = m * gamma_w * z * (math.cos(beta_rad) ** 2)
    effective_normal_stress = normal_stress_total - pore_pressure
    
    shear_strength = c_prime + effective_normal_stress * math.tan(phi_rad)
    shear_stress = (gamma * z + q) * math.sin(beta_rad) * math.cos(beta_rad)
    
    if shear_stress <= 0:
        return 99.99
    return round(shear_strength / shear_stress, 3)

def calculate_blsr(buildings_area: float, zone_area: float) -> float:
    if zone_area == 0: return 0.0
    return round((buildings_area / zone_area) * 100.0, 2)

def calculate_rts(rainfall_intensity: float, terrain_slope: float, soil_type_factor: float) -> float:
    return round((rainfall_intensity * math.tan(math.radians(terrain_slope))) / (soil_type_factor + 0.001), 3)

def calculate_confidence(data_quality_index: float, model_accuracy: float) -> float:
    return round((data_quality_index * 0.4 + model_accuracy * 0.6) * 100.0, 2)
