from __future__ import annotations

from typing import Any

import requests


SOILGRIDS_URL = (
    "https://rest.isric.org/"
    "soilgrids/v2.0/classification/query"
)


SUPPORTED_SOILS = {
    "Acrisols",
    "Cambisols",
    "Fluvisols",
    "Leptosols",
    "Luvisols",
    "Vertisols",
}


class SoilDataError(RuntimeError):
    pass


def fetch_wrb_soil(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:

    try:

        response = requests.get(
            SOILGRIDS_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "number_classes": 5,
            },
            headers={
                "accept": "application/json"
            },
            timeout=60,
        )

        response.raise_for_status()

        payload = response.json()

    except requests.RequestException as exc:

        raise SoilDataError(
            f"SoilGrids request failed: {exc}"
        ) from exc

    except ValueError as exc:

        raise SoilDataError(
            "SoilGrids returned invalid JSON."
        ) from exc

    soil_type = payload.get(
        "wrb_class_name"
    )

    if not soil_type:

        raise SoilDataError(
            "No WRB class returned."
        )

    if soil_type not in SUPPORTED_SOILS:

        raise SoilDataError(
            f"Unsupported WRB class: {soil_type}. "
            f"Supported classes: "
            f"{sorted(SUPPORTED_SOILS)}"
        )

    return {
        "source": "ISRIC SoilGrids",
        "source_url": SOILGRIDS_URL,
        "soil_type_wrb": soil_type,
    }
