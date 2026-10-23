import requests
import json
import os

def fetch_highways():
    print("Querying Overpass API for NER highways (trunk, primary, secondary)...")
    
    query = """
    [out:json][timeout:300];
    (
      way["highway"~"trunk|primary|secondary"](24.0,89.6,29.5,97.4);
    );
    out geom;
    """
    
    headers = {
        "User-Agent": "LandslideRiskMapBot/1.0"
    }
    
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data={'data': query}, headers=headers)
        if response.status_code != 200:
            print("Failed. Status code:", response.status_code)
            print(response.text)
            return
    except Exception as e:
        print("Failed to fetch data:", str(e))
        return
        
    data = response.json()
    
    features = []
    for element in data.get("elements", []):
        if element["type"] == "way":
            coords = [[node["lon"], node["lat"]] for node in element.get("geometry", [])]
            if len(coords) < 2:
                continue
                
            tags = element.get("tags", {})
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "properties": {
                    "id": element["id"],
                    "highway": tags.get("highway", "unknown"),
                    "name": tags.get("name", "Unknown Road"),
                    "ref": tags.get("ref", "")
                }
            }
            features.append(feature)
            
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    os.makedirs("backend/app/data", exist_ok=True)
    out_path = "backend/app/data/ner_highways.geojson"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f)
        
    print(f"Successfully saved {len(features)} highway features to {out_path}.")

if __name__ == "__main__":
    fetch_highways()
