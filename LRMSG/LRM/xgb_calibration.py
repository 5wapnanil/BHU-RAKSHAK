import math

XGB_CALIBRATION_A = 0.023223334854
XGB_CALIBRATION_B = 0.529194610195
EPSILON = 1e-15

def logit(probability: float) -> float:
    p = float(probability)
    p = max(EPSILON, min(1.0 - EPSILON, p))
    return math.log(p / (1.0 - p))

def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)

def calibrate_xgb_probability(raw_probability: float) -> float:
    raw_logit = logit(raw_probability)
    calibrated_logit = XGB_CALIBRATION_A + XGB_CALIBRATION_B * raw_logit
    return float(sigmoid(calibrated_logit))

def calibrated_xgb_result(raw_probability: float) -> dict:
    return {
        "raw_probability": float(raw_probability),
        "calibrated_probability": calibrate_xgb_probability(raw_probability),
        "calibration": {
            "method": "logit_platt",
            "a": XGB_CALIBRATION_A,
            "b": XGB_CALIBRATION_B
        }
    }
