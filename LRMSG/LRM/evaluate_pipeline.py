import sys
import json
from backend.app.api.endpoints.prediction import location_prediction
from backend.app.schemas.prediction import LocationPredictionRequest

coordinates = [
    {"name": "Cherrapunji (High Slope, High Rain)", "lat": 25.2702, "lon": 91.7323},
    {"name": "Guwahati Plains (Low Slope, High Rain)", "lat": 26.1420, "lon": 91.7713},
    {"name": "Darjeeling (Steep, Variable Rain)", "lat": 27.0410, "lon": 88.2663},
    {"name": "Jaisalmer (Flat, Dry)", "lat": 26.9157, "lon": 70.9083},
    {"name": "Leh (Steep, Dry)", "lat": 34.1526, "lon": 77.5771},
]

results = []

for coord in coordinates:
    try:
        req = LocationPredictionRequest(latitude=coord["lat"], longitude=coord["lon"])
        res = location_prediction(req)
        results.append({
            "Location": coord["name"],
            "Latitude": coord["lat"],
            "Longitude": coord["lon"],
            "Features": res.features,
            "XGBoost_Probability": res.xgboost.probability,
            "AHC_Susceptibility": res.ahc.susceptibility,
            "AHC_Cluster": res.ahc.cluster,
            "Final_Probability": res.probability
        })
    except Exception as e:
        results.append({
            "Location": coord["name"],
            "Error": str(e)
        })

print(json.dumps(results, indent=2))
