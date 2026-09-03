import math
import unittest
from backend.geo_engine.formulas import (
    calculate_blsr,
    calculate_ccsi,
    calculate_confidence,
    calculate_fos,
    calculate_rts,
)
from backend.geo_engine.hazard_classifier import (
    build_hazard_zone_feature,
    classify_hazard_color,
    generate_hazard_zones,
)
from backend.geo_engine.mode_switch import determine_terrain_mode


class TestGeoEngineIntegration(unittest.TestCase):
    """
    Stage 5 Integration & End-to-End Test Suite for Role A Geo-Engine Pipeline.
    Tests composition and data flows across all components without mock or external data.
    """

    # ==========================================================================
    # SCENARIO 1: MOUNTAIN HIGH-RISK END-TO-END
    # ==========================================================================

    def test_scenario_1_mountain_high_risk_pipeline(self):
        """
        Verify end-to-end flow for a high-risk mountain zone:
        - Mean slope > 15 deg -> mountain, non-transitional
        - Steep slope + high water table -> unstable FOS (< 1.0)
        - Heavy structural load -> BLSR >= 1.0
        - High CCSI (> 70.0)
        - Urgent TTI (<= 12h) -> high RTS (>= 0.70)
        - Resulting color: 'red'
        """
        mean_slope = 30.0
        mode, is_trans = determine_terrain_mode(mean_slope)
        self.assertEqual(mode, "mountain")
        self.assertFalse(is_trans)

        # Calculate FOS with steep slope and high pore water pressure
        fos = calculate_fos(
            beta=35.0,
            z=3.0,
            c_prime=5.0,
            phi_prime=20.0,
            m=0.8,
            q=15.0,
            gamma_sat=19.0,
            gamma_w=9.81,
        )
        self.assertLess(fos, 1.0)  # Unstable slope

        # Calculate BLSR
        buildings = [
            {"footprint_area": 200.0, "storeys": 3.0, "construction_type_weight": 1.2}
        ]
        blsr = calculate_blsr(
            buildings=buildings,
            safe_soil_bearing_capacity=150.0,
            habitable_land_area=4.0,
        )
        # Expected: (200 * 3 * 1.2) / (150 * 4) = 720 / 600 = 1.2
        self.assertAlmostEqual(blsr, 1.2, places=6)

        # Calculate CCSI with mountain weights
        ccsi = calculate_ccsi(
            fos=fos,
            blsr=blsr,
            drainage_congestion_index=0.4,
            deformation_rate_mm_yr=50.0,
            terrain_mode=mode,
        )
        # FOS < 0.5 -> norm_fos = 1.0; norm_blsr = 0.6; dci = 0.4; norm_def = 0.5
        # ccsi_norm = 0.40(1.0) + 0.30(0.6) + 0.15(0.4) + 0.15(0.5) = 0.40 + 0.18 + 0.06 + 0.075 = 0.715
        # Expected CCSI = 71.5
        self.assertGreater(ccsi, 70.0)

        # Calculate RTS
        rts = calculate_rts(
            tti_hours=4.0,
            svi=0.8,
            blsr=blsr,
            demo_exposure=0.9,
        )
        # tti_score = 1.0; svi = 0.8; struct_load = 0.6; demo = 0.9
        # rts = 0.35(1) + 0.25(0.8) + 0.20(0.6) + 0.20(0.9) = 0.35 + 0.20 + 0.12 + 0.18 = 0.85
        self.assertAlmostEqual(rts, 0.85, places=6)
        self.assertGreaterEqual(rts, 0.70)

        # Calculate Confidence
        conf = calculate_confidence(s_res=85.0, s_source=90.0, s_prox=80.0)
        self.assertAlmostEqual(conf, 85.5, places=6)

        # Classify color
        color = classify_hazard_color(fos=fos, blsr=blsr, ccsi=ccsi, rts=rts)
        self.assertEqual(color, "red")

        # Build feature
        poly_geom = {
            "type": "Polygon",
            "coordinates": [[[76.1, 11.5], [76.2, 11.5], [76.2, 11.6], [76.1, 11.6], [76.1, 11.5]]],
        }
        feature = build_hazard_zone_feature(
            zone_id="ZONE_MTN_RED",
            geometry=poly_geom,
            fos=fos,
            blsr=blsr,
            ccsi=ccsi,
            rts=rts,
            confidence_score=conf,
            zone_color=color,
            terrain_mode=mode,
            is_transitional=is_trans,
        )

        self.assertEqual(feature["type"], "Feature")
        props = feature["properties"]
        self.assertEqual(props["zone_id"], "ZONE_MTN_RED")
        self.assertEqual(props["zone_color"], "red")
        self.assertEqual(props["terrain_mode"], "mountain")
        self.assertIs(props["is_transitional"], False)
        self.assertNotIn("rts", props)

    # ==========================================================================
    # SCENARIO 2: PLAINS END-TO-END
    # ==========================================================================

    def test_scenario_2_plains_inundation_pipeline(self):
        """
        Verify end-to-end flow for a plains inundation zone:
        - Mean slope < 5 deg -> plains, non-transitional
        - High FOS (stable slope)
        - Moderate BLSR
        - High Drainage Congestion Index (DCI = 0.80)
        - Plains CCSI heavily weights DCI (w3 = 0.50)
        """
        mean_slope = 2.5
        mode, is_trans = determine_terrain_mode(mean_slope)
        self.assertEqual(mode, "plains")
        self.assertFalse(is_trans)

        # Stable flat slope FOS
        fos = calculate_fos(
            beta=3.0,
            z=2.0,
            c_prime=10.0,
            phi_prime=25.0,
            m=0.0,
            q=0.0,
            gamma_sat=18.0,
            gamma_w=9.81,
        )
        self.assertGreater(fos, 2.0)  # Safe from slope failure

        # BLSR
        buildings = [
            {"footprint_area": 100.0, "storeys": 2.0, "construction_type_weight": 1.0}
        ]
        blsr = calculate_blsr(
            buildings=buildings,
            safe_soil_bearing_capacity=200.0,
            habitable_land_area=2.5,
        )
        # Expected: 200 / 500 = 0.4
        self.assertAlmostEqual(blsr, 0.4, places=6)

        # CCSI with plains weights
        ccsi = calculate_ccsi(
            fos=fos,
            blsr=blsr,
            drainage_congestion_index=0.8,
            deformation_rate_mm_yr=10.0,
            terrain_mode=mode,
        )
        # FOS >= 2.0 -> norm_inv_fos = 0.0; norm_blsr = 0.2; dci = 0.8; norm_def = 0.1
        # ccsi_norm = 0.10(0) + 0.25(0.2) + 0.50(0.8) + 0.15(0.1) = 0 + 0.05 + 0.40 + 0.015 = 0.465
        # Expected CCSI = 46.5
        self.assertAlmostEqual(ccsi, 46.5, places=6)

        # RTS
        rts = calculate_rts(
            tti_hours=24.0,
            svi=0.4,
            blsr=blsr,
            demo_exposure=0.3,
        )
        # tti_score = 0.5; svi = 0.4; struct_load = 0.2; demo = 0.3
        # rts = 0.35(0.5) + 0.25(0.4) + 0.20(0.2) + 0.20(0.3) = 0.175 + 0.10 + 0.04 + 0.06 = 0.375
        self.assertAlmostEqual(rts, 0.375, places=6)

        conf = calculate_confidence(s_res=70.0, s_source=75.0, s_prox=80.0)
        color = classify_hazard_color(fos=fos, blsr=blsr, ccsi=ccsi, rts=rts)
        # 40 <= CCSI <= 70 -> yellow
        self.assertEqual(color, "yellow")

        # GeoJSON Generation
        record = {
            "zone_id": "ZONE_PLN_01",
            "geometry": {"type": "Point", "coordinates": [75.5, 12.1]},
            "fos": fos,
            "blsr": blsr,
            "ccsi": ccsi,
            "rts": rts,
            "confidence_score": conf,
            "zone_color": color,
            "terrain_mode": mode,
            "is_transitional": is_trans,
        }
        fc = generate_hazard_zones([record])
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(len(fc["features"]), 1)
        self.assertEqual(fc["features"][0]["properties"]["terrain_mode"], "plains")

    # ==========================================================================
    # SCENARIO 3: TRANSITIONAL BOUNDARIES
    # ==========================================================================

    def test_scenario_3_transitional_boundary_transitions(self):
        """
        Verify exact transitional mode boundaries:
        - 4.999  -> ('plains', False)
        - 5.0    -> ('plains', True)
        - 9.999  -> ('plains', True)
        - 10.0   -> ('mountain', True)
        - 15.0   -> ('mountain', True)
        - 15.001 -> ('mountain', False)
        """
        cases = [
            (4.999, "plains", False),
            (5.0, "plains", True),
            (9.999, "plains", True),
            (10.0, "mountain", True),
            (15.0, "mountain", True),
            (15.001, "mountain", False),
        ]
        for slope, exp_mode, exp_trans in cases:
            with self.subTest(slope=slope):
                mode, is_trans = determine_terrain_mode(slope)
                self.assertEqual(mode, exp_mode)
                self.assertEqual(is_trans, exp_trans)

    # ==========================================================================
    # SCENARIO 4: RED FEATURE COLLECTION PIPELINE
    # ==========================================================================

    def test_scenario_4_red_feature_collection_generation(self):
        """
        Full composition test for a RED hazard zone resulting in a FeatureCollection.
        Verify:
        - FeatureCollection type
        - Feature type
        - Exact 8 keys in order
        - Absence of 'rts'
        - All numerics finite
        """
        zone_data = {
            "zone_id": "ZONE_RED_01",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.0, 11.0], [76.1, 11.0], [76.1, 11.1], [76.0, 11.1], [76.0, 11.0]]],
            },
            "fos": 0.65,
            "blsr": 1.5,
            "ccsi": 75.0,
            "rts": 0.82,
            "confidence_score": 90.0,
            "zone_color": "red",
            "terrain_mode": "mountain",
            "is_transitional": False,
        }

        fc = generate_hazard_zones([zone_data])
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(len(fc["features"]), 1)

        feat = fc["features"][0]
        self.assertEqual(feat["type"], "Feature")
        self.assertEqual(feat["geometry"], zone_data["geometry"])

        props = feat["properties"]
        expected_keys = [
            "zone_id",
            "fos",
            "blsr",
            "ccsi",
            "confidence_score",
            "zone_color",
            "terrain_mode",
            "is_transitional",
        ]
        self.assertEqual(list(props.keys()), expected_keys)
        self.assertNotIn("rts", props)
        self.assertEqual(props["zone_color"], "red")
        self.assertEqual(props["terrain_mode"], "mountain")
        self.assertFalse(props["is_transitional"])
        for k in ["fos", "blsr", "ccsi", "confidence_score"]:
            self.assertTrue(math.isfinite(props[k]))

    # ==========================================================================
    # SCENARIO 5: YELLOW END-TO-END
    # ==========================================================================

    def test_scenario_5_yellow_end_to_end(self):
        """
        Verify an end-to-end zone crossing ONLY yellow prototype criteria:
        - 1.0 <= FOS <= 1.5 (e.g. FOS = 1.25)
        - CCSI in safe yellow range (50.0)
        - RTS in moderate yellow range (0.50)
        - BLSR = 0.5
        - No red condition triggered
        """
        fos = 1.25
        blsr = 0.5
        ccsi = 50.0
        rts = 0.50
        color = classify_hazard_color(fos=fos, blsr=blsr, ccsi=ccsi, rts=rts)
        self.assertEqual(color, "yellow")

        record = {
            "zone_id": "ZONE_YEL_01",
            "geometry": {"type": "Point", "coordinates": [76.5, 11.8]},
            "fos": fos,
            "blsr": blsr,
            "ccsi": ccsi,
            "rts": rts,
            "confidence_score": 82.0,
            "terrain_mode": "mountain",
            "is_transitional": True,
        }
        fc = generate_hazard_zones([record])
        feat = fc["features"][0]
        self.assertEqual(feat["properties"]["zone_color"], "yellow")
        self.assertEqual(feat["properties"]["zone_id"], "ZONE_YEL_01")
        self.assertTrue(feat["properties"]["is_transitional"])

    # ==========================================================================
    # SCENARIO 6: GREEN END-TO-END
    # ==========================================================================

    def test_scenario_6_green_end_to_end(self):
        """
        Verify an end-to-end safe zone crossing neither red nor yellow:
        - FOS = 2.2 (> 1.5)
        - BLSR = 0.2 (< 1.0)
        - CCSI = 22.0 (< 40.0)
        - RTS = 0.20 (< 0.40)
        - Resulting color: 'green'
        """
        fos = 2.2
        blsr = 0.2
        ccsi = 22.0
        rts = 0.20
        color = classify_hazard_color(fos=fos, blsr=blsr, ccsi=ccsi, rts=rts)
        self.assertEqual(color, "green")

        record = {
            "zone_id": "ZONE_GRN_01",
            "geometry": {"type": "Point", "coordinates": [76.8, 11.2]},
            "fos": fos,
            "blsr": blsr,
            "ccsi": ccsi,
            "rts": rts,
            "confidence_score": 95.0,
            "terrain_mode": "plains",
            "is_transitional": False,
        }
        fc = generate_hazard_zones([record])
        feat = fc["features"][0]
        self.assertEqual(feat["properties"]["zone_color"], "green")
        self.assertEqual(feat["properties"]["zone_id"], "ZONE_GRN_01")
        self.assertFalse(feat["properties"]["is_transitional"])

    # ==========================================================================
    # SCENARIO 7: MULTI-ZONE BATCH
    # ==========================================================================

    def test_scenario_7_multi_zone_batch_heterogeneous(self):
        """
        Verify batch generation of 3 heterogeneous zones without state leakage:
        1. Zone 1: Mountain Red
        2. Zone 2: Plains Yellow (Transitional)
        3. Zone 3: Plains Green (Non-transitional)
        """
        records = [
            {
                "zone_id": "ZONE_MTN_RED",
                "geometry": {"type": "Point", "coordinates": [76.1, 11.5]},
                "fos": 0.75,
                "blsr": 1.6,
                "ccsi": 78.0,
                "rts": 0.85,
                "confidence_score": 88.0,
                "terrain_mode": "mountain",
                "is_transitional": False,
            },
            {
                "zone_id": "ZONE_PLN_YEL",
                "geometry": {"type": "Point", "coordinates": [76.2, 11.6]},
                "fos": 1.25,
                "blsr": 0.6,
                "ccsi": 48.0,
                "rts": 0.45,
                "confidence_score": 79.0,
                "terrain_mode": "plains",
                "is_transitional": True,
            },
            {
                "zone_id": "ZONE_PLN_GRN",
                "geometry": {"type": "Point", "coordinates": [76.3, 11.7]},
                "fos": 2.1,
                "blsr": 0.15,
                "ccsi": 18.0,
                "rts": 0.15,
                "confidence_score": 92.0,
                "terrain_mode": "plains",
                "is_transitional": False,
            },
        ]

        fc = generate_hazard_zones(records)
        self.assertEqual(len(fc["features"]), 3)

        f1, f2, f3 = fc["features"]

        # Feature 1
        self.assertEqual(f1["properties"]["zone_id"], "ZONE_MTN_RED")
        self.assertEqual(f1["properties"]["zone_color"], "red")
        self.assertEqual(f1["properties"]["terrain_mode"], "mountain")
        self.assertFalse(f1["properties"]["is_transitional"])
        self.assertEqual(f1["properties"]["fos"], 0.75)

        # Feature 2
        self.assertEqual(f2["properties"]["zone_id"], "ZONE_PLN_YEL")
        self.assertEqual(f2["properties"]["zone_color"], "yellow")
        self.assertEqual(f2["properties"]["terrain_mode"], "plains")
        self.assertTrue(f2["properties"]["is_transitional"])
        self.assertEqual(f2["properties"]["ccsi"], 48.0)

        # Feature 3
        self.assertEqual(f3["properties"]["zone_id"], "ZONE_PLN_GRN")
        self.assertEqual(f3["properties"]["zone_color"], "green")
        self.assertEqual(f3["properties"]["terrain_mode"], "plains")
        self.assertFalse(f3["properties"]["is_transitional"])
        self.assertEqual(f3["properties"]["confidence_score"], 92.0)

    # ==========================================================================
    # SCENARIO 8: INVALID PIPELINE INPUTS
    # ==========================================================================

    def test_scenario_8_pipeline_validation_rejections(self):
        """
        Verify rejection of malformed data across the pipeline boundaries.
        """
        # 1. Invalid FOS (non-positive)
        with self.assertRaises(ValueError):
            calculate_fos(
                beta=20.0, z=2.0, c_prime=10.0, phi_prime=20.0, m=0.0, q=0.0, gamma_sat=-19.0, gamma_w=9.81
            )

        # 2. Invalid BLSR bearing capacity (<= 0)
        with self.assertRaises(ValueError):
            calculate_blsr(
                buildings=[], safe_soil_bearing_capacity=0.0, habitable_land_area=10.0
            )

        # 3. Invalid DCI (> 1.0)
        with self.assertRaises(ValueError):
            calculate_ccsi(
                fos=1.5, blsr=0.5, drainage_congestion_index=1.2, deformation_rate_mm_yr=10.0, terrain_mode="mountain"
            )

        # 4. Invalid Deformation (non-finite)
        with self.assertRaises(ValueError):
            calculate_ccsi(
                fos=1.5, blsr=0.5, drainage_congestion_index=0.5, deformation_rate_mm_yr=float("nan"), terrain_mode="mountain"
            )

        # 5. Invalid RTS (TTI <= 0)
        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=0.0, svi=0.5, blsr=0.5, demo_exposure=0.5)

        # 6. Invalid RTS (SVI > 1.0)
        with self.assertRaises(ValueError):
            calculate_rts(tti_hours=12.0, svi=1.5, blsr=0.5, demo_exposure=0.5)

        # 7. Invalid Terrain Mode in determine_terrain_mode (negative slope)
        with self.assertRaises(ValueError):
            determine_terrain_mode(mean_slope=-5.0)

        # 8. Invalid Geometry in build_hazard_zone_feature
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_01",
                geometry={"type": "Polygon"},  # missing coordinates
                fos=1.5,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

        # 9. Empty Zone ID
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="",
                geometry={"type": "Point", "coordinates": [0, 0]},
                fos=1.5,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

        # 10. Negative Confidence Score
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_01",
                geometry={"type": "Point", "coordinates": [0, 0]},
                fos=1.5,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=-5.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

        # 11. Malformed record in generate_hazard_zones
        with self.assertRaises(ValueError):
            generate_hazard_zones([{"zone_id": "ZONE_01"}])  # missing keys


if __name__ == "__main__":
    unittest.main()
