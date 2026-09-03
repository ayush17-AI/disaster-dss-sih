from pydantic import BaseModel
from typing import List, Dict, Any

class HazardZone(BaseModel):
    zone_id: str
    geometry: Dict[str, Any]
    fos: float
    blsr: float
    ccsi: float
    confidence_score: float
    zone_color: str
    terrain_mode: str

class HabitationTriage(BaseModel):
    habitation_id: str
    name: str
    rts_score: float
    tti_hours: float
    svi: float
    struct_load: float
    demo_exposure: float
    priority_rank: int
    lat: float
    lon: float

class RouteRequest(BaseModel):
    from_lat: float
    from_lon: float
    to_lat: float
    to_lon: float

class RouteResponse(BaseModel):
    path_coordinates: List[List[float]]
    distance_km: float
    avoids_red_zones: bool

class ManifestRequest(BaseModel):
    habitation_id: str
    authorized_by: str

class AlertRequest(BaseModel):
    habitation_ids: List[str]
    message_local_language: str
