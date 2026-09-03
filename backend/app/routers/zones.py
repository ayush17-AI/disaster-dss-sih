import os
import json
from fastapi import APIRouter

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOCK_ZONES_PATH = os.path.join(BASE_DIR, "data", "mock_zones.geojson")
LIVE_ZONES_PATH = os.path.join(BASE_DIR, "data", "zones.geojson")
DATA_MOCK_ZONES = os.path.join(os.path.dirname(BASE_DIR), "data", "mock", "zones_wayanad.json")

# In-memory disaster-proof fallback in case of disk I/O lock
IN_MEMORY_FALLBACK = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": "zone_001",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [76.15, 11.55],
                        [76.16, 11.55],
                        [76.16, 11.56],
                        [76.15, 11.56],
                        [76.15, 11.55]
                    ]
                ]
            },
            "properties": {
                "zone_id": "zone_001",
                "name": "Chooralmala Debris Corridor (Hardened Fallback)",
                "zone_color": "RED",
                "fos": 0.72,
                "blsr": 1.45,
                "ccsi": 0.88,
                "confidence_score": 0.85,
                "terrain_mode": "MOUNTAIN_CASCADE"
            }
        },
        {
            "type": "Feature",
            "id": "zone_002",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [76.13, 11.54],
                        [76.14, 11.54],
                        [76.14, 11.55],
                        [76.13, 11.55],
                        [76.13, 11.54]
                    ]
                ]
            },
            "properties": {
                "zone_id": "zone_002",
                "name": "Meppadi Buffer Zone (Hardened Fallback)",
                "zone_color": "YELLOW",
                "fos": 1.15,
                "blsr": 0.92,
                "ccsi": 0.54,
                "confidence_score": 0.78,
                "terrain_mode": "MOUNTAIN_CASCADE"
            }
        }
    ]
}

@router.get("/zones")
def get_zones():
    """
    Retrieve hazard zones with multi-tier error shielding and defensive fallback.
    Tier 1: Live computed file by Role A (if present and unlocked)
    Tier 2: Cached mock_zones.geojson on disk
    Tier 3: In-memory fallback FeatureCollection (zero disk failure risk)
    """
    # Tier 1: Try live computed zones if available
    if os.path.exists(LIVE_ZONES_PATH):
        try:
            with open(LIVE_ZONES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("type") == "FeatureCollection" and data.get("features"):
                    return data
        except Exception:
            pass  # Fall through to Tier 2 on lock or partial write

    # Tier 2: Try disk mock_zones.geojson
    if os.path.exists(MOCK_ZONES_PATH):
        try:
            with open(MOCK_ZONES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("type") == "FeatureCollection" and data.get("features"):
                    return data
        except Exception:
            pass

    # Tier 2b: Try root /data/mock/zones_wayanad.json
    if os.path.exists(DATA_MOCK_ZONES):
        try:
            with open(DATA_MOCK_ZONES, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("type") == "FeatureCollection":
                    return data
        except Exception:
            pass

    # Tier 3: In-memory fail-safe
    return IN_MEMORY_FALLBACK
