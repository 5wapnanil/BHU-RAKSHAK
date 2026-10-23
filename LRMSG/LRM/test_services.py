import sys
from backend.app.services.open_meteo_service import fetch_current_environment
from backend.app.services.soilgrids_service import fetch_wrb_soil
from backend.app.services.opentopo_service import fetch_terrain

lat, lon = 26.7271, 88.3953

print("--- Testing Open-Meteo ---")
try:
    env = fetch_current_environment(lat, lon)
    print(f"Success! RZSM1: {env['rzsm_1']}, Rainfall: {env['cumulative_rainfall_3d_mm']}")
except Exception as e:
    print(f"Open-Meteo Failed: {e}")

print("\n--- Testing SoilGrids ---")
try:
    soil = fetch_wrb_soil(lat, lon)
    print(f"Success! Soil Type: {soil['soil_type_wrb']}")
except Exception as e:
    print(f"SoilGrids Failed: {e}")

print("\n--- Testing OpenTopoData Terrain ---")
try:
    terrain = fetch_terrain(lat, lon)
    print(f"Success! Elevation: {terrain['elevation_m']}, Slope: {terrain['slope_deg']}")
except Exception as e:
    print(f"OpenTopoData Failed: {e}")
