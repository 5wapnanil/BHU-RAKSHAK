"use client";

import { useNetworkStatus } from "@/contexts/NetworkContext";
import { Cloud, CloudOff, CloudDrizzle, RefreshCw, AlertTriangle } from "lucide-react";

export function SyncStatusBar() {
  const { isOnline, pendingCount, failedCount, isSyncingState, syncNow } = useNetworkStatus();

  // If entirely online and no operations queued/failed/syncing, hide to be non-intrusive
  if (isOnline && pendingCount === 0 && failedCount === 0 && !isSyncingState) {
    return null;
  }

  const totalPending = pendingCount + failedCount;
  
  // Determine state
  let state = "ONLINE";
  let Icon = Cloud;
  let colorClass = "bg-green-100 text-green-800 border-green-200";
  let iconColor = "#16a34a";
  
  if (!isOnline) {
    state = "OFFLINE";
    Icon = CloudOff;
    colorClass = "bg-red-100 text-red-800 border-red-200";
    iconColor = "#dc2626";
  } else if (isSyncingState) {
    state = "SYNCING";
    Icon = RefreshCw;
    colorClass = "bg-blue-100 text-blue-800 border-blue-200";
    iconColor = "#2563eb";
  } else if (failedCount > 0) {
    state = "ERROR";
    Icon = AlertTriangle;
    colorClass = "bg-yellow-100 text-yellow-800 border-yellow-200";
    iconColor = "#ca8a04";
  }

  const showSyncNow = isOnline && totalPending > 0 && !isSyncingState;

  return (
    <div style={{
      position: "fixed",
      bottom: "24px",
      right: "24px",
      zIndex: 9999,
      display: "flex",
      alignItems: "center",
      gap: "12px",
      padding: "10px 16px",
      borderRadius: "8px",
      backgroundColor: "#fff",
      boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
      fontFamily: "'DM Sans', sans-serif",
      fontSize: "14px",
      fontWeight: 600,
      border: "1px solid #e5e7eb"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", color: iconColor }}>
        <Icon size={18} className={isSyncingState ? "animate-spin" : ""} />
        <span style={{ fontWeight: 700 }}>{state}</span>
      </div>
      
      {totalPending > 0 && (
        <div style={{ color: "#4b5563", borderLeft: "1px solid #e5e7eb", paddingLeft: "12px" }}>
          {totalPending} report{totalPending === 1 ? "" : "s"} pending
        </div>
      )}

      {showSyncNow && (
        <button 
          onClick={syncNow}
          style={{
            marginLeft: "8px",
            padding: "4px 12px",
            backgroundColor: "#f3f4f6",
            border: "1px solid #d1d5db",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "12px",
            fontWeight: 700,
            color: "#374151"
          }}
          onMouseOver={e => e.currentTarget.style.backgroundColor = "#e5e7eb"}
          onMouseOut={e => e.currentTarget.style.backgroundColor = "#f3f4f6"}
        >
          Sync Now
        </button>
      )}
    </div>
  );
}
