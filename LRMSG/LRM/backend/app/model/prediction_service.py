from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from backend.app.model.model_loader import load_all_models
from final_calibration import calibrated_final_result


# ============================================================
# LAZY MODEL LOADING
# Models are loaded on first prediction request, not at import.
# This prevents ML dependency failures from blocking FastAPI startup.
# ============================================================

DISABLED_MSG = "Legacy landslide prediction ML models have been retired and disabled."

_models_cache: Optional[Dict[str, Any]] = None
_ml_unavailable_error: Optional[Exception] = None


def _get_models() -> Dict[str, Any]:
    """Disabled: Legacy ML models are retired and not loaded into memory."""
    # Preserved original implementation:
    # global _models_cache, _ml_unavailable_error
    # if _models_cache is not None:
    #     return _models_cache
    # if _ml_unavailable_error is not None:
    #     raise _ml_unavailable_error
    # try:
    #     _models_cache = load_all_models()
    #     return _models_cache
    # except Exception as e:
    #     _ml_unavailable_error = e
    #     raise
    raise RuntimeError(DISABLED_MSG)


def _get_xgboost_model():
    return _get_models()["xgboost"]


def _get_ahc_model():
    return _get_models()["ahc"]


def _get_decision_model():
    return _get_models()["decision"]


def _get_ahc_metadata():
    ahc = _get_ahc_model()
    return ahc["cluster_susceptibility"], ahc["cluster_categories"]


# ============================================================
# XGBOOST FEATURE ORDER
# MUST MATCH THE FROZEN MODEL EXACTLY
# ============================================================

XGBOOST_FEATURES = [
    "rzsm_1",
    "rzsm_2",
    "rzsm_3",
    "cumulative_rainfall_3d_mm",
    "_rzsm_mean_",
    "_rzsm_range_",
    "_rzsm_surface_deep_diff_",
    "_rain_rzsm_interaction_",
    "_previous_rzsm_",
    "_previous_rzsm_2_",
    "_previous_rzsm_3_",
    "_previous_rainfall_",
]


# ============================================================
# AHC FEATURE DEFINITIONS
# TAKEN FROM THE FROZEN AHC ARTIFACT
# ============================================================

AHC_NUMERICAL_FEATURES = [
    "cumulative_rainfall_3d_mm",
    "rzsm_0_100",
    "elevation_m",
    "slope_deg",
]

AHC_SOIL_CATEGORIES = [
    "Acrisols",
    "Cambisols",
    "Fluvisols",
    "Leptosols",
    "Luvisols",
    "Vertisols",
]


# ============================================================
# AHC STORED METADATA (lazy — loaded on first prediction)
# ============================================================

AHC_CLUSTER_SUSCEPTIBILITY = None
AHC_CLUSTER_CATEGORIES = None


def _ensure_ahc_metadata():
    global AHC_CLUSTER_SUSCEPTIBILITY, AHC_CLUSTER_CATEGORIES
    if AHC_CLUSTER_SUSCEPTIBILITY is None:
        AHC_CLUSTER_SUSCEPTIBILITY, AHC_CLUSTER_CATEGORIES = _get_ahc_metadata()


# ============================================================
# AHC PREDICTION
# ============================================================

def predict_ahc(
    cumulative_rainfall_3d_mm: float,
    rzsm_0_100: float,
    elevation_m: float,
    slope_deg: float,
    soil_type_wrb: str,
) -> Dict[str, Any]:
    """Disabled: Legacy AHC model inference is retired."""
    raise RuntimeError(DISABLED_MSG)
    # Preserved original implementation:
    # _ensure_ahc_metadata()
    # ahc = _get_ahc_model()

    # --------------------------------------------------------
    # Validate soil category
    # --------------------------------------------------------

    if soil_type_wrb not in AHC_SOIL_CATEGORIES:
        raise ValueError(
            f"Unsupported soil type '{soil_type_wrb}'. "
            f"Expected one of: {AHC_SOIL_CATEGORIES}"
        )

    # --------------------------------------------------------
    # Build numerical AHC input WITH FEATURE NAMES
    # This avoids sklearn feature-name warnings.
    # --------------------------------------------------------

    numerical_df = pd.DataFrame(
        [[
            cumulative_rainfall_3d_mm,
            rzsm_0_100,
            elevation_m,
            slope_deg,
        ]],
        columns=AHC_NUMERICAL_FEATURES,
    )

    # --------------------------------------------------------
    # Apply the EXACT frozen numerical scaler
    # --------------------------------------------------------

    numerical_scaled = ahc["scaler"].transform(
        numerical_df
    )

    # --------------------------------------------------------
    # Encode soil using the EXACT frozen encoder
    # --------------------------------------------------------

    soil_df = pd.DataFrame(
        {"soil_type_wrb": [soil_type_wrb]}
    )

    soil_encoded = ahc["soil_encoder"].transform(
        soil_df[["soil_type_wrb"]]
    )

    if hasattr(soil_encoded, "toarray"):
        soil_encoded = soil_encoded.toarray()

    # --------------------------------------------------------
    # Combine numerical + soil features
    # --------------------------------------------------------

    ahc_input = np.hstack(
        [
            numerical_scaled,
            soil_encoded,
        ]
    )[0]

    # --------------------------------------------------------
    # Read frozen cluster centroids
    #
    # The artifact stores these as a pandas DataFrame.
    # Therefore we iterate over rows, NOT .items().
    # --------------------------------------------------------

    centroids = ahc["cluster_centroids"]

    if isinstance(centroids, pd.DataFrame):

        distances = {}

        for cluster, centroid in centroids.iterrows():

            # Cluster index may be stored as int, numpy int,
            # or another numeric representation.
            cluster_id = int(cluster)

            centroid_array = np.asarray(
                centroid,
                dtype=float,
            )

            distances[cluster_id] = float(
                np.linalg.norm(
                    ahc_input - centroid_array
                )
            )

    else:

        centroid_array = np.asarray(
            centroids,
            dtype=float,
        )

        distances = {
            int(cluster): float(
                np.linalg.norm(
                    ahc_input - centroid
                )
            )
            for cluster, centroid in enumerate(
                centroid_array
            )
        }

    # --------------------------------------------------------
    # Select nearest frozen cluster
    # --------------------------------------------------------

    cluster = min(
        distances,
        key=distances.get,
    )

    # --------------------------------------------------------
    # Retrieve frozen susceptibility + category
    # --------------------------------------------------------

    susceptibility = float(
        AHC_CLUSTER_SUSCEPTIBILITY[cluster]
    )

    category = str(
        AHC_CLUSTER_CATEGORIES[cluster]
    )

    # --------------------------------------------------------
    # Return AHC result
    # --------------------------------------------------------

    return {
        "cluster": int(cluster),
        "susceptibility": susceptibility,
        "category": category,
        "distance_to_centroid": distances,
    }


# ============================================================
# COMPLETE THREE-LAYER PREDICTION
# ============================================================

def predict_complete(
    *,
    rzsm_1: float,
    rzsm_2: float,
    rzsm_3: float,
    cumulative_rainfall_3d_mm: float,
    rzsm_mean: float,
    rzsm_range: float,
    rzsm_surface_deep_diff: float,
    rain_rzsm_interaction: float,
    previous_rzsm: float,
    previous_rzsm_2: float,
    previous_rzsm_3: float,
    previous_rainfall: float,
    rzsm_0_100: float,
    elevation_m: float,
    slope_deg: float,
    soil_type_wrb: str,
) -> Dict[str, Any]:
    """Disabled: Legacy landslide prediction inference is retired."""
    raise RuntimeError(DISABLED_MSG)

    # Preserved original implementation:
    # ========================================================
    # LAYER 1 — FROZEN XGBOOST
    # ========================================================

    xgb_vector = [
        rzsm_1,
        rzsm_2,
        rzsm_3,
        cumulative_rainfall_3d_mm,
        rzsm_mean,
        rzsm_range,
        rzsm_surface_deep_diff,
        rain_rzsm_interaction,
        previous_rzsm,
        previous_rzsm_2,
        previous_rzsm_3,
        previous_rainfall,
    ]

    print("\n========== XGBOOST LIVE INPUT ==========")
    for name, value in zip(XGBOOST_FEATURES, xgb_vector):
        print(f"{name:35s} = {value}")
    print("========================================\n")

    xgb_input = pd.DataFrame([xgb_vector], columns=XGBOOST_FEATURES)

    xgb = _get_xgboost_model()

    # XGBoost natively supports NaN in these features.
    xgb_probability = float(
        xgb.predict_proba(
            xgb_input
        )[0, 1]
    )
    
    print("XGBoost probability =", xgb_probability)

    xgb_prediction = int(
        xgb.predict(
            xgb_input
        )[0]
    )

    # ========================================================
    # LAYER 2 — FROZEN AHC
    # ========================================================

    print("\n========== AHC LIVE INPUT ==========")
    print("cumulative_rainfall_3d_mm =", cumulative_rainfall_3d_mm)
    print("rzsm_0_100                =", rzsm_0_100)
    print("elevation                 =", elevation_m)
    print("slope                     =", slope_deg)
    print("soil_type                 =", soil_type_wrb)
    print("====================================\n")

    ahc_result = predict_ahc(
        cumulative_rainfall_3d_mm=(
            cumulative_rainfall_3d_mm
        ),
        rzsm_0_100=rzsm_0_100,
        elevation_m=elevation_m,
        slope_deg=slope_deg,
        soil_type_wrb=soil_type_wrb,
    )

    ahc_cluster = ahc_result["cluster"]
    ahc_susceptibility = ahc_result["susceptibility"]
    ahc_category = ahc_result["category"]

    print("========== AHC OUTPUT ==========")
    print("AHC cluster =", ahc_cluster)
    print("AHC susceptibility =", ahc_susceptibility)
    print("AHC category =", ahc_category)
    print("================================\n")

    # ========================================================
    # LAYER 3 — FROZEN SPATIAL DECISION MODEL
    # ========================================================

    print("========== DECISION LAYER INPUT ==========")
    print("XGB probability       =", xgb_probability)
    print("AHC susceptibility    =", ahc_susceptibility)
    print("AHC cluster           =", ahc_cluster)
    print("AHC category          =", ahc_category)
    print("==========================================\n")

    # Decision Layer
    decision_input = pd.DataFrame(
        [[
            xgb_probability,
            ahc_susceptibility,
            ahc_cluster,
            ahc_category,
        ]],
        columns=[
            "xgb_spatial_oof_probability",
            "ahc_susceptibility",
            "ahc_cluster",
            "ahc_category",
        ],
    )
    
    # Apply Prototype Threshold = 0.60
    decision = _get_decision_model()
    final_probability = float(decision.predict_proba(decision_input)[0, 1])
    final_prediction = 1 if final_probability >= 0.60 else 0

    # ============================================================
    # OPTION B — FINAL OUTPUT CALIBRATION
    # ============================================================

    raw_final_probability = float(
        final_probability
    )

    final_calibration = calibrated_final_result(raw_final_probability)

    calibrated_final_probability = (
        final_calibration["calibrated_probability"]
    )

    print("========== FINAL RESULT ==========")
    print("XGBoost probability =", xgb_probability)
    print("AHC susceptibility  =", ahc_susceptibility)
    print("AHC cluster         =", ahc_cluster)
    print("AHC category        =", ahc_category)
    print("FINAL probability   =", final_probability)
    print("CALIBRATED probability =", calibrated_final_probability)
    print("==================================\n")

    from xgb_calibration import calibrated_xgb_result
    xgb_calibration_data = calibrated_xgb_result(xgb_probability)

    return {
        "xgboost": {
            "raw_probability": xgb_probability,
            "calibrated_probability": xgb_calibration_data["calibrated_probability"],
            "prediction": 1 if xgb_probability > 0.5 else 0,
            "calibration": xgb_calibration_data["calibration"]
        },
        "ahc": {
            "cluster": ahc_cluster,
            "susceptibility": ahc_susceptibility,
            "category": ahc_category,
        },
        "final_decision": {
            "raw_probability": raw_final_probability,
            "calibrated_probability": calibrated_final_probability,
            "prediction": final_prediction,
            "calibration": final_calibration["calibration"]
        }
    }