from pydantic import BaseModel, Field
from typing import Any, Dict


class LocationPredictionRequest(BaseModel):
    latitude: float
    longitude: float

class CustomPredictionRequest(BaseModel):
    rainfall: float
    soilMoisture: float
    slope: float
    elevation: float
    soilType: str

class PredictionRequest(BaseModel):
    """
    Input required to execute the complete frozen ML pipeline.
    """
    rzsm_1: float
    rzsm_2: float
    rzsm_3: float
    cumulative_rainfall_3d_mm: float
    rzsm_mean: float = Field(alias="_rzsm_mean_")
    rzsm_range: float = Field(alias="_rzsm_range_")
    rzsm_surface_deep_diff: float = Field(alias="_rzsm_surface_deep_diff_")
    rain_rzsm_interaction: float = Field(alias="_rain_rzsm_interaction_")
    previous_rzsm: float = Field(alias="_previous_rzsm_")
    previous_rzsm_2: float = Field(alias="_previous_rzsm_2_")
    previous_rzsm_3: float = Field(alias="_previous_rzsm_3_")
    previous_rainfall: float = Field(alias="_previous_rainfall_")
    rzsm_0_100: float
    elevation_m: float
    slope_deg: float
    soil_type_wrb: str


class FinalCalibrationDetail(BaseModel):
    method: str
    a: float
    b: float

class XGBoostDetail(BaseModel):
    raw_probability: float
    calibrated_probability: float
    prediction: int
    calibration: FinalCalibrationDetail

class AHCDetail(BaseModel):
    cluster: int
    susceptibility: float
    category: str

class FinalDecisionDetail(BaseModel):
    raw_probability: float
    calibrated_probability: float
    prediction: int
    calibration: FinalCalibrationDetail

class PredictionResponse(BaseModel):
    """
    Final response returned by the prediction API.
    """
    xgboost: XGBoostDetail
    ahc: AHCDetail
    final_decision: FinalDecisionDetail
    prediction: int
    probability: float
    features: Dict[str, Any] = None