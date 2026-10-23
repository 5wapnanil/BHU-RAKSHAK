from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Dict
from backend.app.services.spatial_analysis import get_spatial_engine

router = APIRouter()

class DistrictRisk(BaseModel):
    risk_score: float
    risk_level: str

class RoadImpactRequest(BaseModel):
    district_risks: Dict[str, DistrictRisk]

@router.post("/road-impact/analyze")
def analyze_road_impact(request: RoadImpactRequest):
    engine = get_spatial_engine()
    
    # Convert Pydantic dict to native dict
    risks = {k: {"risk_score": v.risk_score, "risk_level": v.risk_level} for k, v in request.district_risks.items()}
    
    geojson = engine.analyze_impact(risks)
    return geojson
