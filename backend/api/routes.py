import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from geo_engine.formulas import calculate_fos
from routing.router import compute_safe_route

router = APIRouter()

MOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "mock")

class AuthorizePayload(BaseModel):
    habitation_id: str
    status: str

@router.get("/zones")
def get_zones(region: str, rainfall_intensity: float, construction_load: float):
    file_path = os.path.join(MOCK_DIR, "zones_wayanad.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Mock data not found")
    with open(file_path, "r") as f:
        data = json.load(f)
        
    # Scale m based on rainfall (0 to 150 -> 0.0 to 1.0)
    m = min(1.0, max(0.0, rainfall_intensity / 100.0))
    q = construction_load * 15.0 # Base load scaled
    
    red_zones = []
    
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        # Simulated base properties for zone
        beta = 35.0 if props.get("name") == "Chooralmala" else 25.0
        z = 5.0
        c_prime = 10.0
        phi_prime = 30.0
        
        fos = calculate_fos(beta, z, c_prime, phi_prime, m, q)
        props["FOS"] = fos
        
        if fos < 1.0:
            props["zone_color"] = "RED"
            red_zones.append(feature)
        elif fos < 1.3:
            props["zone_color"] = "YELLOW"
        else:
            props["zone_color"] = "GREEN"

    return data

@router.get("/triage")
def get_triage(region: str):
    file_path = os.path.join(MOCK_DIR, "triage_wayanad.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Mock data not found")
    with open(file_path, "r") as f:
        return json.load(f)

@router.get("/route")
def get_route(from_lat: float, from_lon: float, to_shelter_id: str):
    return compute_safe_route(from_lat, from_lon, to_shelter_id, [])

@router.post("/manifest/authorize")
def authorize_manifest(payload: AuthorizePayload):
    return {
        "status": "AUTHORIZED",
        "link": "https://example.com/manifest_approved.pdf"
    }

@router.get("/alerts/cap-payload")
def get_cap_payload(habitation_id: str):
    return {
        "xml": "<alert xmlns='urn:oasis:names:tc:emergency:cap:1.2'><info><event>Landslide Warning</event></info></alert>",
        "sms": "URGENT: Landslide risk high. Evacuate immediately."
    }
