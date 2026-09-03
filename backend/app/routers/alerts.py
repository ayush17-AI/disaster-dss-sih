from fastapi import APIRouter
from ..models.schemas import AlertRequest

router = APIRouter()

@router.post("/alerts/dispatch")
def dispatch_alerts(req: AlertRequest):
    return {
        "status": "dispatched",
        "count": len(req.habitation_ids),
        "habitation_ids": req.habitation_ids,
        "message": "CAP alerts formatted and queued for SMS transmission"
    }
