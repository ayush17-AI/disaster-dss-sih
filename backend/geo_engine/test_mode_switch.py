import math
import unittest
from backend.geo_engine.mode_switch import determine_terrain_mode


class TestModeSwitch(unittest.TestCase):
    """
    Stage 3 Test Suite: Terrain Mode Switcher
    Source of truth: Final Team Integration Specification.
    Rules:
        mean_slope < 5.0 -> ("plains", False)
        mean_slope > 15.0 -> ("mountain", False)
        5.0 <= mean_slope <= 15.0:
            mean_slope < 10.0 -> ("plains", True)
            mean_slope >= 10.0 -> ("mountain", True)
    """

    def test_slope_below_5_returns_plains_non_transitional(self):
        mode, is_trans = determine_terrain_mode(mean_slope=3.5)
        self.assertEqual(mode, "plains")
        self.assertFalse(is_trans)

    def test_exact_5_returns_plains_transitional(self):
        mode, is_trans = determine_terrain_mode(mean_slope=5.0)
        self.assertEqual(mode, "plains")
        self.assertTrue(is_trans)

    def test_slope_just_above_5_returns_plains_transitional(self):
        mode, is_trans = determine_terrain_mode(mean_slope=5.0001)
        self.assertEqual(mode, "plains")
        self.assertTrue(is_trans)

    def test_slope_just_below_10_returns_plains_transitional(self):
        mode, is_trans = determine_terrain_mode(mean_slope=9.9999)
        self.assertEqual(mode, "plains")
        self.assertTrue(is_trans)

    def test_exact_10_returns_mountain_transitional(self):
        mode, is_trans = determine_terrain_mode(mean_slope=10.0)
        self.assertEqual(mode, "mountain")
        self.assertTrue(is_trans)

    def test_slope_between_10_and_15_returns_mountain_transitional(self):
        mode, is_trans = determine_terrain_mode(mean_slope=12.5)
        self.assertEqual(mode, "mountain")
        self.assertTrue(is_trans)

    def test_exact_15_returns_mountain_transitional(self):
        mode, is_trans = determine_terrain_mode(mean_slope=15.0)
        self.assertEqual(mode, "mountain")
        self.assertTrue(is_trans)

    def test_slope_above_15_returns_mountain_non_transitional(self):
        mode1, is_trans1 = determine_terrain_mode(mean_slope=15.0001)
        self.assertEqual(mode1, "mountain")
        self.assertFalse(is_trans1)

        mode2, is_trans2 = determine_terrain_mode(mean_slope=28.0)
        self.assertEqual(mode2, "mountain")
        self.assertFalse(is_trans2)

    def test_zero_slope_returns_plains_non_transitional(self):
        mode, is_trans = determine_terrain_mode(mean_slope=0.0)
        self.assertEqual(mode, "plains")
        self.assertFalse(is_trans)

    def test_negative_slope_rejected(self):
        with self.assertRaises(ValueError):
            determine_terrain_mode(mean_slope=-0.01)

        with self.assertRaises(ValueError):
            determine_terrain_mode(mean_slope=-10.0)

    def test_nan_slope_rejected(self):
        with self.assertRaises(ValueError):
            determine_terrain_mode(mean_slope=float("nan"))

    def test_positive_infinity_slope_rejected(self):
        with self.assertRaises(ValueError):
            determine_terrain_mode(mean_slope=float("inf"))

    def test_negative_infinity_slope_rejected(self):
        with self.assertRaises(ValueError):
            determine_terrain_mode(mean_slope=float("-inf"))

    def test_non_numeric_input_rejected(self):
        with self.assertRaises(TypeError):
            determine_terrain_mode(mean_slope="10.0")

        with self.assertRaises(TypeError):
            determine_terrain_mode(mean_slope=None)

        with self.assertRaises(TypeError):
            determine_terrain_mode(mean_slope=[10.0])


if __name__ == "__main__":
    unittest.main()
