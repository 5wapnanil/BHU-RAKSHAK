import os

file_path = r'frontend/src/app/alerts/page.tsx'
with open(file_path, 'r') as f:
    code = f.read()

# 1. Fetch initial alerts
initial_fetch_old = '''  useEffect(() => {
    let reconnectTimer: NodeJS.Timeout;

    const connectWebSocket = () => {'''

initial_fetch_new = '''  useEffect(() => {
    const fetchInitialAlerts = async () => {
      try {
        const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
        const res = await fetch(`http://${host}:8004/api/alerts/`);
        if (res.ok) {
          const data = await res.json();
          setAlerts(data);
        }
      } catch (e) {
        console.error("Failed to fetch initial alerts", e);
      }
    };
    fetchInitialAlerts();

    // Ask for browser notification permission
    if (typeof window !== "undefined" && "Notification" in window) {
      if (Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission();
      }
    }

    let reconnectTimer: NodeJS.Timeout;

    const connectWebSocket = () => {'''

code = code.replace(initial_fetch_old, initial_fetch_new)

# 2. Browser Notifications inside WS onmessage
ws_onmessage_old = '''            if (data.type === "NEW_ALERT" && data.alert.severity === "CRITICAL") {
              toast.error(
                <div style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                  <div style={{ fontWeight: 700, fontSize: "14px" }}>🚨 NEW CRITICAL ALERT</div>
                  <div style={{ fontSize: "13px", marginTop: "4px" }}>{data.alert.location_name}, {data.alert.state}</div>
                  <div style={{ fontSize: "12px", marginTop: "2px", opacity: 0.8 }}>{data.alert.risk_probability}% landslide risk detected.</div>
                </div>, 
                { duration: 6000, style: { background: "#1a1a1a", color: "#fff", border: "1px solid var(--red)" } }
              );
            }'''

ws_onmessage_new = '''            if ((data.type === "NEW_ALERT" || data.type === "ALERT_ESCALATED") && (data.alert.severity === "CRITICAL" || data.alert.severity === "HIGH")) {
              const isCritical = data.alert.severity === "CRITICAL";
              toast.error(
                <div style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                  <div style={{ fontWeight: 700, fontSize: "14px" }}>{isCritical ? "🚨 CRITICAL LANDSLIDE ALERT" : "⚠️ HIGH LANDSLIDE RISK DETECTED"}</div>
                  <div style={{ fontSize: "13px", marginTop: "4px" }}>{data.alert.location_name}, {data.alert.state}</div>
                  <div style={{ fontSize: "12px", marginTop: "2px", opacity: 0.8 }}>{data.alert.risk_probability}% landslide risk detected.</div>
                </div>, 
                { duration: 6000, style: { background: "#1a1a1a", color: "#fff", border: isCritical ? "1px solid var(--red)" : "1px solid var(--orange)" } }
              );
              
              if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
                new Notification(isCritical ? "🚨 CRITICAL LANDSLIDE ALERT" : "⚠️ HIGH LANDSLIDE RISK", {
                  body: `Location: ${data.alert.location_name}, ${data.alert.state}\\nRisk: ${data.alert.risk_probability}%`,
                  icon: "/favicon.ico"
                });
              }
            }'''

code = code.replace(ws_onmessage_old, ws_onmessage_new)

# 3. View on Map button
map_button_old = '''<div style={{ padding: "32px", display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "32px" }}>'''

map_button_new = '''<div style={{ padding: "32px", display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "32px" }}>
              <div style={{ gridColumn: "1 / -1", display: "flex", gap: "10px", paddingBottom: "16px", borderBottom: "1px solid var(--line)" }}>
                <a href={`/risk-map?lat=${selectedAlert.latitude}&lng=${selectedAlert.longitude}`} target="_blank" rel="noreferrer" style={{ display: "flex", alignItems: "center", gap: "8px", background: "var(--accent)", color: "white", padding: "10px 20px", borderRadius: "8px", textDecoration: "none", fontWeight: 700, fontSize: "14px" }}>
                  <MapPinned size={16} /> View on Map
                </a>
              </div>'''

code = code.replace(map_button_old, map_button_new)

with open(file_path, 'w') as f:
    f.write(code)

print("Patched frontend alerts page")
