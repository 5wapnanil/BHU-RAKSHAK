from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Any
import logging

from backend.app.model.prediction_service import predict_complete
from backend.app.schemas.prediction import (
    PredictionRequest,
    LocationPredictionRequest,
    CustomPredictionRequest,
    PredictionResponse,
    XGBoostDetail,
    AHCDetail,
    FinalDecisionDetail,
)
from backend.app.services.open_meteo_service import fetch_current_environment, DataSourceError
from backend.app.services.soilgrids_service import fetch_wrb_soil, SoilDataError
from backend.app.services.feature_engineering import engineer_features
from backend.app.services.opentopo_service import fetch_terrain, TerrainDataError
from backend.app.services.alert_engine import alert_engine

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prediction",
    tags=["Prediction"],
)

def _build_response(result: dict[str, Any], features: dict[str, Any] = None) -> PredictionResponse:
    return PredictionResponse(
        xgboost=XGBoostDetail(
            raw_probability=result["xgboost"]["raw_probability"],
            calibrated_probability=result["xgboost"]["calibrated_probability"],
            prediction=result["xgboost"]["prediction"],
            calibration=result["xgboost"]["calibration"],
        ),
        ahc=AHCDetail(
            cluster=result["ahc"]["cluster"],
            susceptibility=result["ahc"]["susceptibility"],
            category=result["ahc"]["category"],
        ),
        final_decision=FinalDecisionDetail(
            raw_probability=result["final_decision"]["raw_probability"],
            calibrated_probability=result["final_decision"]["calibrated_probability"],
            prediction=result["final_decision"]["prediction"],
            calibration=result["final_decision"]["calibration"],
        ),
        prediction=result["final_decision"]["prediction"],
        probability=result["final_decision"]["calibrated_probability"],
        features=features,
    )

DISABLED_PREDICTION_DETAIL = "The legacy landslide prediction ML model has been retired and disabled."

@router.post("/", response_model=PredictionResponse)
def prediction():
    """Disabled: The legacy landslide prediction ML model is retired."""
    raise HTTPException(
        status_code=503,
        detail=DISABLED_PREDICTION_DETAIL
    )

@router.post("/location", response_model=PredictionResponse)
def location_prediction():
    """Disabled: The legacy landslide prediction ML model is retired."""
    raise HTTPException(
        status_code=503,
        detail=DISABLED_PREDICTION_DETAIL
    )

@router.post("/custom", response_model=PredictionResponse)
def custom_prediction():
    """Disabled: The legacy landslide prediction ML model is retired."""
    raise HTTPException(
        status_code=503,
        detail=DISABLED_PREDICTION_DETAIL
    )