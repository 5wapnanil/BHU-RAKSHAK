import json
import math
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Query, BackgroundTasks
from backend.app.services.alert_engine import alert_engine
import asyncio

# from backend.app.model.prediction_service import predict_complete  # Disabled: Legacy ML model retired
from backend.app.services.feature_engineering import engineer_features

router = APIRouter(prefix="/api/risk-zones", tags=["risk-zones"])

STATIC_FEATURES_PATH = (
    Path(__file__).resolve().parents[4] / "frontend" / "src" / "mock" / "static_features.json"
)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

_CACHE_TTL = 300  # 5 minutes
_cached_ner_data: Optional[Dict[str, Any]] = None
_cached_ner_timestamp: float = 0


def _load_static_features() -> List[Dict[str, Any]]:
    if not STATIC_FEATURES_PATH.exists():
        return []
    with open(STATIC_FEATURES_PATH, "r") as f:
        return json.load(f)


def _get_unique_districts(zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for z in zones:
        key = (z["name"], z["state"])
        if key not in seen:
            seen.add(key)
            unique.append(z)
    return unique


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _risk_level(prob_pct: float) -> str:
    if prob_pct >= 95:
        return "CRITICAL"
    elif prob_pct >= 60:
        return "HIGH"
    elif prob_pct >= 30:
        return "MODERATE"
    return "LOW"


def _risk_color(level: str) -> str:
    return {
        "CRITICAL": "#C93D33",
        "HIGH": "#ea580c",
        "MODERATE": "#ca8a04",
        "LOW": "#3A803B",
    }.get(level, "#3A803B")


def _run_prediction_for_zone(zone: Dict[str, Any], rainfall: float, soil_moisture: float) -> Optional[Dict[str, Any]]:
    """Disabled: Legacy landslide prediction ML model has been retired and disabled."""
    return None
    # Preserved original implementation:
    # try:
    #     rzsm_1 = soil_moisture
    #     ...
    #     result = predict_complete(...)
    #     ...
    # except Exception as e:
    #     return None


def _fetch_weather_for_districts(districts: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    import requests as http_requests

    weather_map: Dict[str, Dict[str, float]] = {}
    batch_size = 50
    for i in range(0, len(districts), batch_size):
        batch = districts[i : i + batch_size]
        lats = ",".join(str(d["lat"]) for d in batch)
        lngs = ",".join(str(d["lng"]) for d in batch)
        try:
            resp = http_requests.get(
                OPEN_METEO_URL,
                params={
                    "latitude": lats,
                    "longitude": lngs,
                    "hourly": "precipitation,soil_moisture_0_to_7cm",
                    "past_hours": "72",
                    "forecast_hours": "1",
                },
                timeout=15,
            )
            if resp.ok:
                data = resp.json()
                for idx, district in enumerate(batch):
                    loc_data = data[idx] if isinstance(data, list) else data
                    precips = loc_data.get("hourly", {}).get("precipitation", [])
                    moistures = loc_data.get("hourly", {}).get("soil_moisture_0_to_7cm", [])
                    rainfall = sum(p or 0 for p in precips)
                    soil_moisture = moistures[-1] if moistures else 0.3
                    weather_map[district["name"]] = {
                        "rainfall": rainfall,
                        "soil_moisture": soil_moisture,
                    }
        except Exception as e:
            print(f"Weather fetch batch failed: {e}")
    return weather_map


def _build_ner_risk_data() -> Dict[str, Any]:
    global _cached_ner_data, _cached_ner_timestamp

    now = time.time()
    if _cached_ner_data and (now - _cached_ner_timestamp) < _CACHE_TTL:
        return _cached_ner_data

    zones = _load_static_features()
    if not zones:
        return {"zones": [], "summary": {}}

    unique_districts = _get_unique_districts(zones)
    weather_map = _fetch_weather_for_districts(unique_districts)

    results = []
    for district in unique_districts:
        weather = weather_map.get(district["name"], {"rainfall": 0, "soil_moisture": 0.3})
        pred = _run_prediction_for_zone(district, weather["rainfall"], weather["soil_moisture"])
        if pred:
            results.append(pred)
        else:
            # When legacy ML is retired, preserve non-ML static features and live weather observations
            # while explicitly indicating prediction unavailable
            results.append({
                "name": district["name"],
                "state": district["state"],
                "lat": district["lat"],
                "lng": district["lng"],
                "elevation": district.get("elevation"),
                "slope": district.get("slope"),
                "soil_type": district.get("soilType"),
                "risk_probability": None,
                "risk_level": "UNAVAILABLE",
                "risk_color": "#6B7280",
                "xgboost_probability": None,
                "ahc_susceptibility": None,
                "ahc_category": None,
                "ahc_cluster": None,
                "rainfall_mm": weather["rainfall"],
                "soil_moisture": round(weather["soil_moisture"] * 100, 1),
                "prediction_status": "UNAVAILABLE",
            })

    critical = [z for z in results if z.get("risk_level") == "CRITICAL"]
    high = [z for z in results if z.get("risk_level") == "HIGH"]
    moderate = [z for z in results if z.get("risk_level") == "MODERATE"]
    unavailable = [z for z in results if z.get("risk_level") == "UNAVAILABLE"]

    try:
        loop = asyncio.get_running_loop()
        for z in results:
            if z.get("risk_probability") is not None and z["risk_probability"] >= 30.0:  # Only trigger if MODERATE or above
                loop.create_task(alert_engine.evaluate_prediction(
                    location_id=f"loc_{z['lat']}_{z['lng']}",
                    location_name=z['name'],
                    district=z['name'],
                    state=z['state'],
                    lat=z['lat'],
                    lng=z['lng'],
                    probability=z['risk_probability'] / 100.0,
                    rainfall=z['rainfall_mm'],
                    soil=z['soil_moisture'] / 100.0,
                    slope=z['slope']
                ))
    except RuntimeError:
        pass
    except Exception as e:
        print("Could not trigger alerts", e)

    data = {
        "prediction_status": "UNAVAILABLE",
        "prediction_message": "The legacy landslide prediction ML model has been retired and disabled.",
        "zones": results,
        "summary": {
            "total": len(results),
            "critical_count": len(critical),
            "high_count": len(high),
            "moderate_count": len(moderate),
            "low_count": len([z for z in results if z.get("risk_level") == "LOW"]),
            "unavailable_count": len(unavailable),
            "critical_zones": [
                {"name": z["name"], "state": z["state"], "risk_probability": z["risk_probability"]}
                for z in sorted(critical, key=lambda x: -(x.get("risk_probability") or 0))
            ],
            "high_zones": [
                {"name": z["name"], "state": z["state"], "risk_probability": z["risk_probability"]}
                for z in sorted(high, key=lambda x: -(x.get("risk_probability") or 0))
            ],
        },
        "risk_grading": {
            "CRITICAL": {"threshold": ">=95%", "color": "#C93D33", "label": "VERY HIGH / CRITICAL"},
            "HIGH": {"threshold": "60-94%", "color": "#ea580c", "label": "HIGH / WARNING"},
            "MODERATE": {"threshold": "30-59%", "color": "#ca8a04", "label": "MODERATE / WATCH"},
            "LOW": {"threshold": "<30%", "color": "#3A803B", "label": "LOW / NORMAL"},
            "UNAVAILABLE": {"threshold": "N/A", "color": "#6B7280", "label": "PREDICTION RETIRED / UNAVAILABLE"},
        },
    }

    _cached_ner_data = data
    _cached_ner_timestamp = now
    return data


@router.get("/ner-risk-data")
def get_ner_risk_data(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    data = _build_ner_risk_data()
    background_tasks.add_task(_trigger_alerts_background, data.get("zones", []))
    return data


def _trigger_alerts_background(results):
    import asyncio
    async def _do_trigger():
        for z in results:
            if z.get("risk_probability") is not None and z["risk_probability"] >= 30.0:
                await alert_engine.evaluate_prediction(
                    location_id=f"loc_{z['lat']}_{z['lng']}",
                    location_name=z['name'], district=z['name'], state=z['state'],
                    lat=z['lat'], lng=z['lng'], probability=z['risk_probability']/100.0,
                    rainfall=z['rainfall_mm'], soil=z['soil_moisture']/100.0, slope=z['slope']
                )
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do_trigger())
    except RuntimeError:
        asyncio.run(_do_trigger())

@router.get("/nearby")
def get_nearby_risk(
    background_tasks: BackgroundTasks,
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(default=150.0, description="Search radius in km"),
) -> Dict[str, Any]:
    ner_data = _build_ner_risk_data()
    all_zones = ner_data.get("zones", [])

    for z in all_zones:
        z["distance_km"] = round(_haversine_km(lat, lng, z["lat"], z["lng"]), 1)

    nearby = sorted(
        [z for z in all_zones if z["distance_km"] <= radius_km],
        key=lambda x: x["distance_km"],
    )

    high_risk_ner = sorted(
        [z for z in all_zones if z.get("risk_level") in ("CRITICAL", "HIGH")],
        key=lambda x: -(x.get("risk_probability") or 0),
    )

    user_zone = nearby[0] if nearby else None
    background_tasks.add_task(_trigger_alerts_background, all_zones)
    return {
        "prediction_status": "UNAVAILABLE",
        "prediction_message": "The legacy landslide prediction ML model has been retired and disabled.",
        "user_location": {"lat": lat, "lng": lng},
        "user_zone": user_zone,
        "nearby_zones": nearby[:10],
        "high_risk_ner": [
            {
                "name": z["name"],
                "state": z["state"],
                "lat": z["lat"],
                "lng": z["lng"],
                "risk_probability": z.get("risk_probability"),
                "risk_level": z.get("risk_level"),
                "risk_color": z.get("risk_color"),
                "distance_km": z.get("distance_km"),
                "rainfall_mm": z.get("rainfall_mm"),
                "ahc_category": z.get("ahc_category"),
                "prediction_status": z.get("prediction_status"),
            }
            for z in high_risk_ner[:20]
        ],
        "summary": {
            "total_zones_evaluated": len(all_zones),
            "critical_count": len([z for z in all_zones if z.get("risk_level") == "CRITICAL"]),
            "high_count": len([z for z in all_zones if z.get("risk_level") == "HIGH"]),
            "moderate_count": len([z for z in all_zones if z.get("risk_level") == "MODERATE"]),
            "low_count": len([z for z in all_zones if z.get("risk_level") == "LOW"]),
            "unavailable_count": len([z for z in all_zones if z.get("risk_level") == "UNAVAILABLE"]),
        },
        "risk_grading": ner_data.get("risk_grading", {}),
    }
