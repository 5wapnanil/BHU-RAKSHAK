from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
import logging

from backend.app.services.open_meteo_service import fetch_current_environment, DataSourceError
from backend.app.services.soilgrids_service import fetch_wrb_soil, SoilDataError
from backend.app.services.feature_engineering import engineer_features
from backend.app.services.opentopo_service import fetch_terrain, TerrainDataError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/environmental-data",
    tags=["Environment"],
)

class LocationRequest(BaseModel):
    latitude: float
    longitude: float

@router.post("/location")
def get_environmental_data(request: LocationRequest) -> dict[str, Any]:
    try:
        # 1. Fetch Weather Data
        env_data = fetch_current_environment(request.latitude, request.longitude)
        
        # 2. Fetch Soil Data
        soil_data = fetch_wrb_soil(request.latitude, request.longitude)
        
        # 3. Fetch Terrain Data (No Auth Required)
        terrain_data = fetch_terrain(request.latitude, request.longitude)

        # 4. Feature Engineering
        features = engineer_features(
            rzsm_1=env_data["rzsm_1"],
            rzsm_2=env_data["rzsm_2"],
            rzsm_3=env_data["rzsm_3"],
            cumulative_rainfall_3d_mm=env_data["cumulative_rainfall_3d_mm"],
            previous=[]
        )

        return {
            "latitude": request.latitude,
            "longitude": request.longitude,
            "observed_at_utc": env_data["timestamp_utc"],
            "rzsm_1": env_data["rzsm_1"],
            "rzsm_2": env_data["rzsm_2"],
            "rzsm_3": env_data["rzsm_3"],
            "rzsm_0_100": features["rzsm_0_100"],
            "cumulative_rainfall_3d_mm": env_data["cumulative_rainfall_3d_mm"],
            "rzsm_mean": features["rzsm_mean"],
            "rzsm_range": features["rzsm_range"],
            "rzsm_surface_deep_diff": features["rzsm_surface_deep_diff"],
            "rain_rzsm_interaction": features["rain_rzsm_interaction"],
            "previous_rzsm": features["previous_rzsm"],
            "previous_rzsm_2": features["previous_rzsm_2"],
            "previous_rzsm_3": features["previous_rzsm_3"],
            "previous_rainfall": features["previous_rainfall"],
            "elevation_m": terrain_data["elevation_m"],
            "slope_deg": terrain_data["slope_deg"],
            "soil_type_wrb": soil_data["soil_type_wrb"],
        }
    except (DataSourceError, SoilDataError, TerrainDataError) as exc:
        logger.warning(f"Environmental data fetch failed: {exc}")
        raise HTTPException(status_code=400, detail="Environmental data unavailable for this location")
    except Exception as exc:
        logger.error(f"Unexpected error in environmental data endpoint: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")
