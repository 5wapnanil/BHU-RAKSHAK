import requests
import json

# Start FastAPI server on port 8003 if not running
API_URL = "http://127.0.0.1:8003/prediction/location"

TEST_LOCATIONS = [
    {"name": "Chandmari, Gangtok", "latitude": 27.338483, "longitude": 88.623217},
    {"name": "Indira Bye Pass, Gangtok", "latitude": 27.328889, "longitude": 88.607778},
    {"name": "Darjeeling", "latitude": 27.041000, "longitude": 88.266300},
    {"name": "Siliguri", "latitude": 26.727100, "longitude": 88.395300},
    {"name": "Shillong", "latitude": 25.578800, "longitude": 91.893300},
    {"name": "Guwahati", "latitude": 26.144500, "longitude": 91.736200},
    {"name": "Kolkata", "latitude": 22.5726, "longitude": 88.3639},
]

print(f"{'Location':<30} | {'Rain':<7} | {'Moist':<6} | {'Slope':<6} | {'Elev':<5} | {'Soil':<10} | {'RawXGB':<7} | {'Clust':<5} | {'Susc':<6} | {'Cat':<4} | {'RawFin':<7} | {'CalFin':<7} | {'Pred':<4}")
print("-" * 135)

for loc in TEST_LOCATIONS:
    payload = {"latitude": loc["latitude"], "longitude": loc["longitude"]}
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        f = data["features"]
        x = data["xgboost"]
        a = data["ahc"]
        fd = data["final_decision"]
        
        print(f"{loc['name']:<30} | "
              f"{f['rainfall']:<7.1f} | "
              f"{f['soilMoisture']:<6.3f} | "
              f"{f['slope']:<6.2f} | "
              f"{f['elevation']:<5.0f} | "
              f"{f['soilType']:<10} | "
              f"{x['raw_probability']:<7.3f} | "
              f"{a['cluster']:<5} | "
              f"{a['susceptibility']:<6.2f} | "
              f"{a['category']:<4} | "
              f"{fd['raw_probability']:<7.3f} | "
              f"{fd['calibrated_probability']:<7.3f} | "
              f"{fd['prediction']:<4}")
    except Exception as e:
        print(f"{loc['name']:<30} | ERROR: {e}")
