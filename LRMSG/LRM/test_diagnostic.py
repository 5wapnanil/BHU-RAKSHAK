import sys
sys.path.append("c:\\Users\\bubub\\Downloads\\LRMSG\\LRM")

from backend.app.services.open_meteo_service import fetch_current_environment
from backend.app.services.opentopo_service import fetch_terrain
from backend.app.services.soilgrids_service import fetch_wrb_soil
from backend.app.services.feature_engineering import engineer_features
from backend.app.model.prediction_service import predict_complete

lat = 27.338483
lon = 88.623217

def run():
    env_data = fetch_current_environment(lat, lon)
    soil_data = fetch_wrb_soil(lat, lon)
    terrain_data = fetch_terrain(lat, lon)
    
    features = engineer_features(
        rzsm_1=env_data["rzsm_1"],
        rzsm_2=env_data["rzsm_2"],
        rzsm_3=env_data["rzsm_3"],
        cumulative_rainfall_3d_mm=env_data["cumulative_rainfall_3d_mm"],
        previous=env_data.get("previous", []),
        previous_rainfall=env_data.get("previous_rainfall", float("nan"))
    )
    
    predict_complete(
        rzsm_1=env_data["rzsm_1"],
        rzsm_2=env_data["rzsm_2"],
        rzsm_3=env_data["rzsm_3"],
        cumulative_rainfall_3d_mm=env_data["cumulative_rainfall_3d_mm"],
        rzsm_mean=features["rzsm_mean"],
        rzsm_range=features["rzsm_range"],
        rzsm_surface_deep_diff=features["rzsm_surface_deep_diff"],
        rain_rzsm_interaction=features["rain_rzsm_interaction"],
        previous_rzsm=features["previous_rzsm"],
        previous_rzsm_2=features["previous_rzsm_2"],
        previous_rzsm_3=features["previous_rzsm_3"],
        previous_rainfall=features["previous_rainfall"],
        rzsm_0_100=features["rzsm_0_100"],
        elevation_m=terrain_data["elevation_m"],
        slope_deg=terrain_data["slope_deg"],
        soil_type_wrb=soil_data["soil_type_wrb"],
    )

if __name__ == "__main__":
    run()
