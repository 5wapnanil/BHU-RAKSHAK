import os

file_path = r'frontend/src/app/alerts/page.tsx'
with open(file_path, 'r') as f:
    code = f.read()

# 1. Remove automatic request
auto_request = '''    // Ask for browser notification permission
    if (typeof window !== "undefined" && "Notification" in window) {
      if (Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission();
      }
    }'''

code = code.replace(auto_request, '')

# 2. Add button
header_old = '''              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, fontFamily: "'Space Grotesk', sans-serif" }}>LATEST WARNINGS</h3>'''

header_new = '''              <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center" }}>
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, fontFamily: "'Space Grotesk', sans-serif" }}>LATEST WARNINGS</h3>
                {typeof window !== "undefined" && "Notification" in window && Notification.permission === "default" && (
                  <button onClick={() => Notification.requestPermission()} style={{ padding: "6px 12px", background: "var(--accent)", color: "white", border: "none", borderRadius: "6px", fontSize: "12px", fontWeight: 600, cursor: "pointer" }}>
                    Enable Browser Notifications
                  </button>
                )}
              </div>'''

code = code.replace(header_old, header_new)

with open(file_path, 'w') as f:
    f.write(code)

print("Patched browser notification UX")
