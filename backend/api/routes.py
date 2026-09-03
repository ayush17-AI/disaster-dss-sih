import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
        return json.load(f)

@router.get("/triage")
def get_triage(region: str):
    file_path = os.path.join(MOCK_DIR, "triage_wayanad.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Mock data not found")
    with open(file_path, "r") as f:
        return json.load(f)

@router.get("/route")
def get_route(from_lat: float, from_lon: float, to_shelter_id: str):
    file_path = os.path.join(MOCK_DIR, "route_sample.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Mock data not found")
    with open(file_path, "r") as f:
        return json.load(f)

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
