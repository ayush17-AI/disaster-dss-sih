import math
import unittest
from backend.geo_engine.formulas import calculate_ccsi


class TestStage3CCSIFormulas(unittest.TestCase):
    """
    Stage 2B Test Suite: Carrying Capacity Susceptibility Index (CCSI)
    Source of truth: Final Team Integration Specification.
    Formula: CCSI = (w1*norm_inv_fos + w2*norm_blsr + w3*dci + w4*norm_def) * 100.0
    """

    def test_ccsi_mountain_mode_hand_calculation(self):
        """
        Validate CCSI calculation in mountain mode:
        Inputs: fos=0.8, blsr=1.0, dci=0.6, def=40.0, terrain_mode='mountain'
        - norm_inv_fos = (2.0 - 0.8) / 1.5 = 1.2 / 1.5 = 0.8
        - norm_blsr = min(1.0, 1.0 / 2.0) = 0.5
        - dci = 0.6
        - norm_def = min(1.0, 40.0 / 100.0) = 0.4
        - Mountain weights: w1=0.40, w2=0.30, w3=0.15, w4=0.15
        - ccsi_norm = 0.40*0.8 + 0.30*0.5 + 0.15*0.6 + 0.15*0.4 = 0.32 + 0.15 + 0.09 + 0.06 = 0.62
        - Expected CCSI = 0.62 * 100.0 = 62.0
        """
        ccsi = calculate_ccsi(
            fos=0.8,
            blsr=1.0,
            drainage_congestion_index=0.6,
            deformation_rate_mm_yr=40.0,
            terrain_mode="mountain",
        )
        self.assertAlmostEqual(ccsi, 62.0, places=6)

    def test_ccsi_plains_mode_hand_calculation(self):
        """
        Validate CCSI calculation in plains mode:
        Inputs: fos=0.8, blsr=1.0, dci=0.6, def=40.0, terrain_mode='plains'
        - Plains weights: w1=0.10, w2=0.25, w3=0.50, w4=0.15
        - ccsi_norm = 0.10*0.8 + 0.25*0.5 + 0.50*0.6 + 0.15*0.4 = 0.08 + 0.125 + 0.30 + 0.06 = 0.565
        - Expected CCSI = 0.565 * 100.0 = 56.5
        """
        ccsi = calculate_ccsi(
            fos=0.8,
            blsr=1.0,
            drainage_congestion_index=0.6,
            deformation_rate_mm_yr=40.0,
            terrain_mode="plains",
        )
        self.assertAlmostEqual(ccsi, 56.5, places=6)

    def test_ccsi_verify_mountain_weights_independently(self):
        """
        Verify each mountain weight independently: w1=0.40, w2=0.30, w3=0.15, w4=0.15
        """
        # w1 (FOS risk = 1.0, others = 0)
        c1 = calculate_ccsi(fos=0.5, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        self.assertAlmostEqual(c1, 40.0, places=6)

        # w2 (BLSR = 2.0 -> norm=1.0, others = 0)
        c2 = calculate_ccsi(fos=2.0, blsr=2.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        self.assertAlmostEqual(c2, 30.0, places=6)

        # w3 (DCI = 1.0, others = 0)
        c3 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=1.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        self.assertAlmostEqual(c3, 15.0, places=6)

        # w4 (Def = 100.0 -> norm=1.0, others = 0)
        c4 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=100.0, terrain_mode="mountain")
        self.assertAlmostEqual(c4, 15.0, places=6)

    def test_ccsi_verify_plains_weights_independently(self):
        """
        Verify each plains weight independently: w1=0.10, w2=0.25, w3=0.50, w4=0.15
        """
        # w1 (FOS risk = 1.0)
        c1 = calculate_ccsi(fos=0.5, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="plains")
        self.assertAlmostEqual(c1, 10.0, places=6)

        # w2 (BLSR = 2.0)
        c2 = calculate_ccsi(fos=2.0, blsr=2.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="plains")
        self.assertAlmostEqual(c2, 25.0, places=6)

        # w3 (DCI = 1.0)
        c3 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=1.0, deformation_rate_mm_yr=0.0, terrain_mode="plains")
        self.assertAlmostEqual(c3, 50.0, places=6)

        # w4 (Def = 100.0)
        c4 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=100.0, terrain_mode="plains")
        self.assertAlmostEqual(c4, 15.0, places=6)

    def test_ccsi_fos_below_or_equal_to_half_saturates_at_max_risk(self):
        """
        FOS <= 0.5 must produce maximum normalized FOS risk (1.0).
        """
        c_at_05 = calculate_ccsi(fos=0.5, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        c_at_02 = calculate_ccsi(fos=0.2, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        self.assertAlmostEqual(c_at_05, 40.0, places=6)
        self.assertAlmostEqual(c_at_02, 40.0, places=6)

    def test_ccsi_fos_above_or_equal_to_two_gives_zero_risk(self):
        """
        FOS >= 2.0 must produce zero normalized FOS risk (0.0).
        """
        c_at_20 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        c_at_35 = calculate_ccsi(fos=3.5, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        self.assertAlmostEqual(c_at_20, 0.0, places=6)
        self.assertAlmostEqual(c_at_35, 0.0, places=6)

    def test_ccsi_fos_linear_interpolation(self):
        """
        FOS = 1.25 -> (2.0 - 1.25) / 1.5 = 0.75 / 1.5 = 0.5.
        Expected mountain output = 0.40 * 0.5 * 100.0 = 20.0
        """
        c_mid = calculate_ccsi(fos=1.25, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        self.assertAlmostEqual(c_mid, 20.0, places=6)

    def test_ccsi_blsr_normalization_and_saturation(self):
        """
        BLSR = 1.0 -> norm = 0.5 (15.0 in mountain).
        BLSR = 2.0 and BLSR = 4.0 both saturate at norm = 1.0 (30.0 in mountain).
        """
        c_mid = calculate_ccsi(fos=2.0, blsr=1.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        c_sat1 = calculate_ccsi(fos=2.0, blsr=2.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        c_sat2 = calculate_ccsi(fos=2.0, blsr=4.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        self.assertAlmostEqual(c_mid, 15.0, places=6)
        self.assertAlmostEqual(c_sat1, 30.0, places=6)
        self.assertAlmostEqual(c_sat2, 30.0, places=6)

    def test_ccsi_deformation_symmetry_for_positive_and_negative(self):
        """
        norm_def uses abs(deformation_rate_mm_yr). +50.0 and -50.0 must yield identical CCSI.
        """
        c_pos = calculate_ccsi(fos=1.0, blsr=0.5, drainage_congestion_index=0.3, deformation_rate_mm_yr=50.0, terrain_mode="mountain")
        c_neg = calculate_ccsi(fos=1.0, blsr=0.5, drainage_congestion_index=0.3, deformation_rate_mm_yr=-50.0, terrain_mode="mountain")
        self.assertAlmostEqual(c_pos, c_neg, places=6)

    def test_ccsi_deformation_saturation_at_100(self):
        """
        Deformation >= 100.0 mm/yr saturates at norm = 1.0 (15.0 in mountain/plains).
        """
        c_100 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=100.0, terrain_mode="mountain")
        c_250 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=250.0, terrain_mode="mountain")
        c_neg_200 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=-200.0, terrain_mode="mountain")
        self.assertAlmostEqual(c_100, 15.0, places=6)
        self.assertAlmostEqual(c_250, 15.0, places=6)
        self.assertAlmostEqual(c_neg_200, 15.0, places=6)

    def test_ccsi_dci_boundary_values(self):
        """
        DCI = 0.0 gives zero contribution; DCI = 1.0 gives full w3 contribution.
        """
        c_dci0 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="plains")
        c_dci1 = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=1.0, deformation_rate_mm_yr=0.0, terrain_mode="plains")
        self.assertAlmostEqual(c_dci0, 0.0, places=6)
        self.assertAlmostEqual(c_dci1, 50.0, places=6)

    def test_ccsi_output_remains_within_0_to_100(self):
        """
        Minimum possible CCSI is 0.0; Maximum possible CCSI is 100.0.
        """
        c_min = calculate_ccsi(fos=2.0, blsr=0.0, drainage_congestion_index=0.0, deformation_rate_mm_yr=0.0, terrain_mode="mountain")
        c_max = calculate_ccsi(fos=0.5, blsr=2.0, drainage_congestion_index=1.0, deformation_rate_mm_yr=100.0, terrain_mode="mountain")
        self.assertAlmostEqual(c_min, 0.0, places=6)
        self.assertAlmostEqual(c_max, 100.0, places=6)

    def test_ccsi_invalid_terrain_mode_rejected(self):
        """
        terrain_mode must be exactly 'mountain' or 'plains'.
        """
        with self.assertRaises(ValueError):
            calculate_ccsi(fos=1.0, blsr=0.5, drainage_congestion_index=0.2, deformation_rate_mm_yr=10.0, terrain_mode="transitional")

        with self.assertRaises(ValueError):
            calculate_ccsi(fos=1.0, blsr=0.5, drainage_congestion_index=0.2, deformation_rate_mm_yr=10.0, terrain_mode="MOUNTAIN")

        with self.assertRaises(ValueError):
            calculate_ccsi(fos=1.0, blsr=0.5, drainage_congestion_index=0.2, deformation_rate_mm_yr=10.0, terrain_mode="")

    def test_ccsi_invalid_dci_rejected(self):
        """
        drainage_congestion_index must be in [0.0, 1.0].
        """
        with self.assertRaises(ValueError):
            calculate_ccsi(fos=1.0, blsr=0.5, drainage_congestion_index=-0.1, deformation_rate_mm_yr=10.0, terrain_mode="mountain")

        with self.assertRaises(ValueError):
            calculate_ccsi(fos=1.0, blsr=0.5, drainage_congestion_index=1.01, deformation_rate_mm_yr=10.0, terrain_mode="mountain")

    def test_ccsi_negative_blsr_rejected(self):
        """
        blsr must be >= 0.0.
        """
        with self.assertRaises(ValueError):
            calculate_ccsi(fos=1.0, blsr=-0.5, drainage_congestion_index=0.2, deformation_rate_mm_yr=10.0, terrain_mode="mountain")

    def test_ccsi_non_positive_fos_rejected(self):
        """
        fos must be strictly positive (> 0.0).
        """
        with self.assertRaises(ValueError):
            calculate_ccsi(fos=0.0, blsr=0.5, drainage_congestion_index=0.2, deformation_rate_mm_yr=10.0, terrain_mode="mountain")

        with self.assertRaises(ValueError):
            calculate_ccsi(fos=-1.0, blsr=0.5, drainage_congestion_index=0.2, deformation_rate_mm_yr=10.0, terrain_mode="mountain")

    def test_ccsi_non_finite_inputs_rejected(self):
        """
        All numeric inputs must be finite.
        """
        with self.assertRaises(ValueError):
            calculate_ccsi(fos=float("nan"), blsr=0.5, drainage_congestion_index=0.2, deformation_rate_mm_yr=10.0, terrain_mode="mountain")

        with self.assertRaises(ValueError):
            calculate_ccsi(fos=1.0, blsr=float("inf"), drainage_congestion_index=0.2, deformation_rate_mm_yr=10.0, terrain_mode="mountain")

        with self.assertRaises(ValueError):
            calculate_ccsi(fos=1.0, blsr=0.5, drainage_congestion_index=0.2, deformation_rate_mm_yr=float("-inf"), terrain_mode="mountain")


if __name__ == "__main__":
    unittest.main()
