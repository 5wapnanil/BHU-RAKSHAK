with open('frontend/src/app/alerts/page.tsx', 'r') as f:
    code = f.read()

import_statement = '''import staticFeatures from "@/mock/static_features.json";
import { Loader2 } from "lucide-react";'''
code = code.replace('import { toast, Toaster } from "react-hot-toast";', 'import { toast, Toaster } from "react-hot-toast";\n' + import_statement)

code = code.replace('const [demoMode, setDemoMode] = useState(false);', 'const [demoMode, setDemoMode] = useState(false);\n  const [scanning, setScanning] = useState(false);\n  const [scanStatus, setScanStatus] = useState("");')

scan_func = '''
  const scanLiveConditions = async () => {
    setScanning(true);
    setScanStatus("Getting GPS Location...");
    const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    
    let userLoc = null;
    try {
      userLoc = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
          err => resolve(null),
          { timeout: 5000 }
        );
      });
    } catch(e) {}

    const locations = [...staticFeatures];
    if (userLoc) {
      locations.push({
        name: "Your Location",
        state: "Detected",
        lat: userLoc.lat,
        lng: userLoc.lng,
        elevation: 500,
        slope: 25,
        soilType: "Acrisols"
      });
    }

    setScanStatus("Fetching Weather Data...");
    const weatherMap = new Map();
    const lats = locations.map(l => l.lat).join(",");
    const lngs = locations.map(l => l.lng).join(",");
    try {
      const weatherRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lats}&longitude=${lngs}&hourly=precipitation,soil_moisture_0_to_7cm&past_hours=72&forecast_hours=1`);
      if (weatherRes.ok) {
        const data = await weatherRes.json();
        locations.forEach((loc, idx) => {
           const locData = Array.isArray(data) ? data[idx] : data;
           const precips = locData?.hourly?.precipitation || [];
           const moistures = locData?.hourly?.soil_moisture_0_to_7cm || [];
           const rainfall = precips.reduce((a, b) => a + (b || 0), 0);
           const soilMoisture = moistures.length > 0 ? (moistures[moistures.length - 1] || 0.3) : 0.3;
           weatherMap.set(loc.name, { rainfall, soilMoisture });
        });
      }
    } catch(e) {}

    setScanStatus("Running ML Predictions...");
    
    let activeAlertsFound = 0;
    for (let i = 0; i < locations.length; i++) {
        const point = locations[i];
        const weather = weatherMap.get(point.name) || { rainfall: 0, soilMoisture: 0.3 };
        try {
          const res = await fetch(`http://${host}:8004/prediction/custom`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              rainfall: weather.rainfall,
              soilMoisture: weather.soilMoisture,
              elevation: point.elevation,
              slope: point.slope,
              soilType: point.soilType
            }),
          });
          if (res.ok) {
            const data = await res.json();
            const prob = data.final_decision.calibrated_probability;
            if (prob >= 0.3) {
              activeAlertsFound++;
              await fetch(`http://${host}:8004/api/alerts/demo/trigger`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  district: point.name, state: point.state, location_name: point.name,
                  lat: point.lat, lng: point.lng, prob: prob, rainfall: weather.rainfall, soil: weather.soilMoisture, slope: point.slope
                })
              });
            }
          }
        } catch(e) {}
    }
    setScanning(false);
    toast.success(`Scan complete! ${activeAlertsFound} new alert(s) generated.`);
  };
'''

code = code.replace('const triggerDemoAlert = async () => {', scan_func + '\n  const triggerDemoAlert = async () => {')

ui_button = '''
          <button onClick={scanLiveConditions} disabled={scanning} style={{ background: "var(--text-primary)", color: "var(--surface)", border: "none", padding: "8px 16px", borderRadius: "6px", fontSize: "13px", cursor: scanning ? "not-allowed" : "pointer", fontWeight: 600, display: "flex", alignItems: "center", gap: "8px" }}>
            {scanning ? <Loader2 size={16} className="animate-spin" /> : <Activity size={16} />}
            {scanning ? scanStatus : "SCAN REGION (GPS + NER)"}
          </button>
'''
code = code.replace('Last updated: Just now\n          </div>', 'Last updated: Just now\n          </div>\n' + ui_button)

with open('frontend/src/app/alerts/page.tsx', 'w') as f:
    f.write(code)
print("Patched frontend")
