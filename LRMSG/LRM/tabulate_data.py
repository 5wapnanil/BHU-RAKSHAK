import sys
sys.path.append("c:\\Users\\bubub\\Downloads\\LRMSG\\LRM")

from backend.app.services.open_meteo_service import fetch_current_environment
from backend.app.services.opentopo_service import fetch_terrain
from backend.app.services.soilgrids_service import fetch_wrb_soil
from backend.app.services.feature_engineering import engineer_features
from backend.app.model.prediction_service import XGBOOST_FEATURES, AHC_NUMERICAL_FEATURES, predict_ahc

lat = 27.041
lon = 88.2663

def run():
    env_data = fetch_current_environment(lat, lon)
    soil_data = fetch_wrb_soil(lat, lon)
    terrain_data = fetch_terrain(lat, lon)
    
    features = engineer_features(
        rzsm_1=env_data["rzsm_1"],
        rzsm_2=env_data["rzsm_2"],
        rzsm_3=env_data["rzsm_3"],
        cumulative_rainfall_3d_mm=env_data["cumulative_rainfall_3d_mm"],
        previous=env_data.get("previous", {})
    )
    
    # 1. XGBoost inputs
    xgb_dict = {
        "rzsm_1": env_data["rzsm_1"],
        "rzsm_2": env_data["rzsm_2"],
        "rzsm_3": env_data["rzsm_3"],
        "cumulative_rainfall_3d_mm": env_data["cumulative_rainfall_3d_mm"],
        "_rzsm_mean_": features["rzsm_mean"],
        "_rzsm_range_": features["rzsm_range"],
        "_rzsm_surface_deep_diff_": features["rzsm_surface_deep_diff"],
        "_rain_rzsm_interaction_": features["rain_rzsm_interaction"],
        "_previous_rzsm_": features["previous_rzsm"],
        "_previous_rzsm_2_": features["previous_rzsm_2"],
        "_previous_rzsm_3_": features["previous_rzsm_3"],
        "_previous_rainfall_": features["previous_rainfall"],
    }
    
    print("=== XGBOOST INPUTS ===")
    for k, v in xgb_dict.items():
        print(f"{k}|{v}")
        
    print("=== AHC INPUTS ===")
    ahc_dict = {
        "cumulative_rainfall_3d_mm": env_data["cumulative_rainfall_3d_mm"],
        "rzsm_0_100": features["rzsm_0_100"],
        "elevation_m": terrain_data["elevation_m"],
        "slope_deg": terrain_data["slope_deg"],
        "soil_type_wrb": soil_data["soil_type_wrb"]
    }
    for k, v in ahc_dict.items():
        print(f"{k}|{v}")

if __name__ == "__main__":
    run()
