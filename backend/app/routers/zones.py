import os
import json
from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOCK_ZONES_PATH = os.path.join(BASE_DIR, "data", "mock_zones.geojson")

@router.get("/zones")
def get_zones():
    if not os.path.exists(MOCK_ZONES_PATH):
        raise HTTPException(status_code=404, detail="Mock zones data not found")
    with open(MOCK_ZONES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
