"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { useNetworkStatus } from "@/contexts/NetworkContext";
import { queueOperation } from "@/lib/syncManager";
import { API_URL } from "@/lib/api";
import { submitFieldReportDirectly } from "@/lib/fieldReports";
import {
  Camera,
  MapPin,
  Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  RefreshCcw,
  Navigation,
  ArrowLeft,
  Info,
  ShieldAlert,
  Image as ImageIcon,
  X
} from "lucide-react";

export default function ReportPage() {
  const { isOnline, pendingCount, isSyncingState } = useNetworkStatus();

  const [form, setForm] = useState({
    location: "",
    latitude: "",
    longitude: "",
    description: "",
    reporterName: "",
    reporterPhone: "",
  });

  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [photoName, setPhotoName] = useState<string | null>(null);
  const [detectingGps, setDetectingGps] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [isOfflineSaved, setIsOfflineSaved] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        alert("Please select an image file (JPEG, PNG, WEBP).");
        return;
      }
      setPhotoName(file.name);
      const url = URL.createObjectURL(file);
      setPhotoPreview(url);
    }
  };

  const removePhoto = () => {
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoPreview(null);
    setPhotoName(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const detectLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    setDetectingGps(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((prev) => ({
          ...prev,
          latitude: pos.coords.latitude.toFixed(6),
          longitude: pos.coords.longitude.toFixed(6),
        }));
        setDetectingGps(false);
      },
      (err) => {
        setDetectingGps(false);
        alert(`Location detection failed: ${err.message}. Please enter coordinates manually.`);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const fileToDataUrl = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg("");
    setIsOfflineSaved(false);

    const opId = "op_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9);

    const latVal = form.latitude ? parseFloat(form.latitude) : undefined;
    const lngVal = form.longitude ? parseFloat(form.longitude) : undefined;
    const attachedFile = fileInputRef.current?.files?.[0];

    // Safely encode photo as data URL if attached so it survives in offline IndexedDB
    let photoDataUrl: string | undefined;
    if (attachedFile) {
      try {
        photoDataUrl = await fileToDataUrl(attachedFile);
      } catch (encodeErr) {
        console.warn("Could not encode photo for offline queue:", encodeErr);
      }
    }

    // Build payload for offline storage and queued synchronization
    const payload = {
      notes: form.description,
      location_name: form.location,
      latitude: latVal,
      longitude: lngVal,
      reporter_name: form.reporterName || undefined,
      reporter_phone: form.reporterPhone || undefined,
      photo_data: photoDataUrl,
      photo_name: attachedFile?.name,
      photo_mime: attachedFile?.type,
      submittedAt: new Date().toISOString(),
    };

    try {
      if (!isOnline) {
        await queueOperation({
          id: opId,
          operationType: "CREATE",
          entityType: "field_report",
          payload,
        });
        setIsOfflineSaved(true);
        setStatusMsg(
          attachedFile
            ? "Report and photo saved to offline queue. It will automatically synchronize when network returns."
            : "Report saved to offline queue. It will automatically synchronize when network returns."
        );
        resetForm();
      } else {
        // Direct submission to the dedicated FieldReport API
        const formData = new FormData();
        formData.append("notes", form.description);
        if (form.location) formData.append("location_name", form.location);
        if (latVal !== undefined && !isNaN(latVal)) formData.append("latitude", String(latVal));
        if (lngVal !== undefined && !isNaN(lngVal)) formData.append("longitude", String(lngVal));
        if (form.reporterName) formData.append("reporter_name", form.reporterName);
        if (form.reporterPhone) formData.append("reporter_phone", form.reporterPhone);
        if (attachedFile) {
          formData.append("photo", attachedFile);
        }

        const res = await submitFieldReportDirectly(formData);

        if (res.success) {
          setStatusMsg("Field observation synchronized successfully with central server.");
          resetForm();
        } else {
          throw new Error(res.error || "SERVER_REJECT");
        }
      }
    } catch (err: any) {
      if (err.message?.includes("HTTP_REJECT") || err.message?.includes("Server rejected")) {
        setIsOfflineSaved(false);
        setStatusMsg("Submission rejected by server: " + err.message);
      } else {
        // Fallback to offline queue with preserved photo data
        console.warn("Direct upload failed, saving to local offline queue:", err);
        await queueOperation({
          id: opId,
          operationType: "CREATE",
          entityType: "field_report",
          payload,
        });
        setIsOfflineSaved(true);
        setStatusMsg(
          attachedFile
            ? "Network issue during submission. Report and photo safely queued locally and will retry automatically."
            : "Network issue during submission. Report safely queued locally and will retry automatically."
        );
        resetForm();
      }
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm({
      location: "",
      latitude: "",
      longitude: "",
      description: "",
      reporterName: "",
      reporterPhone: "",
    });
    removePhoto();
  };

  return (
    <main style={{ minHeight: "calc(100vh - 64px)", backgroundColor: "var(--paper)", padding: "40px 5vw 80px" }}>
      <div style={{ maxWidth: "720px", margin: "0 auto" }}>
        {/* Navigation Breadcrumb */}
        <Link
          href="/"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            font: "600 12px 'DM Mono'",
            color: "var(--text-secondary)",
            textDecoration: "none",
            marginBottom: "24px",
            letterSpacing: "0.5px",
          }}
        >
          <ArrowLeft size={14} /> Back to Overview
        </Link>

        {/* Card Container */}
        <div className="card" style={{ padding: "40px 36px" }}>
          <div style={{ marginBottom: "32px", borderBottom: "1px solid var(--line)", paddingBottom: "24px" }}>
            <p className="eyebrow" style={{ marginBottom: "6px" }}>COMMUNITY GROUND EVIDENCE</p>
            <h1 style={{ font: "700 clamp(24px, 4vw, 32px) 'Space Grotesk'", letterSpacing: "-0.5px", color: "var(--text-primary)", margin: "0 0 10px" }}>
              Submit Landslide Field Observation
            </h1>
            <p style={{ font: "400 14px/1.6 'DM Sans'", color: "var(--text-secondary)", margin: 0 }}>
              Document ground instability symptoms, rockfall, tension cracks, or drainage blockage. Your report will be cataloged for administrative verification and response coordination.
            </p>
          </div>

          {/* Network Sync Status Indicator */}
          <div
            style={{
              padding: "12px 16px",
              borderRadius: "6px",
              backgroundColor: isOnline ? "#f0fdf4" : "#fef2f2",
              color: isOnline ? "#166534" : "#991b1b",
              border: `1px solid ${isOnline ? "#bbf7d0" : "#fecaca"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "24px",
              font: "600 12px 'DM Mono'",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: isOnline ? "#22c55e" : "#ef4444" }} />
              <span>{isOnline ? "LIVE SYNC ACTIVE" : "OFFLINE MODE — REPORTS QUEUED LOCALLY"}</span>
            </div>
            {pendingCount > 0 && (
              <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#475569" }}>
                <RefreshCcw size={13} className={isSyncingState ? "animate-spin" : ""} />
                {pendingCount} queued
              </span>
            )}
          </div>

          {/* Status Alert */}
          {statusMsg && (
            <div
              style={{
                padding: "16px",
                borderRadius: "8px",
                backgroundColor: isOfflineSaved ? "#fffbeb" : "#f0fdf4",
                color: isOfflineSaved ? "#92400e" : "#166534",
                border: `1px solid ${isOfflineSaved ? "#fde68a" : "#bbf7d0"}`,
                display: "flex",
                alignItems: "flex-start",
                gap: "12px",
                marginBottom: "28px",
                font: "500 13px/1.5 'DM Sans'",
              }}
            >
              {isOfflineSaved ? <AlertCircle size={18} style={{ color: "#d97706", flexShrink: 0, marginTop: "2px" }} /> : <CheckCircle size={18} style={{ color: "#16a34a", flexShrink: 0, marginTop: "2px" }} />}
              <div>{statusMsg}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Field: Location Name */}
            <div>
              <label style={{ display: "block", font: "600 13px 'DM Mono'", color: "var(--text-primary)", marginBottom: "8px", letterSpacing: "0.5px" }}>
                LOCATION / LANDMARK <span style={{ color: "var(--red)" }}>*</span>
              </label>
              <input
                required
                type="text"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                placeholder="E.g. NH-13 KM 42, near Tawang River Bend"
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  borderRadius: "6px",
                  border: "1px solid var(--line)",
                  backgroundColor: "var(--surface)",
                  color: "var(--text-primary)",
                  font: "400 14px 'DM Sans'",
                  outline: "none",
                }}
              />
            </div>

            {/* Field: Coordinates */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <label style={{ font: "600 13px 'DM Mono'", color: "var(--text-primary)", letterSpacing: "0.5px" }}>
                  GPS COORDINATES (OPTIONAL)
                </label>
                <button
                  type="button"
                  onClick={detectLocation}
                  disabled={detectingGps}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    background: "transparent",
                    border: "none",
                    color: "var(--accent-text)",
                    font: "600 12px 'DM Mono'",
                    cursor: detectingGps ? "not-allowed" : "pointer",
                  }}
                >
                  <Navigation size={13} className={detectingGps ? "animate-spin" : ""} />
                  {detectingGps ? "Detecting..." : "Detect Location"}
                </button>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <input
                  type="number"
                  step="any"
                  value={form.latitude}
                  onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                  placeholder="Latitude (e.g. 27.5852)"
                  style={{
                    width: "100%",
                    padding: "12px 14px",
                    borderRadius: "6px",
                    border: "1px solid var(--line)",
                    backgroundColor: "var(--surface)",
                    color: "var(--text-primary)",
                    font: "400 14px 'DM Sans'",
                    outline: "none",
                  }}
                />
                <input
                  type="number"
                  step="any"
                  value={form.longitude}
                  onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                  placeholder="Longitude (e.g. 91.8654)"
                  style={{
                    width: "100%",
                    padding: "12px 14px",
                    borderRadius: "6px",
                    border: "1px solid var(--line)",
                    backgroundColor: "var(--surface)",
                    color: "var(--text-primary)",
                    font: "400 14px 'DM Sans'",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            {/* Field: Observation Description */}
            <div>
              <label style={{ display: "block", font: "600 13px 'DM Mono'", color: "var(--text-primary)", marginBottom: "8px", letterSpacing: "0.5px" }}>
                OBSERVED SLOPE CONDITIONS <span style={{ color: "var(--red)" }}>*</span>
              </label>
              <textarea
                required
                rows={4}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Describe visible features: width/length of surface cracks, displaced trees, mud or rock run-out, active seepage, retaining wall tilting, or road subsidence..."
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  borderRadius: "6px",
                  border: "1px solid var(--line)",
                  backgroundColor: "var(--surface)",
                  color: "var(--text-primary)",
                  font: "400 14px/1.5 'DM Sans'",
                  outline: "none",
                }}
              />
            </div>

            {/* Field: Photograph Upload */}
            <div>
              <label style={{ display: "block", font: "600 13px 'DM Mono'", color: "var(--text-primary)", marginBottom: "8px", letterSpacing: "0.5px" }}>
                FIELD PHOTOGRAPH (ATTACH EVIDENCE)
              </label>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                style={{ display: "none" }}
              />

              {!photoPreview ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    border: "2px dashed var(--line)",
                    borderRadius: "8px",
                    padding: "28px",
                    textAlign: "center",
                    cursor: "pointer",
                    backgroundColor: "var(--surface)",
                    transition: "border-color 0.2s ease",
                  }}
                >
                  <Camera size={28} style={{ color: "var(--text-secondary)", margin: "0 auto 10px" }} />
                  <div style={{ font: "600 13px 'DM Sans'", color: "var(--text-primary)", marginBottom: "4px" }}>
                    Click to select or capture a field photo
                  </div>
                  <div style={{ font: "400 11px 'DM Mono'", color: "var(--text-secondary)" }}>
                    Supported: JPG, PNG, WEBP (Max 10MB)
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    position: "relative",
                    borderRadius: "8px",
                    overflow: "hidden",
                    border: "1px solid var(--line)",
                    backgroundColor: "#000",
                    maxHeight: "260px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <img
                    src={photoPreview}
                    alt="Field evidence preview"
                    style={{ maxWidth: "100%", maxHeight: "260px", objectFit: "contain" }}
                  />
                  <button
                    type="button"
                    onClick={removePhoto}
                    style={{
                      position: "absolute",
                      top: "10px",
                      right: "10px",
                      background: "rgba(0,0,0,0.75)",
                      color: "#fff",
                      border: "none",
                      borderRadius: "50%",
                      width: "30px",
                      height: "30px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                    }}
                  >
                    <X size={16} />
                  </button>
                  <div
                    style={{
                      position: "absolute",
                      bottom: 0,
                      left: 0,
                      right: 0,
                      padding: "8px 14px",
                      background: "rgba(0,0,0,0.65)",
                      color: "#fff",
                      font: "500 11px 'DM Mono'",
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <span>{photoName}</span>
                    <span style={{ color: "#86efac" }}>Preview Active</span>
                  </div>
                </div>
              )}

              <div style={{ display: "flex", gap: "6px", alignItems: "flex-start", marginTop: "8px" }}>
                <Info size={14} style={{ color: "var(--text-secondary)", flexShrink: 0, marginTop: "2px" }} />
                <span style={{ font: "400 11px 'DM Sans'", color: "var(--text-secondary)" }}>
                  Photo preview active. Textual observation and GPS coordinates are stored in Phase 1. Image persistence will activate upon Phase 2 backend multipart storage deployment.
                </span>
              </div>
            </div>

            {/* Field: Reporter Contact Information (Optional) */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label style={{ display: "block", font: "600 12px 'DM Mono'", color: "var(--text-primary)", marginBottom: "6px" }}>
                  REPORTER NAME (OPTIONAL)
                </label>
                <input
                  type="text"
                  value={form.reporterName}
                  onChange={(e) => setForm({ ...form, reporterName: e.target.value })}
                  placeholder="Your full name"
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--line)",
                    backgroundColor: "var(--surface)",
                    color: "var(--text-primary)",
                    font: "400 13px 'DM Sans'",
                    outline: "none",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", font: "600 12px 'DM Mono'", color: "var(--text-primary)", marginBottom: "6px" }}>
                  PHONE NUMBER (OPTIONAL)
                </label>
                <input
                  type="tel"
                  value={form.reporterPhone}
                  onChange={(e) => setForm({ ...form, reporterPhone: e.target.value })}
                  placeholder="For official verification"
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--line)",
                    backgroundColor: "var(--surface)",
                    color: "var(--text-primary)",
                    font: "400 13px 'DM Sans'",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: "12px",
                backgroundColor: "var(--accent)",
                color: "#ffffff",
                padding: "16px",
                borderRadius: "8px",
                border: "none",
                font: "700 14px 'DM Mono'",
                letterSpacing: "0.5px",
                cursor: loading ? "not-allowed" : "pointer",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: "10px",
                opacity: loading ? 0.7 : 1,
                boxShadow: "0 4px 12px rgba(139, 69, 19, 0.2)",
              }}
            >
              {loading && <Loader2 size={18} className="animate-spin" />}
              <span>{loading ? "PROCESSING REPORT..." : "SUBMIT FIELD REPORT"}</span>
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
