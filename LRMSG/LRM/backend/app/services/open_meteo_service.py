from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import requests


OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


HOURLY_VARIABLES = [
    "precipitation",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
]


class DataSourceError(RuntimeError):
    pass


def _parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt.astimezone(timezone.utc)


def _validate(
    payload: dict[str, Any],
) -> tuple[list[str], dict[str, list[Any]]]:

    hourly = payload.get("hourly")

    if not isinstance(hourly, dict):
        raise DataSourceError(
            "Open-Meteo returned no hourly object."
        )

    times = hourly.get("time")

    if not isinstance(times, list):
        raise DataSourceError(
            "Open-Meteo returned no hourly timestamps."
        )

    if len(times) < 96:
        raise DataSourceError(
            "Open-Meteo returned fewer than 96 hourly records."
        )

    series = {}

    for variable in HOURLY_VARIABLES:

        values = hourly.get(variable)

        if not isinstance(values, list):
            raise DataSourceError(
                f"Missing Open-Meteo variable: {variable}"
            )

        if len(values) != len(times):
            raise DataSourceError(
                f"Length mismatch for {variable}."
            )

        series[variable] = values

    return times, series


def fetch_current_environment(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "hourly": ",".join(
            HOURLY_VARIABLES
        ),

        "past_hours": 96,
        "forecast_hours": 1,

        "timezone": "UTC",

        # Prefer a land cell for environmental data.
        "cell_selection": "land",
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

    except requests.RequestException as exc:
        raise DataSourceError(
            f"Open-Meteo request failed: {exc}"
        ) from exc

    except ValueError as exc:
        raise DataSourceError(
            "Open-Meteo returned invalid JSON."
        ) from exc

    times, series = _validate(payload)

    parsed_times = [
        _parse_time(str(t))
        for t in times
    ]

    for i in range(1, len(parsed_times)):
        if parsed_times[i] <= parsed_times[i - 1]:
            raise DataSourceError(
                "Open-Meteo timestamps are not strictly increasing."
            )

    now = datetime.now(timezone.utc)

    valid_indices = [
        i
        for i, t in enumerate(parsed_times)
        if t <= now
    ]

    if not valid_indices:
        raise DataSourceError(
            "No usable observation timestamp returned."
        )

    latest_idx = valid_indices[-1]

    latest_timestamp = parsed_times[
        latest_idx
    ]

    def number(
        variable: str,
        index: int,
    ) -> float:

        value = series[variable][index]

        if value is None:
            raise DataSourceError(
                f"Open-Meteo returned null for {variable}."
            )

        try:
            return float(value)

        except (TypeError, ValueError) as exc:
            raise DataSourceError(
                f"Invalid numeric value for {variable}."
            ) from exc

    rzsm_1 = number(
        "soil_moisture_0_to_7cm",
        latest_idx,
    )

    rzsm_2 = number(
        "soil_moisture_7_to_28cm",
        latest_idx,
    )

    rzsm_3 = number(
        "soil_moisture_28_to_100cm",
        latest_idx,
    )

    # ---------------------------------------------------------
    # EXACTLY 72 hourly observations ending at latest_idx
    # ---------------------------------------------------------

    start_idx = latest_idx - 71

    if start_idx < 0:
        raise DataSourceError(
            "Insufficient rainfall history."
        )

    rainfall_values = []

    for i in range(
        start_idx,
        latest_idx + 1,
    ):

        value = series[
            "precipitation"
        ][i]

        if value is None:
            raise DataSourceError(
                "Rainfall contains missing hourly data."
            )

        value = float(value)

        if value < 0:
            raise DataSourceError(
                "Negative precipitation received."
            )

        rainfall_values.append(value)

    cumulative_rainfall_3d_mm = sum(
        rainfall_values
    )

    # ---------------------------------------------------------
    # Extract temporal observations required by the frozen XGB
    #
    # previous[0] = D-1
    # previous[1] = D-2
    # previous[2] = D-3
    #
    # IMPORTANT:
    # previous_rzsm / previous_rzsm_2 / previous_rzsm_3
    # are all SURFACE RZSM (0-7 cm), at different days.
    # ---------------------------------------------------------

    def index_for_time(target_time: datetime) -> int:
        """
        Find the hourly observation corresponding to target_time.
        We require an exact hourly timestamp so that temporal
        semantics cannot silently shift.
        """

        for i, timestamp in enumerate(parsed_times):
            if timestamp == target_time:
                return i

        raise DataSourceError(
            f"Open-Meteo did not return required hourly timestamp: "
            f"{target_time.isoformat()}"
        )


    # D-1, D-2 and D-3 timestamps
    d1_time = latest_timestamp - timedelta(hours=24)
    d2_time = latest_timestamp - timedelta(hours=48)
    d3_time = latest_timestamp - timedelta(hours=72)

    d1_idx = index_for_time(d1_time)
    d2_idx = index_for_time(d2_time)
    d3_idx = index_for_time(d3_time)


    # Surface RZSM temporal lags
    previous = [
        {
            "rzsm_1": number(
                "soil_moisture_0_to_7cm",
                d1_idx,
            )
        },
        {
            "rzsm_1": number(
                "soil_moisture_0_to_7cm",
                d2_idx,
            )
        },
        {
            "rzsm_1": number(
                "soil_moisture_0_to_7cm",
                d3_idx,
            )
        }
    ]


    # ---------------------------------------------------------
    # D-1 3-day cumulative rainfall
    #
    # 72 hourly observations ending at D-1.
    # ---------------------------------------------------------

    past_rain_start = d1_idx - 71

    if past_rain_start < 0:
        raise DataSourceError(
            "Insufficient rainfall history for D-1 rainfall feature."
        )

    past_rain_values = []

    for i in range(
        past_rain_start,
        d1_idx + 1,
    ):

        value = series["precipitation"][i]

        if value is None:
            raise DataSourceError(
                "Rainfall contains missing hourly data "
                "in D-1 3-day history."
            )

        value = float(value)

        if value < 0:
            raise DataSourceError(
                "Negative precipitation received."
            )

        past_rain_values.append(value)


    previous_rainfall = sum(past_rain_values)

    # ---------------------------------------------------------
    # Sanity validation
    # ---------------------------------------------------------

    for name, value in {
        "rzsm_1": rzsm_1,
        "rzsm_2": rzsm_2,
        "rzsm_3": rzsm_3,
    }.items():

        if not 0.0 <= value <= 1.0:
            raise DataSourceError(
                f"{name}={value} outside 0..1."
            )

    return {
        "source": "Open-Meteo",
        "source_url": OPEN_METEO_URL,

        "timestamp_utc":
            latest_timestamp.isoformat(),

        "rzsm_1": rzsm_1,
        "rzsm_2": rzsm_2,
        "rzsm_3": rzsm_3,

        "cumulative_rainfall_3d_mm":
            float(cumulative_rainfall_3d_mm),
            
        "previous": previous,

        "previous_rainfall":
            float(previous_rainfall),
    }
