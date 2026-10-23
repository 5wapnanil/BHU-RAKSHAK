from backend.app.services.open_meteo_service import fetch_current_environment
from backend.app.services.opentopo_service import fetch_terrain
from backend.app.services.soilgrids_service import fetch_wrb_soil
import pprint
import sys

# Test coordinates (Darjeeling)
lat = 27.041
lon = 88.2663

def dump_data():
    try:
        print("=== OPEN METEO DATA (Weather/Soil Moisture) ===")
        om_data = fetch_current_environment(lat, lon)
        pprint.pprint(om_data)
        
        print("\n=== OPENTOPO DATA (Elevation/Slope) ===")
        topo_data = fetch_terrain(lat, lon)
        pprint.pprint(topo_data)
        
        print("\n=== SOILGRIDS DATA (Soil Type) ===")
        soil_data = fetch_wrb_soil(lat, lon)
        pprint.pprint(soil_data)
        
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    dump_data()
