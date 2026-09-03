from fastapi import APIRouter
from ..models.schemas import AlertRequest
from ..services.cap_alert_builder import build_cap_alert, build_simulated_sms
from .triage import MOCK_TRIAGE_DATA

router = APIRouter()

@router.post("/alerts/dispatch")
def dispatch_alerts(req: AlertRequest):
    """
    Format and broadcast NDMA Sachet/CAP-1.2 compliant XML alerts and simulated SMS dispatch.
    """
    target_name = "Wayanad Highland Habitations"
    lat, lon = 11.54, 76.15
    
    if req.habitation_ids:
        primary_id = req.habitation_ids[0].lower()
        for h in MOCK_TRIAGE_DATA:
            if h.habitation_id.lower() == primary_id:
                target_name = h.name
                lat, lon = h.lat, h.lon
                break
        else:
            target_name = f"Habitation {req.habitation_ids[0].upper()}"

    cap_xml = build_cap_alert(
        habitation_name=target_name,
        message=req.message_local_language,
        lat=lat,
        lon=lon
    )
    
    total_recipients = max(1, len(req.habitation_ids)) * 150
    sms_dispatch = build_simulated_sms(
        habitation_name=target_name,
        message=req.message_local_language,
        recipient_count=total_recipients
    )
    
    return {
        "status": "dispatched",
        "alerts_count": len(req.habitation_ids),
        "cap_xml": cap_xml,
        "sms_dispatch": sms_dispatch
    }
