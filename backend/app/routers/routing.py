import os
import json
from fastapi import APIRouter, Query, HTTPException
from ..models.schemas import RouteResponse
from ..services.routing_engine import get_safe_route

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOCK_ZONES_PATH = os.path.join(BASE_DIR, "data", "mock_zones.geojson")

def _get_red_zone_polygons():
    if not os.path.exists(MOCK_ZONES_PATH):
        return []
    try:
        with open(MOCK_ZONES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        red_polygons = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            color = props.get("zone_color", "").lower()
            if color == "red":
                geom = feature.get("geometry")
                if geom:
                    red_polygons.append(geom)
        return red_polygons
    except Exception:
        return []

@router.get("/route", response_model=RouteResponse)
def get_route(
    from_lat: float = Query(..., description="Starting latitude"),
    from_lon: float = Query(..., description="Starting longitude"),
    to_lat: float = Query(..., description="Destination latitude"),
    to_lon: float = Query(..., description="Destination longitude"),
    region: str = Query("wayanad", description="Region name for graph network")
):
    try:
        red_polygons = _get_red_zone_polygons()
        result = get_safe_route(
            region=region,
            from_lat=from_lat,
            from_lon=from_lon,
            to_lat=to_lat,
            to_lon=to_lon,
            red_zone_polygons=red_polygons
        )
        return RouteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")
