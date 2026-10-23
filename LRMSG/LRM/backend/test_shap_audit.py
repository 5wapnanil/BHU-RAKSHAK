import sys
import os
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb

from backend.app.model.model_loader import load_all_models

# ============================================================
# FROZEN XGBOOST FEATURE CONTRIBUTION / SHAP AUDIT
# ============================================================

FEATURES = [
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

# ------------------------------------------------------------
# LOAD FROZEN MODEL
# ------------------------------------------------------------

models = load_all_models()
model = models["xgboost"]

# ------------------------------------------------------------
# LOAD LIVE VALIDATION VECTORS
# ------------------------------------------------------------
RESULTS_JSON = Path("extensive_validation_results.json")
rows = []

if RESULTS_JSON.exists():
    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        for entry in data:
            if "error" in entry:
                continue
            name = entry["location"]["name"]
            feat_dict = entry["features"]
            row = {"location": name}
            row["rzsm_1"] = feat_dict["rzsm_1"]
            row["rzsm_2"] = feat_dict["rzsm_2"]
            row["rzsm_3"] = feat_dict["rzsm_3"]
            row["cumulative_rainfall_3d_mm"] = feat_dict["cumulative_rainfall_3d_mm"]
            row["_rzsm_mean_"] = feat_dict["rzsm_mean"]
            row["_rzsm_range_"] = feat_dict["rzsm_range"]
            row["_rzsm_surface_deep_diff_"] = feat_dict["rzsm_surface_deep_diff"]
            row["_rain_rzsm_interaction_"] = feat_dict["rain_rzsm_interaction"]
            row["_previous_rzsm_"] = feat_dict["previous_rzsm"]
            row["_previous_rzsm_2_"] = feat_dict["previous_rzsm_2"]
            row["_previous_rzsm_3_"] = feat_dict["previous_rzsm_3"]
            row["_previous_rainfall_"] = feat_dict["previous_rainfall"]
            rows.append(row)
else:
    raise FileNotFoundError(f"{RESULTS_JSON} not found. Ensure it was created in the root.")

live_feature_dataframe = pd.DataFrame(rows)

X = live_feature_dataframe[FEATURES].copy()


# ============================================================
# TREE SHAP
# ============================================================

try:
    booster = model.get_booster()
except AttributeError:
    booster = model

dmatrix = xgb.DMatrix(
    X,
    feature_names=FEATURES
)

contrib = booster.predict(
    dmatrix,
    pred_contribs=True
)

shap_df = pd.DataFrame(
    contrib,
    columns=FEATURES + ["_BIAS_"]
)


# ============================================================
# VALIDATION
# ============================================================

probabilities = model.predict_proba(X)[:, 1]

# Calculate raw logit directly from probability.
eps = 1e-15

calculated_margin = np.log(
    np.clip(probabilities, eps, 1 - eps)
    /
    np.clip(1 - probabilities, eps, 1 - eps)
)


# SHAP reconstruction
shap_margin = shap_df.sum(axis=1).to_numpy()


# ============================================================
# OUTPUT
# ============================================================

locations = (
    live_feature_dataframe["location"].astype(str).tolist()
)

out_rows = []

for i, location in enumerate(locations):

    row = {
        "location": location,
        "xgb_probability": float(probabilities[i]),
        "xgb_margin_from_probability": float(calculated_margin[i]),
        "shap_reconstructed_margin": float(shap_margin[i]),
        "reconstruction_error": float(
            shap_margin[i] - calculated_margin[i]
        ),
    }

    for feature in FEATURES:
        row[feature] = float(shap_df.loc[i, feature])

    row["_BIAS_"] = float(shap_df.loc[i, "_BIAS_"])

    out_rows.append(row)


result = pd.DataFrame(out_rows)


# ============================================================
# PRINT FULL CONTRIBUTION TABLE
# ============================================================

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)

print("\n")
print("=" * 100)
print("XGBOOST TREE SHAP FEATURE CONTRIBUTION AUDIT")
print("=" * 100)

for _, row in result.iterrows():

    print("\n")
    print("-" * 100)
    print(row["location"])
    print("-" * 100)

    print(
        f"XGB probability : "
        f"{row['xgb_probability']:.8f}"
    )

    print(
        f"XGB margin      : "
        f"{row['xgb_margin_from_probability']:.8f}"
    )

    print(
        f"SHAP margin     : "
        f"{row['shap_reconstructed_margin']:.8f}"
    )

    print(
        f"Reconstruction error : "
        f"{row['reconstruction_error']:.12f}"
    )

    contributions = {
        feature: row[feature]
        for feature in FEATURES
    }

    contributions_sorted = sorted(
        contributions.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    print("\nFeature contributions ranked by |SHAP|:")

    for rank, (feature, value) in enumerate(
        contributions_sorted,
        start=1
    ):
        print(
            f"{rank:2d}. "
            f"{feature:35s} "
            f"{value:+.8f}"
        )

    print(
        f"\nBias contribution: "
        f"{row['_BIAS_']:+.8f}"
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR = Path("diagnostic_output")
OUTPUT_DIR.mkdir(exist_ok=True)
output_path = OUTPUT_DIR / "xgb_feature_contribution_shap_audit.csv"

result.to_csv(
    output_path,
    index=False
)

print("\n")
print("=" * 100)
print("AUDIT COMPLETE")
print("=" * 100)
print(f"Saved: {output_path}")
