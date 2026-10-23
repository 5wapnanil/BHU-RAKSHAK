import json
import os
from shapely.geometry import shape
from shapely.strtree import STRtree

class SpatialEngine:
    def __init__(self):
        # Load districts
        districts_path = os.path.join(os.path.dirname(__file__), "../../../frontend/public/ner_districts.json")
        self.districts_fc = {"type": "FeatureCollection", "features": []}
        if os.path.exists(districts_path):
            with open(districts_path, "r", encoding="utf-8") as f:
                self.districts_fc = json.load(f)
            
        self.district_geoms = {}
        for feature in self.districts_fc.get("features", []):
            d_name = feature.get("properties", {}).get("NAME_2")
            if d_name:
                try:
                    self.district_geoms[d_name] = shape(feature["geometry"])
                except Exception:
                    pass
                    
        # Load roads
        roads_path = os.path.join(os.path.dirname(__file__), "../data/ner_highways.geojson")
        self.roads_features = []
        if os.path.exists(roads_path):
            with open(roads_path, "r", encoding="utf-8") as f:
                roads_fc = json.load(f)
                self.roads_features = roads_fc.get("features", [])
        
        self.road_geoms = []
        for feature in self.roads_features:
            try:
                self.road_geoms.append(shape(feature["geometry"]))
            except Exception:
                self.road_geoms.append(None)
                
        # Build index over district geometries
        self.district_names = list(self.district_geoms.keys())
        self.district_shapes = list(self.district_geoms.values())
        if self.district_shapes:
            self.district_tree = STRtree(self.district_shapes)
        else:
            self.district_tree = None

    def analyze_impact(self, district_risks: dict):
        result_features = []
        if not self.district_tree:
            return {"type": "FeatureCollection", "features": []}
            
        for i, road_geom in enumerate(self.road_geoms):
            if road_geom is None:
                continue
                
            road_feat = self.roads_features[i]
            
            # Find candidate districts
            candidate_indices = self.district_tree.query(road_geom)
            
            highest_risk_level = "low"
            highest_risk_score = 0
            intersecting_district = None
            intersecting_districts = set()
            
            for idx in candidate_indices:
                d_name = self.district_names[idx]
                d_shape = self.district_shapes[idx]
                
                # Exact intersection
                if road_geom.intersects(d_shape):
                    intersecting_districts.add(d_name)
                    risk_info = district_risks.get(d_name)
                    if risk_info:
                        score = risk_info.get("risk_score", 0)
                        if score > highest_risk_score:
                            highest_risk_score = score
                            highest_risk_level = risk_info.get("risk_level", "low")
                            intersecting_district = d_name
                            
            impact_level = "no_detected_impact"
            if highest_risk_level == "critical":
                impact_level = "critical"
            elif highest_risk_level == "high":
                impact_level = "high"
            elif highest_risk_level == "moderate":
                impact_level = "moderate"
                
            # If no intersection, check buffer (approx 500m ~ 0.005 deg)
            if impact_level == "no_detected_impact":
                buffered_geom = road_geom.buffer(0.005)
                candidate_indices_buf = self.district_tree.query(buffered_geom)
                for idx in candidate_indices_buf:
                    d_name = self.district_names[idx]
                    d_shape = self.district_shapes[idx]
                    if buffered_geom.intersects(d_shape):
                        intersecting_districts.add(d_name)
                        risk_info = district_risks.get(d_name)
                        if risk_info:
                            level = risk_info.get("risk_level", "low")
                            if level in ["critical", "high"]:
                                impact_level = "high" # Proximate to high risk
                                highest_risk_level = level
                            elif level == "moderate" and impact_level not in ["critical", "high"]:
                                impact_level = "moderate"
                                highest_risk_level = level
                                
            if impact_level != "no_detected_impact":
                feat_copy = road_feat.copy()
                feat_copy["properties"] = {
                    **road_feat["properties"],
                    "impact_level": impact_level,
                    "risk_level": highest_risk_level,
                    "intersection_type": "intersects" if intersecting_district else "buffer",
                    "intersecting_districts": list(intersecting_districts),
                    "distance_to_risk_area_m": 0 if intersecting_district else 500,
                    "source": "GIS_ANALYSIS",
                    "confirmed_blockade": False
                }
                result_features.append(feat_copy)
                
        return {
            "type": "FeatureCollection",
            "features": result_features
        }

# Global singleton
engine = None

def get_spatial_engine() -> SpatialEngine:
    global engine
    if engine is None:
        engine = SpatialEngine()
    return engine
