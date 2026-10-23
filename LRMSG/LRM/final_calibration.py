"""
Final Decision-Layer Probability Calibration
=============================================

OPTION B

Frozen pipeline:
    XGBoost -> AHC -> Spatial Decision Layer

This module calibrates ONLY the final Decision-Layer
probability for presentation/output.

It does NOT modify:
    - XGBoost
    - AHC
    - Decision Layer
    - model thresholds
"""

import math


# ============================================================
# LEARNED FINAL CALIBRATION PARAMETERS
# ============================================================

FINAL_CALIBRATION_A = -0.559793489367
FINAL_CALIBRATION_B = 1.080159577111


# ============================================================
# NUMERICAL SAFETY
# ============================================================

EPSILON = 1e-15


# ============================================================
# LOGIT
# ============================================================

def logit(probability: float) -> float:
    """
    Convert probability to log-odds.

        logit(p) = ln(p / (1-p))
    """

    p = float(probability)

    p = max(
        EPSILON,
        min(1.0 - EPSILON, p)
    )

    return math.log(
        p / (1.0 - p)
    )


# ============================================================
# SIGMOID
# ============================================================

def sigmoid(value: float) -> float:
    """
    Convert log-odds back to probability.
    """

    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)

    z = math.exp(value)

    return z / (1.0 + z)


# ============================================================
# FINAL PROBABILITY CALIBRATION
# ============================================================

def calibrate_final_probability(
    raw_final_probability: float
) -> float:
    """
    Calibrate the final Decision-Layer probability.

    Formula:

        logit(P_calibrated)
            = A + B * logit(P_raw_final)

    """

    raw_probability = float(
        raw_final_probability
    )

    raw_logit = logit(
        raw_probability
    )

    calibrated_logit = (
        FINAL_CALIBRATION_A
        +
        FINAL_CALIBRATION_B * raw_logit
    )

    calibrated_probability = sigmoid(
        calibrated_logit
    )

    return float(
        calibrated_probability
    )


# ============================================================
# COMPLETE RESULT
# ============================================================

def calibrated_final_result(
    raw_final_probability: float
) -> dict:
    """
    Return raw and calibrated final probabilities.
    """

    raw_probability = float(
        raw_final_probability
    )

    calibrated_probability = (
        calibrate_final_probability(
            raw_probability
        )
    )

    return {
        "raw_probability": raw_probability,
        "calibrated_probability": calibrated_probability,
        "calibration": {
            "method": "logit_platt",
            "a": FINAL_CALIBRATION_A,
            "b": FINAL_CALIBRATION_B
        }
    }
