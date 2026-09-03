from fastapi import APIRouter
from ..models.schemas import ManifestRequest

router = APIRouter()

@router.post("/manifest/{habitation_id}/authorize")
def authorize_manifest(habitation_id: str, req: ManifestRequest):
    return {
        "status": "PENDING_DM_AUTHORIZATION",
        "habitation_id": habitation_id,
        "authorized_by": req.authorized_by,
        "message": f"Manifest for {habitation_id} submitted for DM authorization."
    }
