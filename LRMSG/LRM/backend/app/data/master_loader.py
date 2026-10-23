from pathlib import Path
from typing import Final

import pandas as pd


# Project root:
# LRM/
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]

MASTER_DATA_DIR: Final[Path] = PROJECT_ROOT / "data" / "master"

RAW_MASTER_PATH: Final[Path] = (
    MASTER_DATA_DIR
    / "Landslide_NER_MASTER_2016_ROWS_RAW.csv"
)

XGBOOST_MASTER_PATH: Final[Path] = (
    MASTER_DATA_DIR
    / "Landslide_NER_MASTER_2016_ROWS_WITH_XGBOOST_FEATURES.csv"
)


RAW_REQUIRED_COLUMNS: Final[list[str]] = [
    "event_date",
    "state",
    "district",
    "latitude",
    "longitude",
    "rzsm_1",
    "rzsm_2",
    "rzsm_3",
    "landslide_occurred",
    "cumulative_rainfall_3d_mm",
    "elevation_m",
    "slope_deg",
    "soil_type_wrb",
    "road_mdr_pct",
    "road_odr_pct",
    "road_pmgsY_border_pct",
    "road_rural_pct",
    "month",
    "season",
]


XGBOOST_REQUIRED_COLUMNS: Final[list[str]] = [
    "master_row_id",
    *RAW_REQUIRED_COLUMNS,
    "_rzsm_mean_",
    "_rzsm_range_",
    "_rzsm_surface_deep_diff_",
    "_rain_rzsm_interaction_",
    "_previous_rzsm_",
    "_previous_rzsm_2_",
    "_previous_rzsm_3_",
    "_previous_rainfall_",
]


XGBOOST_NUMERIC_COLUMNS: Final[list[str]] = [
    "rzsm_1",
    "rzsm_2",
    "rzsm_3",
    "cumulative_rainfall_3d_mm",
    "elevation_m",
    "slope_deg",
    "_rzsm_mean_",
    "_rzsm_range_",
    "_rzsm_surface_deep_diff_",
    "_rain_rzsm_interaction_",
]


def _validate_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str,
) -> None:

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{dataset_name} is missing required columns: {missing}"
        )


def _validate_common_integrity(
    df: pd.DataFrame,
    dataset_name: str,
) -> None:

    if df.empty:
        raise ValueError(
            f"{dataset_name} is empty."
        )

    if df["event_date"].isna().any():
        raise ValueError(
            f"{dataset_name} contains missing event_date values."
        )

    parsed_dates = pd.to_datetime(
        df["event_date"],
        errors="coerce",
    )

    if parsed_dates.isna().any():
        raise ValueError(
            f"{dataset_name} contains invalid event_date values."
        )

    if df["latitude"].isna().any():
        raise ValueError(
            f"{dataset_name} contains missing latitude values."
        )

    if df["longitude"].isna().any():
        raise ValueError(
            f"{dataset_name} contains missing longitude values."
        )

    if ((df["latitude"] < -90) | (df["latitude"] > 90)).any():
        raise ValueError(
            f"{dataset_name} contains invalid latitude values."
        )

    if ((df["longitude"] < -180) | (df["longitude"] > 180)).any():
        raise ValueError(
            f"{dataset_name} contains invalid longitude values."
        )

    if df["landslide_occurred"].isna().any():
        raise ValueError(
            f"{dataset_name} contains missing landslide_occurred values."
        )

    target_values = set(
        pd.to_numeric(
            df["landslide_occurred"],
            errors="coerce",
        ).dropna().unique()
    )

    if not target_values.issubset({0, 1}):
        raise ValueError(
            f"{dataset_name} contains invalid landslide_occurred "
            f"values: {sorted(target_values)}"
        )


def _validate_xgboost_numeric_features(
    df: pd.DataFrame,
) -> None:

    for column in XGBOOST_NUMERIC_COLUMNS:

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if numeric_values.isna().any():
            raise ValueError(
                f"XGBoost master dataset contains non-numeric "
                f"or missing values in '{column}'."
            )


def _validate_xgboost_ids(
    df: pd.DataFrame,
) -> None:

    if df["master_row_id"].isna().any():
        raise ValueError(
            "XGBoost master dataset contains missing master_row_id values."
        )

    if df["master_row_id"].duplicated().any():
        raise ValueError(
            "XGBoost master dataset contains duplicate master_row_id values."
        )


def load_raw_master() -> pd.DataFrame:
    """
    Load the original master dataset.

    Read-only operation.
    """

    if not RAW_MASTER_PATH.exists():
        raise FileNotFoundError(
            f"RAW master dataset not found: {RAW_MASTER_PATH}"
        )

    df = pd.read_csv(RAW_MASTER_PATH)

    _validate_columns(
        df,
        RAW_REQUIRED_COLUMNS,
        "RAW master dataset",
    )

    _validate_common_integrity(
        df,
        "RAW master dataset",
    )

    return df


def load_xgboost_master() -> pd.DataFrame:
    """
    Load the master dataset containing the exact
    engineered features used by the frozen XGBoost model.

    Read-only operation.
    """

    if not XGBOOST_MASTER_PATH.exists():
        raise FileNotFoundError(
            f"XGBoost master dataset not found: {XGBOOST_MASTER_PATH}"
        )

    df = pd.read_csv(XGBOOST_MASTER_PATH)

    _validate_columns(
        df,
        XGBOOST_REQUIRED_COLUMNS,
        "XGBoost master dataset",
    )

    _validate_common_integrity(
        df,
        "XGBoost master dataset",
    )

    _validate_xgboost_numeric_features(df)

    _validate_xgboost_ids(df)

    return df


def validate_master_datasets() -> dict:
    """
    Read and validate both master datasets.

    No dataset or model is modified.
    """

    raw_df = load_raw_master()
    xgb_df = load_xgboost_master()

    return {
        "raw": {
            "rows": len(raw_df),
            "columns": len(raw_df.columns),
        },
        "xgboost": {
            "rows": len(xgb_df),
            "columns": len(xgb_df.columns),
        },
    }