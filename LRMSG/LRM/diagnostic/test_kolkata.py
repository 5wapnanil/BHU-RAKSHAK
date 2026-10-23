import requests
import json

# ============================================================
# KOLKATA LIVE LOCATION TEST
# ============================================================

LATITUDE = 22.5726
LONGITUDE = 88.3639

# Change this ONLY if your FastAPI server uses another port.
API_URL = "http://127.0.0.1:8002/prediction/location"


print("=" * 80)
print("KOLKATA LIVE LOCATION TEST")
print("=" * 80)

print(f"Latitude : {LATITUDE}")
print(f"Longitude: {LONGITUDE}")
print(f"Endpoint : {API_URL}")

payload = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE
}

try:

    response = requests.post(
        API_URL,
        json=payload,
        timeout=120
    )

    print("\nHTTP STATUS:", response.status_code)

    response.raise_for_status()

    data = response.json()

    print("\n" + "=" * 80)
    print("RAW API RESPONSE")
    print("=" * 80)

    print(json.dumps(data, indent=2))

    # ========================================================
    # IMPORTANT VALUES
    # ========================================================

    print("\n" + "=" * 80)
    print("KOLKATA SUMMARY")
    print("=" * 80)

    def get_value(obj, *keys):
        """
        Safely search for a value using multiple possible key names.
        """
        if not isinstance(obj, dict):
            return None

        for key in keys:
            if key in obj:
                return obj[key]

        return None

    # Try common names used by our API
    xgb_probability = get_value(
        data,
        "xgb_probability",
        "xgboost_probability",
        "xgb_event_probability"
    )

    final_probability = get_value(
        data,
        "final_probability",
        "final_risk_probability",
        "risk_probability"
    )

    xgb_margin = get_value(
        data,
        "xgb_margin",
        "xgb_logit",
        "xgb_raw_margin"
    )

    ahc_cluster = get_value(
        data,
        "ahc_cluster",
        "cluster"
    )

    ahc_susceptibility = get_value(
        data,
        "ahc_susceptibility",
        "susceptibility"
    )

    prediction = get_value(
        data,
        "final_prediction",
        "prediction",
        "risk_prediction"
    )

    print(f"XGB probability       : {xgb_probability}")
    print(f"XGB margin             : {xgb_margin}")
    print(f"AHC cluster            : {ahc_cluster}")
    print(f"AHC susceptibility     : {ahc_susceptibility}")
    print(f"Final probability      : {final_probability}")
    print(f"Final prediction       : {prediction}")

    # ========================================================
    # SEARCH FOR TEMPORAL FEATURES
    # ========================================================

    print("\n" + "=" * 80)
    print("TEMPORAL / RZSM FEATURES")
    print("=" * 80)

    feature_names = [
        "rzsm_1",
        "rzsm_2",
        "rzsm_3",
        "_rzsm_mean_",
        "_rzsm_range_",
        "_rzsm_surface_deep_diff_",
        "_rain_rzsm_interaction_",
        "_previous_rzsm_",
        "_previous_rzsm_2_",
        "_previous_rzsm_3_",
        "_previous_rainfall_",
        "cumulative_rainfall_3d_mm"
    ]

    def recursive_find(obj, target):
        """
        Recursively search the JSON response for a key.
        """
        if isinstance(obj, dict):

            if target in obj:
                return obj[target]

            for value in obj.values():
                result = recursive_find(value, target)

                if result is not None:
                    return result

        elif isinstance(obj, list):

            for item in obj:
                result = recursive_find(item, target)

                if result is not None:
                    return result

        return None

    for feature in feature_names:

        value = recursive_find(data, feature)

        print(f"{feature:35s}: {value}")

    print("\n" + "=" * 80)
    print("KOLKATA TEST COMPLETE")
    print("=" * 80)

except requests.exceptions.ConnectionError:

    print("\nERROR: Could not connect to FastAPI.")

    print(
        "\nMake sure your backend is running, for example:"
    )

    print(
        "uvicorn app.main:app --reload"
    )

except requests.exceptions.Timeout:

    print("\nERROR: API request timed out.")

except requests.exceptions.HTTPError as e:

    print("\nHTTP ERROR:")
    print(e)

    try:
        print(response.text)
    except Exception:
        pass

except Exception as e:

    print("\nUNEXPECTED ERROR:")
    print(type(e).__name__, e)
