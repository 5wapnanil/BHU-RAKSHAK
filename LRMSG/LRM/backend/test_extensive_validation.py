from __future__ import annotations

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
import json
import math
from datetime import datetime, timezone

import numpy as np

from backend.app.services.open_meteo_service import (
    fetch_current_environment,
)
from backend.app.services.feature_engineering import (
    engineer_features,
)
from backend.app.services.soilgrids_service import (
    fetch_wrb_soil,
)
from backend.app.services.opentopo_service import (
    fetch_terrain,
)
from backend.app.model.prediction_service import (
    predict_complete,
)


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_JSON = "extensive_validation_results.json"
OUTPUT_CSV = "extensive_validation_summary.csv"

# Change this only if your training CSV is stored elsewhere.
TRAINING_CSV = (
    "Landslide_NER_MASTER_2016_ROWS_WITH_XGBOOST_FEATURES(4).csv"
)


XGB_FEATURES = [
    "rzsm_1",
    "rzsm_2",
    "rzsm_3",
    "cumulative_rainfall_3d_mm",
    "rzsm_mean",
    "rzsm_range",
    "rzsm_surface_deep_diff",
    "rain_rzsm_interaction",
    "previous_rzsm",
    "previous_rzsm_2",
    "previous_rzsm_3",
    "previous_rainfall",
]


TEST_LOCATIONS = [
    {
        "name": "Chandmari, Gangtok",
        "latitude": 27.338483,
        "longitude": 88.623217,
        "known_landslide": True,
    },
    {
        "name": "Indira Bye Pass, Gangtok",
        "latitude": 27.328889,
        "longitude": 88.607778,
        "known_landslide": True,
    },
    {
        "name": "Darjeeling",
        "latitude": 27.041000,
        "longitude": 88.266300,
        "known_landslide": True,
    },
    {
        "name": "Gangtok Control",
        "latitude": 27.331400,
        "longitude": 88.613800,
        "known_landslide": False,
    },
    {
        "name": "Darjeeling Control",
        "latitude": 27.050000,
        "longitude": 88.250000,
        "known_landslide": False,
    },
    {
        "name": "Siliguri Control",
        "latitude": 26.727100,
        "longitude": 88.395300,
        "known_landslide": False,
    },
    {
        "name": "Shillong",
        "latitude": 25.578800,
        "longitude": 91.893300,
        "known_landslide": False,
    },
    {
        "name": "Guwahati",
        "latitude": 26.144500,
        "longitude": 91.736200,
        "known_landslide": False,
    },
]


# ============================================================
# HELPERS
# ============================================================

def finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def sigmoid(x):
    x = max(min(float(x), 700.0), -700.0)
    return 1.0 / (1.0 + math.exp(-x))


def probability_to_logit(p):
    p = min(max(float(p), 1e-15), 1 - 1e-15)
    return math.log(p / (1.0 - p))


def load_training_data():

    if not os.path.exists(TRAINING_CSV):
        print(
            f"\nWARNING: Training CSV not found: "
            f"{TRAINING_CSV}"
        )
        print(
            "Training-distribution comparison will be skipped."
        )
        return None

    import pandas as pd

    df = pd.read_csv(TRAINING_CSV)

    print("\nTraining dataset loaded:")
    print(f"Rows: {len(df)}")

    return df


def find_training_column(df, feature):

    candidates = [
        feature,
        f"_{feature}_",
    ]

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    return None


def calculate_training_statistics(df):

    if df is None:
        return {}

    statistics = {}

    for feature in XGB_FEATURES:

        column = find_training_column(df, feature)

        if column is None:
            continue

        values = (
            df[column]
            .replace([np.inf, -np.inf], np.nan)
            .dropna()
        )

        if len(values) == 0:
            continue

        statistics[feature] = {
            "column": column,
            "count": int(len(values)),
            "min": float(values.min()),
            "p01": float(values.quantile(0.01)),
            "p05": float(values.quantile(0.05)),
            "p25": float(values.quantile(0.25)),
            "median": float(values.median()),
            "p75": float(values.quantile(0.75)),
            "p95": float(values.quantile(0.95)),
            "p99": float(values.quantile(0.99)),
            "max": float(values.max()),
            "mean": float(values.mean()),
            "std": float(values.std()),
        }

    return statistics


def assess_feature_distribution(
    feature,
    value,
    training_statistics,
):

    stats = training_statistics.get(feature)

    if stats is None:
        return "NO_TRAINING_REFERENCE"

    value = float(value)

    if value < stats["min"] or value > stats["max"]:
        return "OUTSIDE_TRAINING_MIN_MAX"

    if value < stats["p01"] or value > stats["p99"]:
        return "EXTREME_1_99_PERCENTILE"

    if value < stats["p05"] or value > stats["p95"]:
        return "EXTREME_5_95_PERCENTILE"

    return "IN_TRAINING_RANGE"


# ============================================================
# ONE LOCATION
# ============================================================

def test_location(location, training_statistics):

    name = location["name"]
    lat = location["latitude"]
    lon = location["longitude"]

    print("\n")
    print("=" * 90)
    print(f"TESTING: {name}")
    print(f"Coordinates: {lat}, {lon}")
    print("=" * 90)

    env = fetch_current_environment(lat, lon)

    soil = fetch_wrb_soil(lat, lon)

    terrain = fetch_terrain(lat, lon)

    features = engineer_features(
        rzsm_1=env["rzsm_1"],
        rzsm_2=env["rzsm_2"],
        rzsm_3=env["rzsm_3"],
        cumulative_rainfall_3d_mm=
            env["cumulative_rainfall_3d_mm"],
        previous=env["previous"],
        previous_rainfall=
            env["previous_rainfall"],
    )

    # --------------------------------------------------------
    # EXACT 12-FEATURE VECTOR
    # --------------------------------------------------------

    feature_vector = {
        "rzsm_1": env["rzsm_1"],
        "rzsm_2": env["rzsm_2"],
        "rzsm_3": env["rzsm_3"],

        "cumulative_rainfall_3d_mm":
            env["cumulative_rainfall_3d_mm"],

        "rzsm_mean":
            features["rzsm_mean"],

        "rzsm_range":
            features["rzsm_range"],

        "rzsm_surface_deep_diff":
            features["rzsm_surface_deep_diff"],

        "rain_rzsm_interaction":
            features["rain_rzsm_interaction"],

        "previous_rzsm":
            features["previous_rzsm"],

        "previous_rzsm_2":
            features["previous_rzsm_2"],

        "previous_rzsm_3":
            features["previous_rzsm_3"],

        "previous_rainfall":
            features["previous_rainfall"],
    }

    # --------------------------------------------------------
    # FEATURE INTEGRITY
    # --------------------------------------------------------

    feature_integrity = {}

    for feature in XGB_FEATURES:

        value = feature_vector[feature]

        feature_integrity[feature] = {
            "value": float(value),
            "finite": finite(value),
            "training_status":
                assess_feature_distribution(
                    feature,
                    value,
                    training_statistics,
                ),
        }

    invalid_features = [
        feature
        for feature, data in feature_integrity.items()
        if not data["finite"]
    ]

    if invalid_features:

        raise RuntimeError(
            f"Invalid XGBoost features: {invalid_features}"
        )

    # --------------------------------------------------------
    # TEMPORAL AUDIT
    # --------------------------------------------------------

    previous = env["previous"]

    temporal_audit = {
        "D_minus_1_surface":
            previous[0]["rzsm_1"],
        "D_minus_2_surface":
            previous[1]["rzsm_1"],
        "D_minus_3_surface":
            previous[2]["rzsm_1"],
        "previous_rainfall":
            env["previous_rainfall"],
    }

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    result = predict_complete(
        rzsm_1=env["rzsm_1"],
        rzsm_2=env["rzsm_2"],
        rzsm_3=env["rzsm_3"],

        cumulative_rainfall_3d_mm=
            env["cumulative_rainfall_3d_mm"],

        rzsm_mean=features["rzsm_mean"],
        rzsm_range=features["rzsm_range"],

        rzsm_surface_deep_diff=
            features["rzsm_surface_deep_diff"],

        rain_rzsm_interaction=
            features["rain_rzsm_interaction"],

        previous_rzsm=
            features["previous_rzsm"],

        previous_rzsm_2=
            features["previous_rzsm_2"],

        previous_rzsm_3=
            features["previous_rzsm_3"],

        previous_rainfall=
            features["previous_rainfall"],

        rzsm_0_100=
            features["rzsm_0_100"],

        elevation_m=terrain["elevation_m"],
        slope_deg=terrain["slope_deg"],
        soil_type_wrb=soil["soil_type_wrb"],
    )

    xgb_probability = float(
        result["xgboost"]["probability"]
    )

    final_probability = float(
        result["final_decision"]["probability"]
    )

    xgb_logit = probability_to_logit(
        xgb_probability
    )

    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    print("\n---------- TEMPORAL FEATURES ----------")

    print(
        "D-1 surface RZSM       =",
        temporal_audit["D_minus_1_surface"],
    )

    print(
        "D-2 surface RZSM       =",
        temporal_audit["D_minus_2_surface"],
    )

    print(
        "D-3 surface RZSM       =",
        temporal_audit["D_minus_3_surface"],
    )

    print(
        "D-1 3-day rainfall     =",
        temporal_audit["previous_rainfall"],
    )

    print("\n---------- 12 XGB FEATURES ----------")

    for feature in XGB_FEATURES:
        print(
            f"{feature:35s} = "
            f"{feature_vector[feature]}"
        )

    print("\n---------- DISTRIBUTION CHECK ----------")

    for feature in XGB_FEATURES:

        data = feature_integrity[feature]

        print(
            f"{feature:35s} = "
            f"{data['training_status']}"
        )

    print("\n---------- ENVIRONMENT ----------")

    print(
        "Timestamp                 =",
        env["timestamp_utc"],
    )

    print(
        "Current 3-day rainfall    =",
        env["cumulative_rainfall_3d_mm"],
    )

    print(
        "RZSM 0-100                =",
        features["rzsm_0_100"],
    )

    print("\n---------- TERRAIN / SOIL ----------")

    print(
        "Elevation                 =",
        terrain["elevation_m"],
    )

    print(
        "Slope                     =",
        terrain["slope_deg"],
    )

    print(
        "Soil                      =",
        soil["soil_type_wrb"],
    )

    print("\n---------- MODEL ----------")

    print(
        "XGBoost probability       =",
        xgb_probability,
    )

    print(
        "XGBoost logit             =",
        xgb_logit,
    )

    print(
        "AHC cluster               =",
        result["ahc"]["cluster"],
    )

    print(
        "AHC susceptibility        =",
        result["ahc"]["susceptibility"],
    )

    print(
        "AHC category              =",
        result["ahc"]["category"],
    )

    print(
        "FINAL probability         =",
        final_probability,
    )

    print(
        "FINAL prediction          =",
        result["final_decision"]["prediction"],
    )

    return {
        "location": location,
        "timestamp_utc": env["timestamp_utc"],

        "environment": {
            "rzsm_1": env["rzsm_1"],
            "rzsm_2": env["rzsm_2"],
            "rzsm_3": env["rzsm_3"],
            "current_rainfall_3d":
                env["cumulative_rainfall_3d_mm"],
            "previous_rainfall_3d":
                env["previous_rainfall"],
        },

        "temporal_audit": temporal_audit,

        "features": feature_vector,

        "feature_integrity":
            feature_integrity,

        "terrain": terrain,

        "soil": soil,

        "model": {
            "xgb_probability":
                xgb_probability,

            "xgb_logit":
                xgb_logit,

            "xgb_prediction":
                result["xgboost"]["prediction"],

            "ahc_cluster":
                result["ahc"]["cluster"],

            "ahc_susceptibility":
                result["ahc"]["susceptibility"],

            "ahc_category":
                result["ahc"]["category"],

            "final_probability":
                final_probability,

            "final_prediction":
                result["final_decision"]["prediction"],
        },
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("#" * 90)
    print("# EXTENSIVE CORRECTED PIPELINE VALIDATION")
    print("#" * 90)

    training_df = load_training_data()

    training_statistics = (
        calculate_training_statistics(training_df)
    )

    results = []

    for location in TEST_LOCATIONS:

        try:

            result = test_location(
                location,
                training_statistics,
            )

            results.append(result)

        except Exception as exc:

            print("\n!!! LOCATION FAILED !!!")
            print(location["name"])
            print(type(exc).__name__)
            print(str(exc))

            results.append({
                "location": location,
                "error": type(exc).__name__,
                "message": str(exc),
            })

    # ========================================================
    # SAVE JSON
    # ========================================================

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # SUMMARY CSV
    # ========================================================

    rows = []

    for result in results:

        if "error" in result:

            rows.append({
                "location":
                    result["location"]["name"],
                "error":
                    result["message"],
            })

            continue

        rows.append({
            "location":
                result["location"]["name"],

            "latitude":
                result["location"]["latitude"],

            "longitude":
                result["location"]["longitude"],

            "known_landslide":
                result["location"]["known_landslide"],

            "rainfall_3d":
                result["environment"]
                ["current_rainfall_3d"],

            "rzsm_1":
                result["features"]["rzsm_1"],

            "rzsm_mean":
                result["features"]["rzsm_mean"],

            "previous_rzsm":
                result["features"]["previous_rzsm"],

            "previous_rzsm_2":
                result["features"]["previous_rzsm_2"],

            "previous_rzsm_3":
                result["features"]["previous_rzsm_3"],

            "previous_rainfall":
                result["features"]["previous_rainfall"],

            "xgb_probability":
                result["model"]["xgb_probability"],

            "xgb_logit":
                result["model"]["xgb_logit"],

            "ahc_cluster":
                result["model"]["ahc_cluster"],

            "ahc_susceptibility":
                result["model"]["ahc_susceptibility"],

            "ahc_category":
                result["model"]["ahc_category"],

            "final_probability":
                result["model"]["final_probability"],

            "final_prediction":
                result["model"]["final_prediction"],
        })

    if rows:

        fieldnames = list(rows[0].keys())

        with open(
            OUTPUT_CSV,
            "w",
            newline="",
            encoding="utf-8",
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
            )

            writer.writeheader()
            writer.writerows(rows)

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")
    print("#" * 90)
    print("# FINAL SUMMARY")
    print("#" * 90)

    print(
        f"{'Location':30s}"
        f"{'Rain':>10s}"
        f"{'XGB':>12s}"
        f"{'AHC':>12s}"
        f"{'Final':>12s}"
    )

    print("-" * 90)

    for result in results:

        if "error" in result:

            print(
                f"{result['location']['name']:30s}"
                f"FAILED"
            )
            continue

        name = result["location"]["name"]

        rain = result["environment"][
            "current_rainfall_3d"
        ]

        xgb = result["model"]["xgb_probability"]

        ahc = result["model"]["ahc_susceptibility"]

        final = result["model"]["final_probability"]

        print(
            f"{name:30s}"
            f"{rain:10.2f}"
            f"{xgb * 100:11.2f}%"
            f"{ahc:11.2f}"
            f"{final * 100:11.2f}%"
        )

    print("\n")
    print("Saved:")
    print(f"  {OUTPUT_JSON}")
    print(f"  {OUTPUT_CSV}")
    print("#" * 90)


if __name__ == "__main__":
    main()
