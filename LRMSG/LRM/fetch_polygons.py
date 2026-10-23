import requests
import json
import time

zones = [
    {"name": "Darjeeling", "state": "West Bengal"},
    {"name": "East Sikkim", "state": "Sikkim"}, # Gangtok is in East Sikkim
    {"name": "East Khasi Hills", "state": "Meghalaya"}, # Shillong
    {"name": "Kohima", "state": "Nagaland"},
    {"name": "Aizawl", "state": "Mizoram"},
    {"name": "Papum Pare", "state": "Arunachal Pradesh"}, # Itanagar
    {"name": "Imphal West", "state": "Manipur"},
    {"name": "West Tripura", "state": "Tripura"}, # Agartala
    {"name": "Kamrup Metropolitan", "state": "Assam"}, # Guwahati
    {"name": "Champhai", "state": "Mizoram"},
    {"name": "Dhemaji", "state": "Assam"},
    {"name": "Lower Dibang Valley", "state": "Arunachal Pradesh"},
    {"name": "East Jaintia Hills", "state": "Meghalaya"},
    {"name": "West Kameng", "state": "Arunachal Pradesh"},
    {"name": "North Tripura", "state": "Tripura"},
]

features = []

for z in zones:
    print(f"Fetching {z['name']}, {z['state']}...")
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "county": z["name"],
        "state": z["state"],
        "country": "India",
        "polygon_geojson": 1,
        "format": "json"
    }
    headers = {"User-Agent": "LRM-App/1.0"}
    res = requests.get(url, params=params, headers=headers)
    data = res.json()
    if data:
        # Find the one that has geojson
        for item in data:
            if "geojson" in item and item["geojson"]["type"] in ["Polygon", "MultiPolygon"]:
                features.append({
                    "type": "Feature",
                    "properties": {"name": z["name"]},
                    "geometry": item["geojson"]
                })
                break
    time.sleep(1.5) # Respect Nominatim rate limits

geojson = {
    "type": "FeatureCollection",
    "features": features
}

with open("c:/Users/bubub/Downloads/LRMSG/LRM/frontend/public/ner_districts.json", "w") as f:
    json.dump(geojson, f)

print(f"Saved {len(features)} polygons.")
