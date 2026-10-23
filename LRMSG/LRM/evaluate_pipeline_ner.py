import sys
import json
from backend.app.api.endpoints.prediction import location_prediction
from backend.app.schemas.prediction import LocationPredictionRequest

coordinates = [
    {"name": "Cherrapunji, Meghalaya (Extreme Rain, High Slope)", "lat": 25.2702, "lon": 91.7323},
    {"name": "Aizawl, Mizoram (High Rain, Very High Slope)", "lat": 23.7271, "lon": 92.7176},
    {"name": "Tawang, Arunachal Pradesh (High Elevation, Steep)", "lat": 27.5860, "lon": 91.8596},
    {"name": "Gangtok, Sikkim (Himalayan Terrain)", "lat": 27.3389, "lon": 88.6065},
    {"name": "Kohima, Nagaland (Hilly Terrain)", "lat": 25.6751, "lon": 94.1086},
    {"name": "Guwahati Plains, Assam (Low Slope, High Rain)", "lat": 26.1420, "lon": 91.7713},
    {"name": "Majuli Island, Assam (Flat Riverine, Very Low Slope)", "lat": 26.9535, "lon": 94.2498},
    {"name": "Agartala, Tripura (Low/Moderate Slope)", "lat": 23.8315, "lon": 91.2868},
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
