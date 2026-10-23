import json
import os
import math
from typing import List, Dict, Any

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contacts_db.json")

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class ContactsService:
    def __init__(self):
        self.contacts = self._load_contacts()

    def _load_contacts(self) -> List[Dict[str, Any]]:
        if not os.path.exists(DATA_PATH):
            return []
        try:
            with open(DATA_PATH, "r") as f:
                return json.load(f)
        except:
            return []
            
    def get_affected_contacts(self, lat: float, lng: float) -> List[Dict[str, Any]]:
        affected = []
        for c in self.contacts:
            if not c.get("sms_enabled", False): continue
            
            dist = _haversine_km(lat, lng, c["latitude"], c["longitude"])
            if dist <= c.get("alert_radius_km", 50.0):
                affected.append(c)
        return affected

contacts_service = ContactsService()
