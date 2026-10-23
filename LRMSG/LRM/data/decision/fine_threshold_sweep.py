import numpy as np
import pandas as pd
from pathlib import Path

INPUT_FILE = "spatial_decision_layer_oof_results.csv"
PROBABILITY_COLUMN = "decision_spatial_oof_probability"
LABEL_COLUMN = "landslide_occurred"

START = 0.40
END = 0.80
STEP = 0.001

def metrics(y, p, threshold):
    pred = (p >= threshold).astype(int)
    tp = int(((y == 1) & (pred == 1)).sum())
    tn = int(((y == 0) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum())

    precision = tp / (tp + fp) if tp + fp else np.nan
    recall = tp / (tp + fn) if tp + fn else np.nan
    specificity = tn / (tn + fp) if tn + fp else np.nan
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else np.nan
    bal_acc = (recall + specificity) / 2
    youden = recall + specificity - 1
    accuracy = (tp + tn) / len(y)

    return {
        "threshold": threshold, "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "accuracy": accuracy, "precision": precision, "recall": recall,
        "specificity": specificity, "FPR": 1-specificity, "FNR": 1-recall,
        "F1": f1, "balanced_accuracy": bal_acc, "youden_J": youden,
        "predicted_positive_rate": pred.mean()
    }

def main():
    path = Path(INPUT_FILE)
    if not path.exists():
        path = Path(__file__).resolve().parent / INPUT_FILE
    if not path.exists():
        raise FileNotFoundError(f"Could not find {INPUT_FILE}")

    df = pd.read_csv(path)
    missing = {PROBABILITY_COLUMN, LABEL_COLUMN} - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    d = df[[PROBABILITY_COLUMN, LABEL_COLUMN]].copy()
    d[PROBABILITY_COLUMN] = pd.to_numeric(d[PROBABILITY_COLUMN], errors="coerce")
    d[LABEL_COLUMN] = pd.to_numeric(d[LABEL_COLUMN], errors="coerce")
    d = d.dropna()
    d = d[d[LABEL_COLUMN].isin([0, 1])]

    p = d[PROBABILITY_COLUMN].to_numpy(float)
    y = d[LABEL_COLUMN].to_numpy(int)

    thresholds = np.round(np.arange(START, END + STEP/2, STEP), 3)
    result = pd.DataFrame([metrics(y, p, t) for t in thresholds])

    # Exact current operating point.
    current = result.iloc[(result["threshold"] - 0.600).abs().argmin()]

    # Best candidates by each criterion.
    best_f1 = result.loc[result["F1"].idxmax()]
    best_bal = result.loc[result["balanced_accuracy"].idxmax()]
    best_youden = result.loc[result["youden_J"].idxmax()]
    best_accuracy = result.loc[result["accuracy"].idxmax()]

    # Recall-constrained candidates: useful for early-warning analysis.
    recall_constraints = [0.99, 0.98, 0.97, 0.95]
    constrained = []
    for minimum_recall in recall_constraints:
        eligible = result[result["recall"] >= minimum_recall]
        if len(eligible):
            row = eligible.loc[eligible["specificity"].idxmax()]
            constrained.append({
                "minimum_recall": minimum_recall,
                "threshold": row["threshold"],
                "recall": row["recall"],
                "specificity": row["specificity"],
                "FPR": row["FPR"],
                "F1": row["F1"],
                "balanced_accuracy": row["balanced_accuracy"]
            })
        else:
            constrained.append({
                "minimum_recall": minimum_recall,
                "threshold": np.nan, "recall": np.nan,
                "specificity": np.nan, "FPR": np.nan,
                "F1": np.nan, "balanced_accuracy": np.nan
            })
    constrained = pd.DataFrame(constrained)

    # Local neighborhood around 0.60.
    neighborhood = result[(result["threshold"] >= 0.590) & (result["threshold"] <= 0.610)].copy()

    # Stability: thresholds within 99.5% of max F1.
    max_f1 = result["F1"].max()
    stable_f1 = result[result["F1"] >= 0.995 * max_f1].copy()

    # Calibrated equivalent of selected raw thresholds.
    a = -0.559793489367
    b = 1.080159577111
    eps = 1e-15
    def calibrate(x):
        x = np.clip(np.asarray(x, float), eps, 1-eps)
        z = np.log(x/(1-x))
        return 1/(1+np.exp(-(a+b*z)))

    selected = pd.DataFrame([
        {"criterion": "Current operating point", **current.to_dict()},
        {"criterion": "Best F1", **best_f1.to_dict()},
        {"criterion": "Best balanced accuracy", **best_bal.to_dict()},
        {"criterion": "Best Youden J", **best_youden.to_dict()},
        {"criterion": "Best accuracy", **best_accuracy.to_dict()},
    ])
    selected["calibrated_equivalent"] = calibrate(selected["threshold"])

    result.to_csv(path.parent / "fine_threshold_sweep_040_080.csv", index=False)
    neighborhood.to_csv(path.parent / "threshold_neighborhood_059_061.csv", index=False)
    selected.to_csv(path.parent / "fine_sweep_selected_points.csv", index=False)
    constrained.to_csv(path.parent / "recall_constrained_operating_points.csv", index=False)
    stable_f1.to_csv(path.parent / "f1_stability_region_99_5pct.csv", index=False)

    print("="*95)
    print("FINE-GRAINED OPERATING THRESHOLD SWEEP — RAW FINAL DECISION LAYER")
    print("="*95)
    print(f"Rows: {len(y)} | Positives: {y.sum()} | Negatives: {(1-y).sum()}")
    print(f"Threshold range: {START:.3f} to {END:.3f} | Step: {STEP:.3f}")
    print()

    print("SELECTED OPERATING POINTS")
    print(selected[[
        "criterion","threshold","accuracy","precision","recall",
        "specificity","FPR","FNR","F1","balanced_accuracy",
        "youden_J","calibrated_equivalent"
    ]].to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print()

    print("RECALL-CONSTRAINED OPERATING POINTS")
    print(constrained.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print()

    print("0.590–0.610 NEIGHBORHOOD")
    print(neighborhood.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print()

    print("F1 STABILITY REGION (>= 99.5% OF MAX F1)")
    if len(stable_f1):
        print(
            f"Thresholds from {stable_f1['threshold'].min():.3f} "
            f"to {stable_f1['threshold'].max():.3f} "
            f"({len(stable_f1)} tested points)."
        )
    else:
        print("No points found.")
    print()

    print("INTERPRETATION")
    print(f"Best F1 threshold: {best_f1['threshold']:.3f} (F1={best_f1['F1']:.6f})")
    print(f"Best balanced-accuracy threshold: {best_bal['threshold']:.3f} "
          f"(BA={best_bal['balanced_accuracy']:.6f})")
    print(f"Best Youden-J threshold: {best_youden['threshold']:.3f} "
          f"(J={best_youden['youden_J']:.6f})")
    print(f"Current 0.600 threshold: F1={current['F1']:.6f}, "
          f"BA={current['balanced_accuracy']:.6f}")
    print("No threshold has been automatically changed.")

    print()
    print("OUTPUT FILES")
    for name in [
        "fine_threshold_sweep_040_080.csv",
        "threshold_neighborhood_059_061.csv",
        "fine_sweep_selected_points.csv",
        "recall_constrained_operating_points.csv",
        "f1_stability_region_99_5pct.csv",
    ]:
        print(" -", name)

if __name__ == "__main__":
    main()
