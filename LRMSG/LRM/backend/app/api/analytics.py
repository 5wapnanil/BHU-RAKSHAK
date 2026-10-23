from fastapi import APIRouter
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
import os

router = APIRouter()

# Assuming data is located relative to the backend folder
DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "master" / "Landslide_NER_MASTER_2016_ROWS_RAW.csv"

_cached_df = None

def get_data():
    global _cached_df
    if _cached_df is not None:
        return _cached_df.copy()
        
    df_raw = pd.read_csv(DATA_PATH)
    # Parse date and extract year for raw data (needed for filtering)
    df_raw["event_date"] = pd.to_datetime(df_raw["event_date"])
    df_raw["year"] = df_raw["event_date"].dt.year
    df_raw["month_name"] = df_raw["event_date"].dt.strftime("%B")
    _cached_df = df_raw
    return df_raw.copy()

@router.get("/historical")
def get_historical_analytics(year: str = "ALL", state: str = "ALL", month: str = "ALL") -> Dict[str, Any]:
    if not os.path.exists(DATA_PATH):
        return {"error": "Dataset not found"}

    df_raw = get_data()
    
    # Available states for UI dropdown (unfiltered)
    available_states = sorted(df_raw["state"].unique().tolist())
    
    # Apply query filters to raw df
    if year != "ALL":
        df_raw = df_raw[df_raw["year"] == int(year)]
    if state != "ALL":
        df_raw = df_raw[df_raw["state"] == state]
    if month != "ALL":
        df_raw = df_raw[df_raw["month_name"] == month]
        
    # Calculate Correlation Matrix on the raw (filtered by time/space, but including both landslide 0 and 1)
    corr_cols_map = {
        "cumulative_rainfall_3d_mm": "Rainfall (3D)",
        "elevation_m": "Elevation",
        "slope_deg": "Slope",
        "rzsm_1": "Soil Moisture",
        "road_mdr_pct": "Road Density",
        "landslide_occurred": "Landslide Risk"
    }
    
    available_cols = [c for c in corr_cols_map.keys() if c in df_raw.columns]
    
    correlation_data = []
    if not df_raw.empty and len(df_raw["landslide_occurred"].unique()) > 1:
        corr_matrix = df_raw[available_cols].corr().replace([np.nan, np.inf, -np.inf], 0)
        
        # Flatten matrix for frontend
        for col_x in available_cols:
            for col_y in available_cols:
                val = corr_matrix.loc[col_x, col_y]
                correlation_data.append({
                    "factor_x": corr_cols_map[col_x],
                    "factor_y": corr_cols_map[col_y],
                    "value": float(val)
                })
    
    # Now filter for actual landslide events for the rest of the KPIs
    df = df_raw[df_raw["landslide_occurred"] == 1].copy()
    
    # Check if df is empty after filters
    if df.empty:
        return {
            "kpis": {"total_events": 0, "peak_year": None, "peak_month": None, "top_state": None, "recurring_hotspots": 0},
            "yearly_trend": [],
            "monthly_pattern": [],
            "state_distribution": [],
            "heatmap": [],
            "hotspots": [],
            "events": [],
            "correlation_matrix": correlation_data,
            "available_states": available_states
        }
    
    # KPIs
    total_events = len(df)
    
    # Peak year
    yearly_counts = df["year"].value_counts()
    peak_year = int(yearly_counts.idxmax()) if not yearly_counts.empty else None
    
    # Peak month
    monthly_counts = df["month_name"].value_counts()
    peak_month = monthly_counts.idxmax() if not monthly_counts.empty else None
    
    # Top state
    state_counts = df["state"].value_counts()
    top_state = state_counts.idxmax() if not state_counts.empty else None
    
    # Recurring hotspots (districts with events in multiple years or >1 total)
    hotspots_all = df.groupby(["state", "district"]).agg(
        total_events=("landslide_occurred", "count"),
        active_years=("year", "nunique"),
        avg_rainfall=("cumulative_rainfall_3d_mm", "mean"),
        avg_slope=("slope_deg", "mean"),
        avg_elevation=("elevation_m", "mean"),
        common_season=("season", lambda x: pd.Series.mode(x)[0] if not x.empty and not pd.Series.mode(x).empty else "Unknown")
    ).reset_index()
    
    # Filter to only recurring hotspots
    hotspots_all = hotspots_all[hotspots_all["total_events"] > 1].sort_values("total_events", ascending=False)
    
    # The true total number of recurring hotspots
    num_hotspots = len(hotspots_all)
    
    # Only send the top 6 to the UI for performance and UI layout
    hotspots_top6 = hotspots_all.head(6).replace([np.inf, -np.inf, np.nan], None)
    
    hotspots_list = hotspots_top6.to_dict(orient="records")
    
    # Yearly trend
    yearly_trend = [{"year": int(k), "count": int(v)} for k, v in yearly_counts.sort_index().items()]
    
    # Monthly pattern (sort chronologically)
    months_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    monthly_pattern_dict = df["month_name"].value_counts().to_dict()
    monthly_pattern = [{"month": m, "count": int(monthly_pattern_dict.get(m, 0))} for m in months_order]
    
    # State distribution
    state_distribution = [{"state": str(k), "count": int(v)} for k, v in state_counts.items()]
    
    # Year x Region Heatmap
    # Cross tabulation of State and Year
    heatmap_df = pd.crosstab(df["state"], df["year"])
    heatmap_data = []
    for state, row in heatmap_df.iterrows():
        heatmap_data.append({
            "state": state,
            "years": {str(year): int(val) for year, val in row.items()}
        })
    
    # Events for the Map
    # Only sending necessary fields to keep payload small
    events = df[["latitude", "longitude", "year", "month_name", "state", "district", "event_date"]].copy()
    events["event_date"] = events["event_date"].dt.strftime("%Y-%m-%d")
    events_list = events.to_dict("records")

    # Calendar Heatmap Data
    calendar_df = df.groupby(df["event_date"].dt.strftime("%Y-%m-%d")).size().reset_index(name="count")
    calendar_data = []
    for _, row in calendar_df.iterrows():
        calendar_data.append({
            "date": row["event_date"],
            "count": int(row["count"])
        })
    
    return {
        "kpis": {
            "total_events": total_events,
            "peak_year": peak_year,
            "peak_month": peak_month,
            "top_state": top_state,
            "recurring_hotspots": num_hotspots
        },
        "yearly_trend": yearly_trend,
        "monthly_pattern": monthly_pattern,
        "state_distribution": state_distribution,
        "heatmap": heatmap_data,
        "hotspots": hotspots_list,
        "events": events_list,
        "correlation_matrix": correlation_data,
        "calendar_heatmap": calendar_data,
        "available_states": available_states
    }
