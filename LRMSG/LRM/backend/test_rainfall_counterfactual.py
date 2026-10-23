from pathlib import Path
import math
import numpy as np
import pandas as pd
import xgboost as xgb
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.model.model_loader import load_all_models


# ============================================================
# CONFIG
# ============================================================

DISCREPANCY_CSV = Path(
    "significant_rainfall_discrepancy_landslide_locations.csv"
)

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
# LOAD DISCREPANCY & TRAINING DATA
# ============================================================

disc = pd.read_csv(DISCREPANCY_CSV)
train_df = pd.read_csv(TRAINING_CSV)

print("\n============================================================")
print("RAINFALL COUNTERFACTUAL TEST")
print("============================================================")

print(f"Discrepancy rows: {len(disc)}")
print(f"Training rows: {len(train_df)}")

# Round coordinates for safe merging
disc["latitude_round"] = disc["latitude"].round(5)
disc["longitude_round"] = disc["longitude"].round(5)
train_df["latitude_round"] = train_df["latitude"].round(5)
train_df["longitude_round"] = train_df["longitude"].round(5)
# Ensure event_date is string for merge
disc["event_date"] = disc["event_date"].astype(str)
train_df["event_date"] = train_df["event_date"].astype(str)

merged = disc.merge(
    train_df,
    how="inner",
    left_on=["latitude_round", "longitude_round", "event_date"],
    right_on=["latitude_round", "longitude_round", "event_date"],
    suffixes=('_disc', '')
)

print(f"Merged matching rows: {len(merged)}")

if len(merged) == 0:
    raise RuntimeError("Zero matching rows between discrepancy file and training data based on coords and date.")

# ============================================================
# LOAD FROZEN XGBOOST
# ============================================================

models = load_all_models()
model = models["xgboost"]

try:
    booster = model.get_booster()
except AttributeError:
    booster = model

print("\nFrozen model:", type(model))
print("Boosted rounds:", booster.num_boosted_rounds())

if booster.num_boosted_rounds() != 300:
    raise RuntimeError("Frozen model does not contain exactly 300 trees.")


# ============================================================
# BUILD RESULT ROWS
# ============================================================

results = []

for idx, row in merged.iterrows():

    # Get rainfall values
    old_rain = float(row["original_cumulative_rainfall_mm"])
    new_rain = float(row["updated_correct_cumulative_rainfall_mm"])

    # Extract RZSM values from the matched training data
    rzsm1 = float(row["rzsm_1"])
    rzsm2 = float(row["rzsm_2"])
    rzsm3 = float(row["rzsm_3"])
    
    # Optional previous lag features
    previous_rzsm = float(row["_previous_rzsm_"]) if pd.notna(row["_previous_rzsm_"]) else np.nan
    previous_rzsm_2 = float(row["_previous_rzsm_2_"]) if pd.notna(row["_previous_rzsm_2_"]) else np.nan
    previous_rzsm_3 = float(row["_previous_rzsm_3_"]) if pd.notna(row["_previous_rzsm_3_"]) else np.nan
    previous_rainfall = float(row["_previous_rainfall_"]) if pd.notna(row["_previous_rainfall_"]) else np.nan

    rzsm_mean = (rzsm1 + rzsm2 + rzsm3) / 3.0

    # --------------------------------------------------------
    # IMPORTANT:
    # Interaction must be recalculated using corrected rain.
    # --------------------------------------------------------
    old_interaction = old_rain * rzsm_mean
    new_interaction = new_rain * rzsm_mean

    # --------------------------------------------------------
    # Other features remain unchanged for this counterfactual.
    # --------------------------------------------------------
    base = {
        "rzsm_1": rzsm1,
        "rzsm_2": rzsm2,
        "rzsm_3": rzsm3,
        "_rzsm_mean_": rzsm_mean,
        "_rzsm_range_": (max(rzsm1, rzsm2, rzsm3) - min(rzsm1, rzsm2, rzsm3)),
        "_rzsm_surface_deep_diff_": (rzsm1 - rzsm3),
        "_previous_rzsm_": previous_rzsm,
        "_previous_rzsm_2_": previous_rzsm_2,
        "_previous_rzsm_3_": previous_rzsm_3,
        "_previous_rainfall_": previous_rainfall,
    }

    # ========================================================
    # OLD VECTOR
    # ========================================================
    old_vector = {
        **base,
        "cumulative_rainfall_3d_mm": old_rain,
        "_rain_rzsm_interaction_": old_interaction,
    }

    # ========================================================
    # CORRECTED VECTOR
    # ========================================================
    new_vector = {
        **base,
        "cumulative_rainfall_3d_mm": new_rain,
        "_rain_rzsm_interaction_": new_interaction,
    }

    # ========================================================
    # CREATE DATAFRAMES IN EXACT FROZEN ORDER
    # ========================================================
    X_old = pd.DataFrame([[old_vector[f] for f in FEATURES]], columns=FEATURES)
    X_new = pd.DataFrame([[new_vector[f] for f in FEATURES]], columns=FEATURES)

    # ========================================================
    # XGBOOST PREDICTION
    # ========================================================
    d_old = xgb.DMatrix(X_old, feature_names=FEATURES)
    d_new = xgb.DMatrix(X_new, feature_names=FEATURES)

    old_margin = float(booster.predict(d_old, output_margin=True)[0])
    new_margin = float(booster.predict(d_new, output_margin=True)[0])

    old_probability = 1.0 / (1.0 + math.exp(-old_margin))
    new_probability = 1.0 / (1.0 + math.exp(-new_margin))

    results.append({
        "row_index": idx,
        "location": f"{row['state']}, {row['district']} ({row['latitude_disc']}, {row['longitude_disc']})",
        "original_rainfall_3d_mm": old_rain,
        "corrected_rainfall_3d_mm": new_rain,
        "rainfall_difference_mm": (new_rain - old_rain),
        "rzsm_mean": rzsm_mean,
        "original_rain_rzsm_interaction": old_interaction,
        "corrected_rain_rzsm_interaction": new_interaction,
        "original_xgb_margin": old_margin,
        "corrected_xgb_margin": new_margin,
        "original_xgb_probability": old_probability,
        "corrected_xgb_probability": new_probability,
        "probability_change": new_probability - old_probability,
        "absolute_probability_change": abs(new_probability - old_probability),
        "margin_change": new_margin - old_margin,
    })


# ============================================================
# SAVE
# ============================================================
result_df = pd.DataFrame(results)
result_df = result_df.sort_values("absolute_probability_change", ascending=False)
output_file = OUTPUT_DIR / "rainfall_counterfactual_results.csv"
result_df.to_csv(output_file, index=False)


# ============================================================
# SUMMARY
# ============================================================
print("\n============================================================")
print("COUNTERFACTUAL SUMMARY")
print("============================================================")

print(
    result_df[
        [
            "location",
            "original_rainfall_3d_mm",
            "corrected_rainfall_3d_mm",
            "original_xgb_probability",
            "corrected_xgb_probability",
            "probability_change",
        ]
    ].to_string(index=False)
)

print("\n============================================================")
print("STATISTICS")
print("============================================================")

changes = result_df["probability_change"]

print("Mean probability change:", changes.mean())
print("Median probability change:", changes.median())
print("Maximum absolute change:", result_df["absolute_probability_change"].max())
print("Rows with change > 5 percentage points:", (result_df["absolute_probability_change"] > 0.05).sum())
print("Rows with change > 10 percentage points:", (result_df["absolute_probability_change"] > 0.10).sum())
print("Rows with change > 20 percentage points:", (result_df["absolute_probability_change"] > 0.20).sum())

print("\nOutput:")
print(output_file.resolve())
print("\n============================================================")
print("NO MODEL WAS MODIFIED.")
print("COUNTERFACTUAL TEST COMPLETE.")
print("============================================================")
