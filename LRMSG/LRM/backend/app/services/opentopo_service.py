import math
import requests
from typing import Any

OPENTOPO_URL = "https://api.opentopodata.org/v1/srtm30m"

class TerrainDataError(RuntimeError):
    pass

def fetch_terrain(latitude: float, longitude: float) -> dict[str, Any]:
    # Use a step of ~30 meters (0.00027 degrees) to match SRTM30 resolution
    step = 0.00027

    # Center, Left, Right, Bottom, Top
    coords = [
        (latitude, longitude),                   # 0: center
        (latitude, longitude - step),            # 1: left
        (latitude, longitude + step),            # 2: right
        (latitude - step, longitude),            # 3: bottom
        (latitude + step, longitude),            # 4: top
    ]

    locations_str = "|".join([f"{lat},{lon}" for lat, lon in coords])

    try:
        response = requests.get(
            OPENTOPO_URL,
            params={"locations": locations_str},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise TerrainDataError(f"OpenTopoData request failed: {exc}") from exc
    except ValueError as exc:
        raise TerrainDataError("OpenTopoData returned invalid JSON.") from exc

    results = payload.get("results")
    if not results or len(results) != 5:
        raise TerrainDataError("OpenTopoData returned insufficient elevation data.")

    elevations = []
    for res in results:
        z = res.get("elevation")
        if z is None:
            raise TerrainDataError("OpenTopoData returned null elevation.")
        elevations.append(float(z))

    z_center = elevations[0]
    z_left   = elevations[1]
    z_right  = elevations[2]
    z_bottom = elevations[3]
    z_top    = elevations[4]

    # Calculate distances in meters
    lat_rad = math.radians(latitude)
    meters_per_deg_lat = 111320.0
    meters_per_deg_lon = 111320.0 * math.cos(lat_rad)

    dx_meters = 2.0 * step * meters_per_deg_lon
    dy_meters = 2.0 * step * meters_per_deg_lat

    # Protect against division by zero at the poles (though unrealistic for landslides)
    if dx_meters <= 0:
        dx_meters = 1.0

    # Calculate partial derivatives
    dz_dx = (z_right - z_left) / dx_meters
    dz_dy = (z_top - z_bottom) / dy_meters

    # Calculate slope in degrees according to the provided formula
    slope_rad = math.atan(math.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = math.degrees(slope_rad)

    return {
        "source": "OpenTopoData (SRTM30m)",
        "elevation_m": z_center,
        "slope_deg": slope_deg,
    }
