from __future__ import annotations

import math
from typing import Any


def calculate_rzsm_mean(
    rzsm_1: float,
    rzsm_2: float,
    rzsm_3: float,
) -> float:
    return (rzsm_1 + rzsm_2 + rzsm_3) / 3.0


def calculate_rzsm_range(
    rzsm_1: float,
    rzsm_2: float,
    rzsm_3: float,
) -> float:
    return max(rzsm_1, rzsm_2, rzsm_3) - min(
        rzsm_1,
        rzsm_2,
        rzsm_3,
    )


def calculate_surface_deep_difference(
    rzsm_1: float,
    rzsm_3: float,
) -> float:
    return rzsm_1 - rzsm_3


def calculate_rain_rzsm_interaction(
    cumulative_rainfall_3d_mm: float,
    rzsm_mean: float,
) -> float:
    return cumulative_rainfall_3d_mm * rzsm_mean


def calculate_rzsm_0_100(
    rzsm_1: float,
    rzsm_2: float,
    rzsm_3: float,
) -> float:
    """
    Weighted 0–100 cm representation verified against
    the project's supplied AHC training data.
    """
    return (
        7.0 * rzsm_1
        + 21.0 * rzsm_2
        + 72.0 * rzsm_3
    ) / 100.0


def _previous_value(
    previous: list[dict[str, Any]],
    index: int,
    key: str,
) -> float:
    if index >= len(previous):
        return float("nan")

    value = previous[index].get(key)

    if value is None:
        return float("nan")

    return float(value)


def engineer_features(
    *,
    rzsm_1: float,
    rzsm_2: float,
    rzsm_3: float,
    cumulative_rainfall_3d_mm: float,
    previous: list[dict[str, Any]] = None,
    previous_rainfall: float = float("nan"),
) -> dict[str, float]:

    if previous is None:
        previous = []

    rzsm_mean = calculate_rzsm_mean(
        rzsm_1,
        rzsm_2,
        rzsm_3,
    )

    rzsm_range = calculate_rzsm_range(
        rzsm_1,
        rzsm_2,
        rzsm_3,
    )

    surface_deep_difference = (
        calculate_surface_deep_difference(
            rzsm_1,
            rzsm_3,
        )
    )

    rain_rzsm_interaction = (
        calculate_rain_rzsm_interaction(
            cumulative_rainfall_3d_mm,
            rzsm_mean,
        )
    )

    return {
        "rzsm_mean": rzsm_mean,

        "rzsm_range": rzsm_range,

        "rzsm_surface_deep_diff":
            surface_deep_difference,

        "rain_rzsm_interaction":
            rain_rzsm_interaction,

        # D-1 surface RZSM
        "previous_rzsm": _previous_value(
            previous,
            0,
            "rzsm_1",
        ),

        # D-2 surface RZSM
        "previous_rzsm_2": _previous_value(
            previous,
            1,
            "rzsm_1",
        ),

        # D-3 surface RZSM
        "previous_rzsm_3": _previous_value(
            previous,
            2,
            "rzsm_1",
        ),

        # D-1 3-day rainfall
        "previous_rainfall":
            float(previous_rainfall),

        # Frozen 7/21/72 weighted RZSM
        "rzsm_0_100":
            calculate_rzsm_0_100(
                rzsm_1,
                rzsm_2,
                rzsm_3,
            ),
    }
