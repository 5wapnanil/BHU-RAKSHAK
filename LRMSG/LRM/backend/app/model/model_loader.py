from pathlib import Path

# NOTE: Heavy ML libraries (xgboost, joblib) are not imported at top level
# to prevent legacy ML runtime from loading into memory.
# Model artifact paths are preserved for future reference and reuse:
MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
XGBOOST_MODEL_PATH = MODEL_DIR / "STEP73_FROZEN_XGBOOST.json"
AHC_MODEL_PATH = MODEL_DIR / "ahc_landslide_susceptibility_model.pkl"
DECISION_MODEL_PATH = MODEL_DIR / "spatial_layered_decision_model.pkl"

DISABLED_MSG = "Legacy landslide prediction ML models have been retired and disabled."


def load_xgboost_model():
    """Disabled: Legacy XGBoost model loading is retired."""
    # Preserved original implementation:
    # import xgboost as xgb
    # model = xgb.XGBClassifier()
    # model.load_model(XGBOOST_MODEL_PATH)
    # return model
    raise RuntimeError(DISABLED_MSG)


def load_ahc_model():
    """Disabled: Legacy AHC model loading is retired."""
    # Preserved original implementation:
    # import joblib
    # return joblib.load(AHC_MODEL_PATH)
    raise RuntimeError(DISABLED_MSG)


def load_decision_model():
    """Disabled: Legacy decision model loading is retired."""
    # Preserved original implementation:
    # import joblib
    # return joblib.load(DECISION_MODEL_PATH)
    raise RuntimeError(DISABLED_MSG)


def load_all_models():
    """Disabled: Legacy ML models are retired and not loaded into memory."""
    # Preserved original implementation:
    # return {
    #     "xgboost": load_xgboost_model(),
    #     "ahc": load_ahc_model(),
    #     "decision": load_decision_model(),
    # }
    raise RuntimeError(DISABLED_MSG)
