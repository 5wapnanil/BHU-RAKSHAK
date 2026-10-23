from __future__ import annotations

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import xgboost as xgb

from backend.app.model.model_loader import load_all_models


# ============================================================
# CONFIGURATION
# ============================================================

TRAINING_CSV = Path(
    "data/master/Landslide_NER_XGBOOST_TRAIN_1278.csv"
)

OUTPUT_DIR = Path("diagnostic_output")
OUTPUT_DIR.mkdir(exist_ok=True)

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


# ============================================================
# LIVE VALIDATION VECTORS
# ============================================================

RESULTS_JSON = Path("extensive_validation_results.json")
LIVE = {}

if RESULTS_JSON.exists():
    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        for entry in data:
            if "error" in entry:
                continue
            name = entry["location"]["name"]
            feat_dict = entry["features"]
            # Map the json feature names to the frozen FEATURES list order
            vector = [
                feat_dict["rzsm_1"],
                feat_dict["rzsm_2"],
                feat_dict["rzsm_3"],
                feat_dict["cumulative_rainfall_3d_mm"],
                feat_dict["rzsm_mean"],
                feat_dict["rzsm_range"],
                feat_dict["rzsm_surface_deep_diff"],
                feat_dict["rain_rzsm_interaction"],
                feat_dict["previous_rzsm"],
                feat_dict["previous_rzsm_2"],
                feat_dict["previous_rzsm_3"],
                feat_dict["previous_rainfall"],
            ]
            LIVE[name] = vector
else:
    raise FileNotFoundError(f"{RESULTS_JSON} not found. Ensure it was created in the root.")


# ============================================================
# LOAD FROZEN MODEL
# ============================================================

MODELS = load_all_models()

MODEL = MODELS["xgboost"]

print("\n============================================================")
print("FROZEN XGBOOST DIAGNOSTIC")
print("============================================================")

print("Model type:", type(MODEL))

try:
    BOOSTER = MODEL.get_booster()
except AttributeError:
    BOOSTER = MODEL


print("Number of trees:", BOOSTER.num_boosted_rounds())


# ============================================================
# LOAD TRAINING DATA
# ============================================================

if not TRAINING_CSV.exists():
    raise FileNotFoundError(
        f"Training CSV not found: {TRAINING_CSV.resolve()}"
    )

df = pd.read_csv(TRAINING_CSV)

print("\nTraining shape:", df.shape)

# ------------------------------------------------------------
# Locate exact feature columns
# ------------------------------------------------------------

missing = [
    feature
    for feature in FEATURES
    if feature not in df.columns
]

if missing:
    print("\nERROR: Missing exact feature columns:")
    for feature in missing:
        print("  ", feature)

    print("\nAvailable columns:")
    for column in df.columns:
        print("  ", column)

    raise ValueError(
        "Training CSV does not contain the frozen feature contract."
    )


# ============================================================
# FEATURE DISTRIBUTION AUDIT
# ============================================================

distribution_rows = []

for feature in FEATURES:

    values = pd.to_numeric(
        df[feature],
        errors="coerce"
    )

    clean = values.dropna()

    row = {
        "feature": feature,
        "count": int(clean.count()),
        "missing": int(values.isna().sum()),
        "min": float(clean.min()),
        "p01": float(clean.quantile(0.01)),
        "p05": float(clean.quantile(0.05)),
        "p25": float(clean.quantile(0.25)),
        "median": float(clean.quantile(0.50)),
        "p75": float(clean.quantile(0.75)),
        "p95": float(clean.quantile(0.95)),
        "p99": float(clean.quantile(0.99)),
        "max": float(clean.max()),
        "mean": float(clean.mean()),
        "std": float(clean.std()),
    }

    distribution_rows.append(row)


distribution_df = pd.DataFrame(distribution_rows)

distribution_df.to_csv(
    OUTPUT_DIR / "training_feature_distribution.csv",
    index=False
)

print("\n============================================================")
print("TRAINING FEATURE DISTRIBUTION")
print("============================================================")

print(
    distribution_df.to_string(
        index=False
    )
)


# ============================================================
# LIVE FEATURE POSITION AUDIT
# ============================================================

live_rows = []

for location, vector in LIVE.items():

    for feature, value in zip(FEATURES, vector):

        values = pd.to_numeric(
            df[feature],
            errors="coerce"
        ).dropna()

        minimum = float(values.min())
        maximum = float(values.max())

        p01 = float(values.quantile(0.01))
        p05 = float(values.quantile(0.05))
        p25 = float(values.quantile(0.25))
        p75 = float(values.quantile(0.75))
        p95 = float(values.quantile(0.95))
        p99 = float(values.quantile(0.99))

        value = float(value)

        if value < minimum or value > maximum:
            status = "OUTSIDE_TRAINING_RANGE"

        elif value < p01 or value > p99:
            status = "EXTREME_1_PERCENT"

        elif value < p05 or value > p95:
            status = "OUTER_5_PERCENT"

        elif value < p25 or value > p75:
            status = "OUTER_50_PERCENT"

        else:
            status = "CENTRAL_50_PERCENT"

        live_rows.append({
            "location": location,
            "feature": feature,
            "live_value": value,
            "training_min": minimum,
            "training_p01": p01,
            "training_p05": p05,
            "training_p25": p25,
            "training_p75": p75,
            "training_p95": p95,
            "training_p99": p99,
            "training_max": maximum,
            "status": status,
        })


live_distribution_df = pd.DataFrame(live_rows)

live_distribution_df.to_csv(
    OUTPUT_DIR / "live_feature_distribution_audit.csv",
    index=False
)

print("\n============================================================")
print("LIVE FEATURE DISTRIBUTION AUDIT")
print("============================================================")

print(
    live_distribution_df.to_string(
        index=False
    )
)


# ============================================================
# TREE-BY-TREE MARGIN TRACE
# ============================================================

tree_rows = []


for location, vector in LIVE.items():

    X = pd.DataFrame(
        [vector],
        columns=FEATURES
    )

    dmatrix = xgb.DMatrix(
        X,
        feature_names=FEATURES
    )

    cumulative_margins = []

    for tree_count in range(1, 301):

        margin = float(
            BOOSTER.predict(
                dmatrix,
                output_margin=True,
                iteration_range=(0, tree_count)
            )[0]
        )

        cumulative_margins.append(margin)

    # --------------------------------------------------------
    # Convert cumulative margins into individual tree effects
    # --------------------------------------------------------

    previous_margin = None

    for tree_index, cumulative_margin in enumerate(
        cumulative_margins
    ):

        if previous_margin is None:
            contribution = cumulative_margin
        else:
            contribution = (
                cumulative_margin
                - previous_margin
            )

        tree_rows.append({
            "location": location,
            "tree": tree_index + 1,
            "cumulative_margin": cumulative_margin,
            "tree_contribution": contribution,
        })

        previous_margin = cumulative_margin


tree_df = pd.DataFrame(tree_rows)

tree_df.to_csv(
    OUTPUT_DIR / "xgboost_tree_trace.csv",
    index=False
)


# ============================================================
# TREE CONTRIBUTION SUMMARY
# ============================================================

summary_rows = []

for location in LIVE:

    subset = tree_df[
        tree_df["location"] == location
    ].copy()

    positive = subset[
        subset["tree_contribution"] > 0
    ]

    negative = subset[
        subset["tree_contribution"] < 0
    ]

    top_positive = (
        positive
        .sort_values(
            "tree_contribution",
            ascending=False
        )
        .head(20)
    )

    top_negative = (
        negative
        .sort_values(
            "tree_contribution",
            ascending=True
        )
        .head(20)
    )

    final_margin = float(
        subset.iloc[-1]["cumulative_margin"]
    )

    final_probability = (
        1.0 / (1.0 + math.exp(-final_margin))
    )

    summary_rows.append({
        "location": location,
        "final_margin": final_margin,
        "final_probability": final_probability,
        "positive_tree_count": int(len(positive)),
        "negative_tree_count": int(len(negative)),
        "positive_sum": float(
            positive["tree_contribution"].sum()
        ),
        "negative_sum": float(
            negative["tree_contribution"].sum()
        ),
        "largest_positive_tree": int(
            top_positive.iloc[0]["tree"]
        ) if len(top_positive) else None,
        "largest_positive_contribution": float(
            top_positive.iloc[0]["tree_contribution"]
        ) if len(top_positive) else None,
        "largest_negative_tree": int(
            top_negative.iloc[0]["tree"]
        ) if len(top_negative) else None,
        "largest_negative_contribution": float(
            top_negative.iloc[0]["tree_contribution"]
        ) if len(top_negative) else None,
    })


tree_summary_df = pd.DataFrame(summary_rows)

tree_summary_df.to_csv(
    OUTPUT_DIR / "xgboost_tree_summary.csv",
    index=False
)


# ============================================================
# TOP TREE CONTRIBUTIONS PER LOCATION
# ============================================================

top_rows = []

for location in LIVE:

    subset = tree_df[
        tree_df["location"] == location
    ].copy()

    subset["abs_contribution"] = (
        subset["tree_contribution"].abs()
    )

    top = subset.nlargest(
        30,
        "abs_contribution"
    )

    for _, row in top.iterrows():

        top_rows.append({
            "location": location,
            "tree": int(row["tree"]),
            "cumulative_margin": float(
                row["cumulative_margin"]
            ),
            "tree_contribution": float(
                row["tree_contribution"]
            ),
        })


top_tree_df = pd.DataFrame(top_rows)

top_tree_df.to_csv(
    OUTPUT_DIR / "xgboost_top_30_tree_contributions.csv",
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n============================================================")
print("TREE CONTRIBUTION SUMMARY")
print("============================================================")

print(
    tree_summary_df.to_string(
        index=False
    )
)

print("\n============================================================")
print("FILES CREATED")
print("============================================================")

print(
    OUTPUT_DIR / "training_feature_distribution.csv"
)

print(
    OUTPUT_DIR / "live_feature_distribution_audit.csv"
)

print(
    OUTPUT_DIR / "xgboost_tree_trace.csv"
)

print(
    OUTPUT_DIR / "xgboost_tree_summary.csv"
)

print(
    OUTPUT_DIR / "xgboost_top_30_tree_contributions.csv"
)

print("\nDIAGNOSTIC COMPLETE.")
