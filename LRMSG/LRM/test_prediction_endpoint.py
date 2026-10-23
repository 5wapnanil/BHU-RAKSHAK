import sys
import json
from backend.app.api.endpoints.prediction import location_prediction
from backend.app.schemas.prediction import LocationPredictionRequest

print("Starting end-to-end API prediction test...")
try:
    req = LocationPredictionRequest(latitude=26.7271, longitude=88.3953)
    response = location_prediction(req)
    print("\n--- FULL PREDICTION API RESPONSE ---")
    print(response.model_dump_json(indent=2))
    print("\nSUCCESS! The endpoint successfully ran the ML pipeline.")
except Exception as e:
    print(f"\nAPI Endpoint Failed: {e}")
    sys.exit(1)
