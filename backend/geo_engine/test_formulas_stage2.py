import math
import unittest
from backend.geo_engine.formulas import calculate_confidence


class TestStage2Formulas(unittest.TestCase):
    """
    Stage 2A Test Suite: Confidence Score
    Scientific source of truth: Team_Blueprint_Deep_Summary.pdf and SIH_Red_Zone_CCSI_Research_Dossier.md.
    Formula: Confidence = 0.40 * S_res + 0.35 * S_source + 0.25 * S_prox
    """

    def test_confidence_hand_calculated_normal_case(self):
        """
        Validate exact linear arithmetic on a standard test point:
        s_res = 85.0, s_source = 90.0, s_prox = 70.0
        Expected = 0.40*85.0 + 0.35*90.0 + 0.25*70.0 = 34.0 + 31.5 + 17.5 = 83.0
        """
        conf = calculate_confidence(s_res=85.0, s_source=90.0, s_prox=70.0)
        self.assertAlmostEqual(conf, 83.0, places=6)

    def test_confidence_all_zeros(self):
        """
        Validate zero inputs evaluate to zero.
        """
        conf = calculate_confidence(s_res=0.0, s_source=0.0, s_prox=0.0)
        self.assertEqual(conf, 0.0)

    def test_confidence_individual_weight_isolation(self):
        """
        Validate each weight coefficient individually:
        - s_res coefficient = 0.40
        - s_source coefficient = 0.35
        - s_prox coefficient = 0.25
        """
        # Test s_res alone
        conf_res = calculate_confidence(s_res=100.0, s_source=0.0, s_prox=0.0)
        self.assertAlmostEqual(conf_res, 40.0, places=6)

        # Test s_source alone
        conf_source = calculate_confidence(s_res=0.0, s_source=100.0, s_prox=0.0)
        self.assertAlmostEqual(conf_source, 35.0, places=6)

        # Test s_prox alone
        conf_prox = calculate_confidence(s_res=0.0, s_source=0.0, s_prox=100.0)
        self.assertAlmostEqual(conf_prox, 25.0, places=6)

    def test_confidence_fractional_float_inputs(self):
        """
        Validate decimal fractional inputs without rounding or conversion errors:
        s_res = 0.85, s_source = 0.92, s_prox = 0.74
        Expected = 0.40*0.85 + 0.35*0.92 + 0.25*0.74 = 0.340 + 0.322 + 0.185 = 0.847
        """
        conf = calculate_confidence(s_res=0.85, s_source=0.92, s_prox=0.74)
        self.assertAlmostEqual(conf, 0.847, places=6)

    def test_confidence_preserves_finite_values_outside_0_to_100(self):
        """
        Validate that inputs/outputs are not clamped to 0-100 since range and scaling
        are NOT specified in project documents.
        """
        # Values > 100
        conf_large = calculate_confidence(s_res=150.0, s_source=200.0, s_prox=120.0)
        # Expected = 0.40*150.0 + 0.35*200.0 + 0.25*120.0 = 60.0 + 70.0 + 30.0 = 160.0
        self.assertAlmostEqual(conf_large, 160.0, places=6)

        # Negative finite values
        conf_neg = calculate_confidence(s_res=-10.0, s_source=-20.0, s_prox=-30.0)
        # Expected = 0.40*(-10.0) + 0.35*(-20.0) + 0.25*(-30.0) = -4.0 - 7.0 - 7.5 = -18.5
        self.assertAlmostEqual(conf_neg, -18.5, places=6)

    def test_confidence_invalid_non_finite_and_type_handling(self):
        """
        Validate rejection of non-finite floats (NaN, Inf) and non-numeric types.
        """
        # NaN handling
        with self.assertRaises(ValueError):
            calculate_confidence(s_res=float("nan"), s_source=80.0, s_prox=70.0)

        # Infinity handling
        with self.assertRaises(ValueError):
            calculate_confidence(s_res=80.0, s_source=float("inf"), s_prox=70.0)

        with self.assertRaises(ValueError):
            calculate_confidence(s_res=80.0, s_source=70.0, s_prox=float("-inf"))

        # Non-numeric type
        with self.assertRaises(TypeError):
            calculate_confidence(s_res="80.0", s_source=80.0, s_prox=70.0)


if __name__ == "__main__":
    unittest.main()
