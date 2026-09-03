import math
import unittest
from backend.geo_engine.formulas import calculate_blsr, calculate_fos


class TestStage1Formulas(unittest.TestCase):
    """
    Stage 1 Test Suite: FOS and BLSR
    Scientific source of truth: Team_Blueprint_Deep_Summary.pdf and SIH_Red_Zone_CCSI_Research_Dossier.md.
    """

    # ==========================================================================
    # 1. FOS Tests
    # ==========================================================================

    def test_fos_analytical_known_value(self):
        """
        Validate FOS against exact analytical calculation from the project equation:
        FOS = [c' + ((gamma_sat*z + q) - m*gamma_w*z) * cos^2(beta) * tan(phi')]
              / [(gamma_sat*z + q) * sin(beta) * cos(beta)]

        # Hand-calculated values:
        # - beta = 30.0 deg -> sin(30) = 0.5, cos(30) = sqrt(3)/2, cos^2(30) = 0.75
        # - phi_prime = 25.0 deg -> tan(25) = 0.4663076581549986
        # - z = 2.0 m, c_prime = 10.0 kPa, m = 0.2, q = 15.0 kPa
        # - gamma_sat = 19.5 kN/m^3, gamma_w = 9.81 kN/m^3
        # - total_overburden = 19.5 * 2.0 + 15.0 = 54.0 kPa
        # - pore_pressure = 0.2 * 9.81 * 2.0 = 3.924 kPa
        # - effective_normal = 54.0 - 3.924 = 50.076 kPa
        # - resisting_force = 10.0 + 50.076 * cos^2(30 deg) * tan(25 deg) = 27.513117283733075
        # - driving_force = 54.0 * sin(30 deg) * cos(30 deg) = 23.382685902179844
        # - expected FOS = 27.513117283733075 / 23.382685902179844 = 1.176644840221815
        """
        fos = calculate_fos(
            beta=30.0,
            z=2.0,
            c_prime=10.0,
            phi_prime=25.0,
            m=0.2,
            q=15.0,
            gamma_sat=19.5,
            gamma_w=9.81,
        )
        self.assertAlmostEqual(fos, 1.176644840221815, places=6)

    def test_fos_angle_conversion_and_pure_cohesion(self):
        """
        Validate angle conversion: when phi_prime = 0 deg, tan(phi_prime) = 0.
        The resisting force reduces strictly to c'.
        """
        # driving_force for beta=30, z=2, q=15, gamma_sat=19.5 is 23.38268590217984
        # Setting c_prime equal to driving_force must yield FOS = 1.0 exactly
        c_val = 54.0 * math.sin(math.radians(30.0)) * math.cos(math.radians(30.0))
        fos = calculate_fos(
            beta=30.0,
            z=2.0,
            c_prime=c_val,
            phi_prime=0.0,
            m=0.0,
            q=15.0,
            gamma_sat=19.5,
            gamma_w=9.81,
        )
        self.assertAlmostEqual(fos, 1.0, places=6)

    def test_fos_groundwater_saturation_effect(self):
        """
        Validate that increasing groundwater ratio m from 0.0 (dry) to 1.0 (fully saturated)
        strictly decreases FOS due to pore water pressure reduction of effective normal stress.
        """
        fos_dry = calculate_fos(
            beta=28.0,
            z=2.5,
            c_prime=8.0,
            phi_prime=25.0,
            m=0.0,
            q=10.0,
            gamma_sat=19.0,
            gamma_w=9.81,
        )
        fos_saturated = calculate_fos(
            beta=28.0,
            z=2.5,
            c_prime=8.0,
            phi_prime=25.0,
            m=1.0,
            q=10.0,
            gamma_sat=19.0,
            gamma_w=9.81,
        )
        self.assertLess(fos_saturated, fos_dry)

    def test_fos_surcharge_destabilization_effect(self):
        """
        Validate that adding structural building surcharge q on an inclined slope
        increases the driving shear stress and reduces FOS.
        """
        fos_no_surcharge = calculate_fos(
            beta=35.0,
            z=2.0,
            c_prime=5.0,
            phi_prime=22.0,
            m=0.3,
            q=0.0,
            gamma_sat=19.0,
            gamma_w=9.81,
        )
        fos_with_surcharge = calculate_fos(
            beta=35.0,
            z=2.0,
            c_prime=5.0,
            phi_prime=22.0,
            m=0.3,
            q=25.0,
            gamma_sat=19.0,
            gamma_w=9.81,
        )
        self.assertLess(fos_with_surcharge, fos_no_surcharge)

    def test_fos_flat_slope_boundary_convention(self):
        """
        IMPLEMENTATION CONVENTION - NOT SPECIFIED IN PROJECT DOCUMENTS:
        When beta == 0.0 (flat terrain), driving shear stress is zero, returning float('inf').
        """
        fos = calculate_fos(
            beta=0.0,
            z=3.0,
            c_prime=10.0,
            phi_prime=25.0,
            m=0.0,
            q=0.0,
            gamma_sat=19.0,
            gamma_w=9.81,
        )
        self.assertEqual(fos, float("inf"))

    def test_fos_invalid_physical_inputs(self):
        """
        Validate rejection of physically invalid domain parameters.
        """
        # Negative soil depth
        with self.assertRaises(ValueError):
            calculate_fos(beta=20.0, z=-1.0, c_prime=10.0, phi_prime=25.0, m=0.0, q=0.0, gamma_sat=19.0, gamma_w=9.81)
        # Invalid slope angle beta (>= 90 or < 0)
        with self.assertRaises(ValueError):
            calculate_fos(beta=90.0, z=2.0, c_prime=10.0, phi_prime=25.0, m=0.0, q=0.0, gamma_sat=19.0, gamma_w=9.81)
        with self.assertRaises(ValueError):
            calculate_fos(beta=-5.0, z=2.0, c_prime=10.0, phi_prime=25.0, m=0.0, q=0.0, gamma_sat=19.0, gamma_w=9.81)
        # Negative cohesion
        with self.assertRaises(ValueError):
            calculate_fos(beta=20.0, z=2.0, c_prime=-1.0, phi_prime=25.0, m=0.0, q=0.0, gamma_sat=19.0, gamma_w=9.81)
        # Non-positive soil unit weight
        with self.assertRaises(ValueError):
            calculate_fos(beta=20.0, z=2.0, c_prime=10.0, phi_prime=25.0, m=0.0, q=0.0, gamma_sat=0.0, gamma_w=9.81)
        # Non-positive water unit weight
        with self.assertRaises(ValueError):
            calculate_fos(beta=20.0, z=2.0, c_prime=10.0, phi_prime=25.0, m=0.0, q=0.0, gamma_sat=19.0, gamma_w=0.0)

    # ==========================================================================
    # 2. BLSR Tests
    # ==========================================================================

    def test_blsr_heterogeneous_buildings_calculation(self):
        """
        Validate BLSR calculation across heterogeneous building structures:
        BLSR = SUM(footprint_area_i * storeys_i * construction_type_weight_i)
               / (safe_bearing_capacity * habitable_land_area)

        Hand-calculated values:
        - Building 1: 120.0 m^2 * 3.0 storeys * 1.5 weight = 540.0
        - Building 2: 80.0 m^2 * 1.0 storeys * 0.8 weight = 64.0
        - Building 3: 200.0 m^2 * 2.0 storeys * 1.0 weight = 400.0
        - Numerator sum = 540.0 + 64.0 + 400.0 = 1004.0
        - safe_soil_bearing_capacity = 150.0 kPa
        - habitable_land_area = 2000.0 m^2
        - Denominator = 150.0 * 2000.0 = 300000.0
        - Expected BLSR = 1004.0 / 300000.0 = 0.003346666666666667
        """
        buildings = [
            {"footprint_area": 120.0, "storeys": 3.0, "construction_type_weight": 1.5},
            {"footprint_area": 80.0, "storeys": 1.0, "construction_type_weight": 0.8},
            {"footprint_area": 200.0, "storeys": 2.0, "construction_type_weight": 1.0},
        ]
        blsr = calculate_blsr(
            buildings=buildings,
            safe_soil_bearing_capacity=150.0,
            habitable_land_area=2000.0,
        )
        self.assertAlmostEqual(blsr, 0.003346666666666667, places=8)

    def test_blsr_empty_buildings_list(self):
        """
        IMPLEMENTATION CONVENTION - NOT SPECIFIED IN PROJECT DOCUMENTS:
        An empty building list represents zero structural load (numerator = 0.0), returning 0.0.
        """
        blsr = calculate_blsr(
            buildings=[],
            safe_soil_bearing_capacity=150.0,
            habitable_land_area=1000.0,
        )
        self.assertEqual(blsr, 0.0)

    def test_blsr_invalid_building_records(self):
        """
        Validate rejection of invalid building list elements and records.
        """
        # Non-dictionary item in list
        with self.assertRaises(TypeError):
            calculate_blsr(buildings=[100.0], safe_soil_bearing_capacity=150.0, habitable_land_area=1000.0)

        # Missing required key
        with self.assertRaises(ValueError):
            calculate_blsr(
                buildings=[{"footprint_area": 100.0, "storeys": 2.0}],
                safe_soil_bearing_capacity=150.0,
                habitable_land_area=1000.0,
            )

        # Non-numeric field value
        with self.assertRaises(TypeError):
            calculate_blsr(
                buildings=[{"footprint_area": "100", "storeys": 2.0, "construction_type_weight": 1.0}],
                safe_soil_bearing_capacity=150.0,
                habitable_land_area=1000.0,
            )

        # Negative footprint area
        with self.assertRaises(ValueError):
            calculate_blsr(
                buildings=[{"footprint_area": -50.0, "storeys": 1.0, "construction_type_weight": 1.0}],
                safe_soil_bearing_capacity=150.0,
                habitable_land_area=1000.0,
            )

    def test_blsr_invalid_zone_parameters(self):
        """
        Validate rejection of non-positive soil bearing capacity or habitable area.
        """
        buildings = [{"footprint_area": 100.0, "storeys": 1.0, "construction_type_weight": 1.0}]
        # Zero or negative bearing capacity
        with self.assertRaises(ValueError):
            calculate_blsr(buildings=buildings, safe_soil_bearing_capacity=0.0, habitable_land_area=1000.0)
        with self.assertRaises(ValueError):
            calculate_blsr(buildings=buildings, safe_soil_bearing_capacity=-100.0, habitable_land_area=1000.0)

        # Zero or negative habitable area
        with self.assertRaises(ValueError):
            calculate_blsr(buildings=buildings, safe_soil_bearing_capacity=150.0, habitable_land_area=0.0)
        with self.assertRaises(ValueError):
            calculate_blsr(buildings=buildings, safe_soil_bearing_capacity=150.0, habitable_land_area=-500.0)


if __name__ == "__main__":
    unittest.main()
