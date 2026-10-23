from __future__ import annotations

from typing import Any
import ee


class GEEServiceError(RuntimeError):
    pass


def init_gee(project_id: str = "") -> None:
    try:
        if project_id:
            ee.Initialize(project=project_id)
        else:
            ee.Initialize()
    except Exception as exc:
        raise GEEServiceError(f"Failed to initialize Earth Engine: {exc}") from exc


def fetch_terrain(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    
    try:
        point = ee.Geometry.Point([longitude, latitude])
        
        # Use SRTM Digital Elevation Data
        dataset = ee.Image('USGS/SRTMGL1_003')
        elevation = dataset.select('elevation')
        
        # Calculate slope in degrees
        slope = ee.Terrain.slope(elevation)
        
        # Sample the point
        ele_val = elevation.sample(point, 30).first().get('elevation').getInfo()
        slope_val = slope.sample(point, 30).first().get('slope').getInfo()
        
        if ele_val is None or slope_val is None:
            raise GEEServiceError("GEE returned null for terrain features.")
            
        return {
            "source": "Google Earth Engine (SRTMGL1_003)",
            "elevation_m": float(ele_val),
            "slope_deg": float(slope_val),
        }
        
    except Exception as exc:
        raise GEEServiceError(f"GEE terrain extraction failed: {exc}") from exc
