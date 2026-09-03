import math
import unittest
from backend.geo_engine.hazard_classifier import (
    build_hazard_zone_feature,
    classify_hazard_color,
    generate_hazard_zones,
)


class TestHazardClassifier(unittest.TestCase):
    """
    Stage 4 Test Suite: Hazard Color Classifier and GeoJSON Zone Generator
    Source of truth: Stage 4 Specification in implementation_plan.md.
    """

    # ==========================================================================
    # PART A: classify_hazard_color Tests (Tests 1 - 23)
    # ==========================================================================

    def test_01_fos_red(self):
        # FOS < 1.0 -> 'red'
        color = classify_hazard_color(fos=0.8, blsr=0.5, ccsi=30.0, rts=0.2)
        self.assertEqual(color, "red")

    def test_02_fos_yellow(self):
        # 1.0 <= FOS <= 1.5 -> 'yellow'
        color = classify_hazard_color(fos=1.2, blsr=0.5, ccsi=30.0, rts=0.2)
        self.assertEqual(color, "yellow")

    def test_03_fos_green(self):
        # FOS > 1.5 with safe others -> 'green'
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=30.0, rts=0.2)
        self.assertEqual(color, "green")

    def test_04_ccsi_red(self):
        # CCSI > 70.0 -> 'red'
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=75.0, rts=0.2)
        self.assertEqual(color, "red")

    def test_05_rts_red(self):
        # RTS >= 0.70 -> 'red'
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=30.0, rts=0.75)
        self.assertEqual(color, "red")

    def test_06_blsr_yellow(self):
        # BLSR >= 1.0 -> 'yellow'
        color = classify_hazard_color(fos=1.8, blsr=1.2, ccsi=30.0, rts=0.2)
        self.assertEqual(color, "yellow")

    def test_07_ccsi_yellow(self):
        # 40.0 <= CCSI <= 70.0 -> 'yellow'
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=50.0, rts=0.2)
        self.assertEqual(color, "yellow")

    def test_08_rts_yellow(self):
        # 0.40 <= RTS < 0.70 -> 'yellow'
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=30.0, rts=0.55)
        self.assertEqual(color, "yellow")

    def test_09_green_when_no_thresholds_crossed(self):
        # Safe baseline
        color = classify_hazard_color(fos=2.0, blsr=0.2, ccsi=20.0, rts=0.1)
        self.assertEqual(color, "green")

    def test_10_red_precedence_over_yellow(self):
        # FOS < 1.0 (red) with BLSR >= 1.0 (yellow) and CCSI in 40-70 (yellow) -> 'red'
        color = classify_hazard_color(fos=0.8, blsr=1.5, ccsi=55.0, rts=0.5)
        self.assertEqual(color, "red")

    def test_11_boundary_fos_one(self):
        # Boundary FOS = 1.0 -> 'yellow'
        color = classify_hazard_color(fos=1.0, blsr=0.5, ccsi=30.0, rts=0.2)
        self.assertEqual(color, "yellow")

    def test_12_boundary_fos_one_point_five(self):
        # Boundary FOS = 1.5 -> 'yellow'
        color = classify_hazard_color(fos=1.5, blsr=0.5, ccsi=30.0, rts=0.2)
        self.assertEqual(color, "yellow")

    def test_13_boundary_ccsi_forty(self):
        # Boundary CCSI = 40.0 -> 'yellow'
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=40.0, rts=0.2)
        self.assertEqual(color, "yellow")

    def test_14_boundary_ccsi_seventy(self):
        # Boundary CCSI = 70.0 -> 'yellow' (70.0 is yellow, > 70.0 is red)
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=70.0, rts=0.2)
        self.assertEqual(color, "yellow")

    def test_15_boundary_rts_forty(self):
        # Boundary RTS = 0.40 -> 'yellow'
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=30.0, rts=0.40)
        self.assertEqual(color, "yellow")

    def test_16_boundary_rts_seventy(self):
        # Boundary RTS = 0.70 -> 'red' (RTS >= 0.70 is red)
        color = classify_hazard_color(fos=1.8, blsr=0.5, ccsi=30.0, rts=0.70)
        self.assertEqual(color, "red")

    def test_17_boundary_blsr_one(self):
        # Boundary BLSR = 1.0 -> 'yellow'
        color = classify_hazard_color(fos=1.8, blsr=1.0, ccsi=30.0, rts=0.2)
        self.assertEqual(color, "yellow")

    def test_18_invalid_fos(self):
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=0.0, blsr=0.5, ccsi=30.0, rts=0.2)
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=-1.0, blsr=0.5, ccsi=30.0, rts=0.2)

    def test_19_invalid_blsr(self):
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=1.5, blsr=-0.1, ccsi=30.0, rts=0.2)

    def test_20_invalid_ccsi(self):
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=1.5, blsr=0.5, ccsi=-1.0, rts=0.2)
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=1.5, blsr=0.5, ccsi=100.1, rts=0.2)

    def test_21_invalid_rts(self):
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=1.5, blsr=0.5, ccsi=30.0, rts=-0.01)
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=1.5, blsr=0.5, ccsi=30.0, rts=1.01)

    def test_22_non_finite_inputs(self):
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=float("nan"), blsr=0.5, ccsi=30.0, rts=0.2)
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=1.5, blsr=float("inf"), ccsi=30.0, rts=0.2)
        with self.assertRaises(ValueError):
            classify_hazard_color(fos=1.5, blsr=0.5, ccsi=float("-inf"), rts=0.2)

    def test_23_non_numeric_inputs(self):
        with self.assertRaises(TypeError):
            classify_hazard_color(fos="1.5", blsr=0.5, ccsi=30.0, rts=0.2)
        with self.assertRaises(TypeError):
            classify_hazard_color(fos=1.5, blsr=None, ccsi=30.0, rts=0.2)

    # ==========================================================================
    # PART B: build_hazard_zone_feature Tests (Tests 24 - 34)
    # ==========================================================================

    def test_24_valid_polygon_feature(self):
        poly_geom = {
            "type": "Polygon",
            "coordinates": [[[76.15, 11.55], [76.16, 11.55], [76.16, 11.56], [76.15, 11.56], [76.15, 11.55]]],
        }
        feat = build_hazard_zone_feature(
            zone_id="ZONE_001",
            geometry=poly_geom,
            fos=0.72,
            blsr=1.45,
            ccsi=78.5,
            rts=0.75,
            confidence_score=88.0,
            zone_color="red",
            terrain_mode="mountain",
            is_transitional=False,
        )
        self.assertEqual(feat["type"], "Feature")
        self.assertEqual(feat["geometry"], poly_geom)
        props = feat["properties"]
        self.assertEqual(props["zone_id"], "ZONE_001")
        self.assertEqual(props["fos"], 0.72)
        self.assertEqual(props["blsr"], 1.45)
        self.assertEqual(props["ccsi"], 78.5)
        self.assertEqual(props["confidence_score"], 88.0)
        self.assertEqual(props["zone_color"], "red")
        self.assertEqual(props["terrain_mode"], "mountain")
        self.assertIs(props["is_transitional"], False)

    def test_25_valid_point_feature(self):
        pt_geom = {"type": "Point", "coordinates": [76.15, 11.55]}
        feat = build_hazard_zone_feature(
            zone_id="ZONE_002",
            geometry=pt_geom,
            fos=1.8,
            blsr=0.3,
            ccsi=25.0,
            rts=0.15,
            confidence_score=92.0,
            zone_color="green",
            terrain_mode="plains",
            is_transitional=True,
        )
        self.assertEqual(feat["type"], "Feature")
        self.assertEqual(feat["geometry"]["type"], "Point")
        self.assertIs(feat["properties"]["is_transitional"], True)

    def test_26_exact_property_key_contract(self):
        poly_geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        feat = build_hazard_zone_feature(
            zone_id="ZONE_001",
            geometry=poly_geom,
            fos=1.2,
            blsr=0.8,
            ccsi=55.0,
            rts=0.45,
            confidence_score=85.0,
            zone_color="yellow",
            terrain_mode="mountain",
            is_transitional=True,
        )
        keys = list(feat["properties"].keys())
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
        self.assertEqual(keys, expected_keys)

    def test_27_rts_is_not_present_in_properties(self):
        poly_geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        feat = build_hazard_zone_feature(
            zone_id="ZONE_001",
            geometry=poly_geom,
            fos=1.2,
            blsr=0.8,
            ccsi=55.0,
            rts=0.45,
            confidence_score=85.0,
            zone_color="yellow",
            terrain_mode="mountain",
            is_transitional=False,
        )
        self.assertNotIn("rts", feat["properties"])

    def test_28_invalid_zone_id(self):
        poly_geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="",
                geometry=poly_geom,
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="   ",
                geometry=poly_geom,
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

    def test_29_invalid_geometry(self):
        with self.assertRaises(TypeError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry="not_a_dict",
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry={"type": "InvalidType", "coordinates": [0, 0]},
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry={"type": "Polygon"},  # missing coordinates
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

    def test_30_invalid_zone_color(self):
        poly_geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry=poly_geom,
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="RED",  # uppercase
                terrain_mode="mountain",
                is_transitional=False,
            )
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry=poly_geom,
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="blue",
                terrain_mode="mountain",
                is_transitional=False,
            )

    def test_31_invalid_terrain_mode(self):
        poly_geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry=poly_geom,
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="transitional",  # not allowed in contract
                is_transitional=False,
            )

    def test_32_invalid_is_transitional(self):
        poly_geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        with self.assertRaises(TypeError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry=poly_geom,
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional="false",  # string instead of bool
            )

    def test_33_invalid_numeric_property(self):
        poly_geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry=poly_geom,
                fos=0.0,  # non-positive
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry=poly_geom,
                fos=1.5,
                blsr=-0.5,  # negative
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

    def test_34_invalid_confidence_score(self):
        poly_geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry=poly_geom,
                fos=1.5,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=-10.0,  # negative
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry=poly_geom,
                fos=1.5,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=float("nan"),
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

    # ==========================================================================
    # PART C: generate_hazard_zones Tests (Tests 35 - 40)
    # ==========================================================================

    def test_35_empty_list_returns_empty_feature_collection(self):
        res = generate_hazard_zones([])
        self.assertEqual(res, {"type": "FeatureCollection", "features": []})

    def test_36_single_valid_zone(self):
        poly = {"type": "Polygon", "coordinates": [[[76.15, 11.55], [76.16, 11.55], [76.16, 11.56], [76.15, 11.55]]]}
        records = [
            {
                "zone_id": "ZONE_001",
                "geometry": poly,
                "fos": 0.72,
                "blsr": 1.45,
                "ccsi": 78.5,
                "rts": 0.75,
                "confidence_score": 88.0,
                "zone_color": "red",
                "terrain_mode": "mountain",
                "is_transitional": False,
            }
        ]
        fc = generate_hazard_zones(records)
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(len(fc["features"]), 1)
        self.assertEqual(fc["features"][0]["properties"]["zone_id"], "ZONE_001")
        self.assertEqual(fc["features"][0]["properties"]["zone_color"], "red")

    def test_37_multiple_zones(self):
        records = [
            {
                "zone_id": "ZONE_001",
                "geometry": {"type": "Point", "coordinates": [76.15, 11.55]},
                "fos": 0.82,
                "blsr": 1.34,
                "ccsi": 75.0,
                "rts": 0.8,
                "confidence_score": 83.5,
                "zone_color": "red",
                "terrain_mode": "mountain",
                "is_transitional": False,
            },
            {
                "zone_id": "ZONE_002",
                "geometry": {"type": "Point", "coordinates": [76.13, 11.54]},
                "fos": 1.18,
                "blsr": 0.4,
                "ccsi": 45.0,
                "rts": 0.3,
                "confidence_score": 79.0,
                "zone_color": "yellow",
                "terrain_mode": "mountain",
                "is_transitional": True,
            },
        ]
        fc = generate_hazard_zones(records)
        self.assertEqual(len(fc["features"]), 2)
        self.assertEqual(fc["features"][0]["properties"]["zone_id"], "ZONE_001")
        self.assertEqual(fc["features"][1]["properties"]["zone_id"], "ZONE_002")

    def test_38_missing_zone_color_automatic_classification(self):
        # Record without zone_color: FOS=0.82 -> should automatically classify as 'red'
        records = [
            {
                "zone_id": "ZONE_AUTO",
                "geometry": {"type": "Point", "coordinates": [76.15, 11.55]},
                "fos": 0.82,
                "blsr": 0.5,
                "ccsi": 30.0,
                "rts": 0.2,
                "confidence_score": 85.0,
                "terrain_mode": "mountain",
                "is_transitional": False,
            }
        ]
        fc = generate_hazard_zones(records)
        self.assertEqual(fc["features"][0]["properties"]["zone_color"], "red")

    def test_39_malformed_zone_record_rejected(self):
        # Missing required key 'fos'
        bad_records = [
            {
                "zone_id": "ZONE_001",
                "geometry": {"type": "Point", "coordinates": [76.15, 11.55]},
                "blsr": 0.5,
                "ccsi": 30.0,
                "rts": 0.2,
                "confidence_score": 85.0,
                "terrain_mode": "mountain",
                "is_transitional": False,
            }
        ]
        with self.assertRaises(ValueError):
            generate_hazard_zones(bad_records)

        # Record is not a dictionary
        with self.assertRaises(TypeError):
            generate_hazard_zones(["not_a_dict"])

    def test_40_non_list_input_rejected(self):
        with self.assertRaises(TypeError):
            generate_hazard_zones("not_a_list")
        with self.assertRaises(TypeError):
            generate_hazard_zones(None)
        with self.assertRaises(TypeError):
            generate_hazard_zones({"features": []})

    def test_41_valid_geometry_collection(self):
        geom_coll = {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "Point", "coordinates": [76.15, 11.55]},
                {"type": "LineString", "coordinates": [[76.15, 11.55], [76.16, 11.56]]},
            ],
        }
        feat = build_hazard_zone_feature(
            zone_id="ZONE_GC",
            geometry=geom_coll,
            fos=1.5,
            blsr=0.5,
            ccsi=30.0,
            rts=0.2,
            confidence_score=80.0,
            zone_color="green",
            terrain_mode="mountain",
            is_transitional=False,
        )
        self.assertEqual(feat["geometry"]["type"], "GeometryCollection")
        self.assertEqual(len(feat["geometry"]["geometries"]), 2)

    def test_42_geometry_collection_missing_geometries_rejected(self):
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry={"type": "GeometryCollection"},
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

    def test_43_geometry_collection_coordinates_only_rejected(self):
        with self.assertRaises(ValueError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry={"type": "GeometryCollection", "coordinates": [76.15, 11.55]},
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )

    def test_44_geometry_collection_non_list_geometries_rejected(self):
        with self.assertRaises(TypeError):
            build_hazard_zone_feature(
                zone_id="ZONE_001",
                geometry={"type": "GeometryCollection", "geometries": "not_a_list"},
                fos=1.0,
                blsr=0.5,
                ccsi=30.0,
                rts=0.2,
                confidence_score=80.0,
                zone_color="green",
                terrain_mode="mountain",
                is_transitional=False,
            )


if __name__ == "__main__":
    unittest.main()

