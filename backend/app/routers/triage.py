from fastapi import APIRouter
from typing import List
from ..models.schemas import HabitationTriage

router = APIRouter()

MOCK_TRIAGE_DATA: List[HabitationTriage] = [
    HabitationTriage(
        habitation_id="hab_001",
        name="Mundakkai Settlement",
        rts_score=0.88,
        tti_hours=2.5,
        svi=0.74,
        struct_load=1.35,
        demo_exposure=420.0,
        priority_rank=1,
        lat=11.538,
        lon=76.155
    ),
    HabitationTriage(
        habitation_id="hab_002",
        name="Chooralmala Riverside",
        rts_score=0.76,
        tti_hours=4.0,
        svi=0.62,
        struct_load=1.10,
        demo_exposure=280.0,
        priority_rank=2,
        lat=11.542,
        lon=76.162
    )
]

@router.get("/triage", response_model=List[HabitationTriage])
def get_triage():
    return MOCK_TRIAGE_DATA
