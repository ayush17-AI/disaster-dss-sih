import math
import unittest
from backend.geo_engine.formulas import calculate_rts


class TestStage2CRTSFormulas(unittest.TestCase):
    """
    Stage 2C Test Suite: Relocation Triage Score (RTS)
    Source of truth: Final Team Integration Specification.
    Formula: RTS = 0.35*tti_score + 0.25*svi + 0.20*struct_load + 0.20*demo_exposure
    """

    def test_rts_normal_hand_calculated_case(self):
        """
        Validate RTS calculation on a standard test point:
        tti_hours = 6.0 -> tti_score = min(1.0, 12.0 / 6.0) = 1.0
        svi = 0.8
        blsr = 1.0 -> struct_load = min(1.0, 1.0 / 2.0) = 0.5
        demo_exposure = 0.7
        Expected RTS = 0.35*1.0 + 0.25*0.8 + 0.20*0.5 + 0.20*0.7
                     = 0.35 + 0.20 + 0.10 + 0.14 = 0.79
        """
        rts = calculate_rts(
            tti_hours=6.0,
            svi=0.8,
            blsr=1.0,
            demo_exposure=0.7,
        )
        self.assertAlmostEqual(rts, 0.79, places=6)

    def test_rts_tti_below_or_equal_to_one_hour_max_score(self):
        """
        TTI <= 1.0 hour yields tti_score = 1.0.
        """
        rts_05 = calculate_rts(tti_hours=0.5, svi=0.0, blsr=0.0, demo_exposure=0.0)
        rts_10 = calculate_rts(tti_hours=1.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        self.assertAlmostEqual(rts_05, 0.35, places=6)
        self.assertAlmostEqual(rts_10, 0.35, places=6)

    def test_rts_tti_at_twelve_hours_produces_max_score(self):
        """
        TTI = 12.0 hours yields min(1.0, 12.0 / 12.0) = 1.0.
        """
        rts_12 = calculate_rts(tti_hours=12.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        self.assertAlmostEqual(rts_12, 0.35, places=6)

    def test_rts_tti_above_twelve_hours_decreases_urgency(self):
        """
        TTI > 12.0 hours yields 12.0 / tti_hours < 1.0.
        - tti = 24.0 -> tti_score = 12.0 / 24.0 = 0.5 -> contribution = 0.35 * 0.5 = 0.175
        - tti = 48.0 -> tti_score = 12.0 / 48.0 = 0.25 -> contribution = 0.35 * 0.25 = 0.0875
        """
        rts_24 = calculate_rts(tti_hours=24.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        rts_48 = calculate_rts(tti_hours=48.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        self.assertAlmostEqual(rts_24, 0.175, places=6)
        self.assertAlmostEqual(rts_48, 0.0875, places=6)

    def test_rts_independent_tti_weighting(self):
        """
        Validate TTI weight alpha = 0.35.
        """
        rts = calculate_rts(tti_hours=1.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        self.assertAlmostEqual(rts, 0.35, places=6)

    def test_rts_independent_svi_weighting(self):
        """
        Validate SVI weight beta = 0.25.
        """
        baseline = calculate_rts(tti_hours=12.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        with_svi = calculate_rts(tti_hours=12.0, svi=1.0, blsr=0.0, demo_exposure=0.0)
        self.assertAlmostEqual(with_svi - baseline, 0.25, places=6)

    def test_rts_independent_structural_load_weighting(self):
        """
        Validate structural load weight gamma = 0.20.
        """
        baseline = calculate_rts(tti_hours=12.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        with_struct = calculate_rts(tti_hours=12.0, svi=0.0, blsr=2.0, demo_exposure=0.0)
        self.assertAlmostEqual(with_struct - baseline, 0.20, places=6)

    def test_rts_independent_demographic_exposure_weighting(self):
        """
        Validate demographic exposure weight delta = 0.20.
        """
        baseline = calculate_rts(tti_hours=12.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        with_demo = calculate_rts(tti_hours=12.0, svi=0.0, blsr=0.0, demo_exposure=1.0)
        self.assertAlmostEqual(with_demo - baseline, 0.20, places=6)

    def test_rts_blsr_normalization_and_saturation(self):
        """
        Validate struct_load = min(1.0, blsr / 2.0).
        - blsr = 1.0 -> struct_load = 0.5 -> 0.20 * 0.5 = 0.10
        - blsr = 2.0 and 5.0 -> struct_load = 1.0 -> 0.20 * 1.0 = 0.20
        """
        baseline = calculate_rts(tti_hours=12.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        rts_mid = calculate_rts(tti_hours=12.0, svi=0.0, blsr=1.0, demo_exposure=0.0)
        rts_sat1 = calculate_rts(tti_hours=12.0, svi=0.0, blsr=2.0, demo_exposure=0.0)
        rts_sat2 = calculate_rts(tti_hours=12.0, svi=0.0, blsr=5.0, demo_exposure=0.0)
        self.assertAlmostEqual(rts_mid - baseline, 0.10, places=6)
        self.assertAlmostEqual(rts_sat1 - baseline, 0.20, places=6)
        self.assertAlmostEqual(rts_sat2 - baseline, 0.20, places=6)

    def test_rts_all_zero_non_tti_components(self):
        """
        When svi=0, blsr=0, demo=0, RTS equals alpha * tti_score.
        """
        rts = calculate_rts(tti_hours=12.0, svi=0.0, blsr=0.0, demo_exposure=0.0)
        self.assertAlmostEqual(rts, 0.35, places=6)

    def test_rts_all_maximum_components_gives_one(self):
        """
        When all components are at maximum:
        tti <= 12 -> 0.35
        svi = 1.0 -> 0.25
        blsr >= 2.0 -> 0.20
        demo = 1.0 -> 0.20
        Total RTS = 1.0
        """
        rts_max = calculate_rts(tti_hours=1.0, svi=1.0, blsr=2.0, demo_exposure=1.0)
        self.assertAlmostEqual(rts_max, 1.0, places=6)

    def test_rts_invalid_tti_rejected(self):
        """
        tti_hours must be strictly positive (> 0.0).
        """
        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=0.0, svi=0.5, blsr=1.0, demo_exposure=0.5)

        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=-2.0, svi=0.5, blsr=1.0, demo_exposure=0.5)

    def test_rts_invalid_svi_rejected(self):
        """
        svi must be in range [0.0, 1.0].
        """
        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=5.0, svi=-0.1, blsr=1.0, demo_exposure=0.5)

        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=5.0, svi=1.05, blsr=1.0, demo_exposure=0.5)

    def test_rts_negative_blsr_rejected(self):
        """
        blsr must be non-negative (>= 0.0).
        """
        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=5.0, svi=0.5, blsr=-1.0, demo_exposure=0.5)

    def test_rts_invalid_demo_exposure_rejected(self):
        """
        demo_exposure must be in range [0.0, 1.0].
        """
        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=5.0, svi=0.5, blsr=1.0, demo_exposure=-0.01)

        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=5.0, svi=0.5, blsr=1.0, demo_exposure=1.5)

    def test_rts_non_finite_inputs_rejected(self):
        """
        All inputs must be finite numbers.
        """
        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=float("nan"), svi=0.5, blsr=1.0, demo_exposure=0.5)

        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=5.0, svi=float("inf"), blsr=1.0, demo_exposure=0.5)

        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=5.0, svi=0.5, blsr=float("-inf"), demo_exposure=0.5)

        with self.assertRaises(TypeError):
            calculate_rts(tti_hours="5.0", svi=0.5, blsr=1.0, demo_exposure=0.5)


if __name__ == "__main__":
    unittest.main()
