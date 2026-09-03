import os
import time
from datetime import datetime
from fastapi import APIRouter
from ..models.schemas import ManifestRequest
from ..services.manifest_generator import generate_manifest_pdf, STATIC_MANIFESTS_DIR
from .triage import MOCK_TRIAGE_DATA

router = APIRouter()

@router.post("/manifest/{habitation_id}/authorize")
def authorize_manifest(habitation_id: str, req: ManifestRequest):
    # Lookup habitation in mock triage data or create matching dictionary
    matched = None
    for h in MOCK_TRIAGE_DATA:
        if h.habitation_id.lower() == habitation_id.lower():
            matched = h.model_dump()
            break
            
    if not matched:
        matched = {
            "habitation_id": habitation_id,
            "name": f"Habitation {habitation_id.upper()}",
            "priority_rank": 1,
            "rts_score": 0.85,
            "struct_load": 1.25,
            "tti_hours": 3.0,
            "svi": 0.70,
            "demo_exposure": 350.0,
            "lat": 11.54,
            "lon": 76.15
        }
        
    clean_hab = habitation_id.lower().replace("-", "_")
    timestamp_suffix = int(time.time())
    filename = f"{clean_hab}_authorized_{timestamp_suffix}.pdf"
    output_path = os.path.join(STATIC_MANIFESTS_DIR, filename)
    
    meta = generate_manifest_pdf(
        habitation=matched,
        output_path=output_path,
        authorized_by=req.authorized_by or "District Magistrate"
    )
    
    order_ref = meta["order_id"]
    download_url = f"/static/manifests/{filename}"
    iso_timestamp = datetime.utcnow().isoformat() + "Z"
    
    return {
        "status": "AUTHORIZED",
        "order_id": order_ref,
        "download_url": download_url,
        "habitation_id": habitation_id,
        "timestamp": iso_timestamp
    }
