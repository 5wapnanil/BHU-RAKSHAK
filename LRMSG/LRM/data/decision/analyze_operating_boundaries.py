import math
from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = "spatial_decision_layer_oof_results.csv"
PROBABILITY_COLUMN = "decision_spatial_oof_probability"
LABEL_COLUMN = "landslide_occurred"

FINAL_CALIBRATION_A = -0.559793489367
FINAL_CALIBRATION_B = 1.080159577111
EPSILON = 1e-15

THRESHOLDS = np.round(np.arange(0.10, 0.951, 0.05), 2)
BOUNDARY_BINS = [
    (0.50, 0.55),
    (0.55, 0.60),
    (0.60, 0.65),
    (0.65, 0.70),
]
BAND_EDGES = [0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPSILON, 1.0 - EPSILON)
    return np.log(p / (1.0 - p))


def sigmoid(z):
    z = np.asarray(z, dtype=float)
    return 1.0 / (1.0 + np.exp(-z))


def calibrate_final_probability(p):
    return sigmoid(FINAL_CALIBRATION_A + FINAL_CALIBRATION_B * logit(p))


def confusion_metrics(y_true, probability, threshold):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = (np.asarray(probability) >= threshold).astype(int)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    n = len(y_true)
    accuracy = (tp + tn) / n if n else np.nan
    precision = tp / (tp + fp) if (tp + fp) else np.nan
    recall = tp / (tp + fn) if (tp + fn) else np.nan
    specificity = tn / (tn + fp) if (tn + fp) else np.nan
    fpr = fp / (fp + tn) if (fp + tn) else np.nan
    fnr = fn / (fn + tp) if (fn + tp) else np.nan
    f1 = (
        2 * precision * recall / (precision + recall)
        if np.isfinite(precision) and np.isfinite(recall) and (precision + recall)
        else np.nan
    )
    balanced_accuracy = (
        (recall + specificity) / 2
        if np.isfinite(recall) and np.isfinite(specificity)
        else np.nan
    )

    return {
        "threshold": threshold,
        "n": n,
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "FPR": fpr,
        "FNR": fnr,
        "F1": f1,
        "balanced_accuracy": balanced_accuracy,
        "predicted_positive_rate": float(y_pred.mean()) if n else np.nan,
    }


def main():
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        # Also support running from the directory containing this script.
        input_path = Path(__file__).resolve().parent / INPUT_FILE

    if not input_path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}. Put the script beside the OOF CSV."
        )

    df = pd.read_csv(input_path)

    required = {PROBABILITY_COLUMN, LABEL_COLUMN}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    work = df[[PROBABILITY_COLUMN, LABEL_COLUMN]].copy()
    work[PROBABILITY_COLUMN] = pd.to_numeric(work[PROBABILITY_COLUMN], errors="coerce")
    work[LABEL_COLUMN] = pd.to_numeric(work[LABEL_COLUMN], errors="coerce")
    work = work.dropna()

    # Binary labels only.
    work = work[work[LABEL_COLUMN].isin([0, 1])].copy()
    p = work[PROBABILITY_COLUMN].to_numpy(dtype=float)
    y = work[LABEL_COLUMN].to_numpy(dtype=int)

    if len(work) == 0:
        raise ValueError("No usable OOF rows remain after validation.")

    if ((p < 0) | (p > 1)).any():
        raise ValueError("OOF probabilities outside [0, 1] were found.")

    calibrated = calibrate_final_probability(p)
    work["calibrated_final_probability"] = calibrated

    # 1. Threshold performance table.
    threshold_rows = [confusion_metrics(y, p, float(t)) for t in THRESHOLDS]
    threshold_table = pd.DataFrame(threshold_rows)

    # 2. Explicit 0.60 confusion matrix / metrics.
    metrics_060 = confusion_metrics(y, p, 0.60)
    confusion_060 = pd.DataFrame(
        [[metrics_060["TN"], metrics_060["FP"]],
         [metrics_060["FN"], metrics_060["TP"]]],
        index=["Actual 0", "Actual 1"],
        columns=["Predicted 0", "Predicted 1"],
    )

    # 3. Threshold-to-calibrated-score mapping.
    mapping_thresholds = np.array(
        [0.10, 0.20, 0.30, 0.40, 0.50, 0.55, 0.60, 0.65,
         0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.99]
    )
    mapping = pd.DataFrame({
        "raw_final_threshold": mapping_thresholds,
        "calibrated_final_equivalent": calibrate_final_probability(mapping_thresholds),
        "calibrated_percent": calibrate_final_probability(mapping_thresholds) * 100,
    })

    # 4. Probability-band event rates using raw final scores.
    band_rows = []
    for lo, hi in zip(BAND_EDGES[:-1], BAND_EDGES[1:]):
        if hi < 1.0:
            mask = (p >= lo) & (p < hi)
            label = f"[{lo:.2f}, {hi:.2f})"
        else:
            mask = (p >= lo) & (p <= hi)
            label = f"[{lo:.2f}, {hi:.2f}]"

        vals = p[mask]
        labels = y[mask]
        cal_vals = calibrated[mask]

        band_rows.append({
            "raw_probability_band": label,
            "lower": lo,
            "upper": hi,
            "n": int(mask.sum()),
            "actual_landslide_rate": float(labels.mean()) if len(labels) else np.nan,
            "mean_raw_probability": float(vals.mean()) if len(vals) else np.nan,
            "mean_calibrated_probability": float(cal_vals.mean()) if len(cal_vals) else np.nan,
            "min_calibrated_probability": float(cal_vals.min()) if len(cal_vals) else np.nan,
            "max_calibrated_probability": float(cal_vals.max()) if len(cal_vals) else np.nan,
        })
    band_table = pd.DataFrame(band_rows)

    # 5. Focused boundary analysis.
    boundary_rows = []
    for lo, hi in BOUNDARY_BINS:
        mask = (p >= lo) & (p < hi)
        vals = p[mask]
        labels = y[mask]
        cal_vals = calibrated[mask]
        boundary_rows.append({
            "raw_boundary_bin": f"[{lo:.2f}, {hi:.2f})",
            "n": int(mask.sum()),
            "positive_count": int(labels.sum()),
            "negative_count": int((1 - labels).sum()),
            "actual_landslide_rate": float(labels.mean()) if len(labels) else np.nan,
            "mean_raw_score": float(vals.mean()) if len(vals) else np.nan,
            "mean_calibrated_score": float(cal_vals.mean()) if len(cal_vals) else np.nan,
            "min_calibrated_score": float(cal_vals.min()) if len(cal_vals) else np.nan,
            "max_calibrated_score": float(cal_vals.max()) if len(cal_vals) else np.nan,
        })
    boundary_table = pd.DataFrame(boundary_rows)

    # 6. Exact 0.60 operating point plus nearby candidates.
    candidate_thresholds = [0.50, 0.55, 0.60, 0.65, 0.70]
    candidates = pd.DataFrame(
        [confusion_metrics(y, p, t) for t in candidate_thresholds]
    )
    candidates["calibrated_equivalent"] = calibrate_final_probability(
        candidates["threshold"].to_numpy()
    )

    # Conservative summary: do not auto-select a new threshold.
    # Rank only for inspection, not as a recommendation.
    candidates["F1_rank"] = candidates["F1"].rank(ascending=False, method="min")
    candidates["balanced_accuracy_rank"] = candidates["balanced_accuracy"].rank(
        ascending=False, method="min"
    )

    # 7. Sanity checks.
    checks = {
        "rows_used": len(work),
        "positive_rows": int(y.sum()),
        "negative_rows": int((1 - y).sum()),
        "observed_positive_rate": float(y.mean()),
        "probabilities_in_0_1": bool(((p >= 0) & (p <= 1)).all()),
        "calibrated_probabilities_in_0_1": bool(
            ((calibrated >= 0) & (calibrated <= 1)).all()
        ),
        "calibration_monotonic": bool(np.all(np.diff(calibrated[np.argsort(p)]) >= -1e-12)),
        "raw_060_calibrated_equivalent": float(calibrate_final_probability(0.60)),
    }

    output_dir = input_path.parent
    threshold_table.to_csv(output_dir / "operating_threshold_performance.csv", index=False)
    confusion_060.to_csv(output_dir / "confusion_matrix_raw_threshold_060.csv")
    mapping.to_csv(output_dir / "raw_to_calibrated_threshold_mapping.csv", index=False)
    band_table.to_csv(output_dir / "raw_probability_band_analysis.csv", index=False)
    boundary_table.to_csv(output_dir / "boundary_050_to_070_analysis.csv", index=False)
    candidates.to_csv(output_dir / "candidate_operating_points_050_070.csv", index=False)
    pd.DataFrame([checks]).to_csv(output_dir / "operating_boundary_sanity_checks.csv", index=False)

    print("=" * 92)
    print("OPERATING-BOUNDARY ANALYSIS — FINAL DECISION LAYER OOF")
    print("=" * 92)
    print(f"Input: {input_path.name}")
    print(f"Rows used: {checks['rows_used']} | Positives: {checks['positive_rows']} | Negatives: {checks['negative_rows']}")
    print(f"Observed positive rate: {checks['observed_positive_rate']:.6f}")
    print()

    print("1) THRESHOLD PERFORMANCE")
    print(threshold_table.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print()

    print("2) RAW THRESHOLD = 0.60")
    print(confusion_060.to_string())
    for key in ["accuracy", "precision", "recall", "specificity", "FPR", "FNR", "F1", "balanced_accuracy"]:
        print(f"{key:20s}: {metrics_060[key]:.6f}")
    print()

    print("3) RAW -> CALIBRATED THRESHOLD MAPPING")
    print(mapping.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print()

    print("4) PROBABILITY-BAND EVENT RATES")
    print(band_table.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print()

    print("5) FOCUSED 0.50–0.70 BOUNDARY ANALYSIS")
    print(boundary_table.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print()

    print("6) CANDIDATE OPERATING POINTS — INSPECTION ONLY")
    print(candidates.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print()

    print("7) SANITY CHECKS")
    for k, v in checks.items():
        print(f"{k}: {v}")
    print()

    print("No threshold was automatically changed or selected.")
    print("The existing raw Decision Layer threshold remains 0.60 pending interpretation.")
    print()
    print("Output files:")
    for name in [
        "operating_threshold_performance.csv",
        "confusion_matrix_raw_threshold_060.csv",
        "raw_to_calibrated_threshold_mapping.csv",
        "raw_probability_band_analysis.csv",
        "boundary_050_to_070_analysis.csv",
        "candidate_operating_points_050_070.csv",
        "operating_boundary_sanity_checks.csv",
    ]:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
