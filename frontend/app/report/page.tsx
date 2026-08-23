"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { LocationSearch, GeoResult } from "@/components/LocationSearch";
import { enqueueOperation } from "@/lib/offline/queue";
import { useOnline } from "@/hooks/useOnline";
import { api } from "@/lib/axios";
import { IncidentSeverity } from "@/lib/types";
import { AlertCircle, CheckCircle2, Send, WifiOff, ShieldAlert, MapPin, ArrowRight } from "lucide-react";

export default function ReportPage() {
  const router = useRouter();
  const isOnline = useOnline();

  const [content, setContent] = useState("");
  const [severity, setSeverity] = useState<IncidentSeverity>("medium");
  const [selectedGeo, setSelectedGeo] = useState<GeoResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const operation_id = crypto.randomUUID();

    if (!isOnline) {
      // Offline mode: queue report with geographic metadata
      const offlinePayload = {
        operation_id,
        content,
        severity,
        location: selectedGeo ? {
          name: selectedGeo.name,
          formatted_address: selectedGeo.formatted_address,
          lat: selectedGeo.lat,
          lng: selectedGeo.lng,
          region: selectedGeo.city || selectedGeo.state || selectedGeo.country || "Global",
        } : null,
        created_at: new Date().toISOString(),
      };
      try {
        await enqueueOperation("create_report", offlinePayload);
        setSuccessMsg("FIELD REPORT ENQUEUED OFFLINE: Data saved to local queue. Will auto-sync when online.");
        setContent("");
        setSelectedGeo(null);
      } catch (err: any) {
        setErrorMsg("Failed to save offline report: " + err.message);
      } finally {
        setSubmitting(false);
      }
    } else {
      // Online mode: create location in CockroachDB if selected, then create incident
      try {
        let locationId: string | undefined = undefined;

        if (selectedGeo) {
          // Register new real-time geocoded location in CockroachDB
          const locRes = await api.post("/locations", {
            name: selectedGeo.name,
            lat: selectedGeo.lat,
            lng: selectedGeo.lng,
            region: selectedGeo.city || selectedGeo.state || selectedGeo.country || "Global",
            type: "other",
            description: selectedGeo.formatted_address,
          });
          locationId = locRes.data.id;
        }

        // Post incident linked to CockroachDB location
        await api.post("/incidents", {
          type: "flood",
          description: content,
          severity,
          location_id: locationId,
        });

        setSuccessMsg(`INCIDENT COMMITTED TO COCKROACHDB: Positioned at ${selectedGeo ? selectedGeo.name : "unassigned location"}. Redirecting to Command Center map…`);
        setContent("");
        setSelectedGeo(null);

        // Auto-redirect to Command Center to view live map & telemetry log
        setTimeout(() => {
          router.push("/");
        }, 1200);
      } catch (err: any) {
        console.warn("Incident creation failed, falling back to report queue:", err);
        const offlinePayload = { operation_id, content, severity, created_at: new Date().toISOString() };
        await enqueueOperation("create_report", offlinePayload);
        setSuccessMsg("NETWORK ANOMALY: Report saved locally into offline sync queue.");
        setContent("");
        setSelectedGeo(null);
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#080B10] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-3xl w-full mx-auto px-3 sm:px-6 py-6 space-y-4">
        {/* HEADER PANEL */}
        <div className="bg-[#0D121D] border border-[#1E293B] p-4 rounded-lg flex items-center justify-between">
          <div>
            <h1 className="text-base font-bold text-white tracking-wider uppercase flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-orange-500" />
              <span>Field Incident &amp; Observation Telemetry</span>
            </h1>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Submit observations. Search any location globally (city, road, landmark, or address) to place on crisis map.
            </p>
          </div>
          <span className="hidden sm:inline font-mono text-[10px] text-slate-400 bg-[#111722] px-2 py-1 rounded border border-[#1E293B]">
            OPS-IN-01
          </span>
        </div>

        {/* Offline Banner */}
        {!isOnline && (
          <div className="bg-amber-950/40 border border-amber-800 rounded-lg p-3 flex items-center gap-3 text-amber-300 text-xs font-mono">
            <WifiOff className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold block">OFFLINE FIELD MODE ACTIVE</span>
              <span>Reports will be stored locally in IndexedDB and automatically pushed to CockroachDB when reconnected.</span>
            </div>
          </div>
        )}

        {/* Success Alert */}
        {successMsg && (
          <div className="bg-emerald-950/40 border border-emerald-800 rounded-lg p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-emerald-300 text-xs font-mono">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
            <button
              onClick={() => router.push("/")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-900/80 hover:bg-emerald-800 border border-emerald-700 text-white font-bold shrink-0 transition-colors cursor-pointer"
            >
              <span>View on Map</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="bg-red-950/40 border border-red-800 rounded-lg p-3 flex items-center gap-2.5 text-red-300 text-xs font-mono">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-5 space-y-4 shadow-xl">

          {/* Content */}
          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
              Field Report Content *
            </label>
            <textarea
              required
              rows={4}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="e.g. Road 17 near Shelter 7 is completely blocked by flooding. Water level 1.2m."
              className="w-full bg-[#080B10] border border-[#1E293B] rounded-lg p-3 text-xs sm:text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500"
            />
          </div>

          {/* Free-Text Real-Time Location Search (Uber/Rapido style) */}
          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-orange-400" />
              Incident Location (Real-Time Global Search)
            </label>
            <LocationSearch
              value={selectedGeo}
              onChange={(geo) => setSelectedGeo(geo)}
              placeholder="Search city, area, road, landmark or address (e.g. YMCA Road, Jubilee Hills)..."
            />
          </div>

          {/* Severity */}
          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
              Assessed Severity Level
            </label>
            <div className="grid grid-cols-4 gap-2 font-mono">
              {(["critical", "high", "medium", "low"] as IncidentSeverity[]).map((sev) => (
                <button
                  key={sev}
                  type="button"
                  onClick={() => setSeverity(sev)}
                  className={`py-2 px-3 rounded text-xs font-bold uppercase transition-all border cursor-pointer ${
                    severity === sev
                      ? sev === "critical"
                        ? "bg-red-950/80 border-red-500 text-red-300"
                        : sev === "high"
                        ? "bg-orange-950/80 border-orange-500 text-orange-300"
                        : sev === "medium"
                        ? "bg-amber-950/80 border-amber-500 text-amber-300"
                        : "bg-slate-800 border-slate-500 text-slate-200"
                      : "bg-[#080B10] border-[#1E293B] text-slate-400 hover:bg-[#111722]"
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>

          {/* Quick Scenario Fillers */}
          <div className="bg-[#080B10] p-3 rounded border border-[#1E293B] text-[11px] font-mono text-slate-400 space-y-1">
            <span className="font-bold text-slate-300 uppercase block mb-1">
              Field Scenario Shortcuts:
            </span>
            <button
              type="button"
              onClick={() => {
                setContent("Road 17 is flooded near Shelter 7. Truck access completely cut off.");
                setSeverity("critical");
                setSelectedGeo({
                  place_id: "road-17-junction",
                  display_name: "Road 17 Junction, Region Alpha",
                  name: "Road 17 Junction",
                  formatted_address: "Road 17 Junction, Region Alpha Sector",
                  lat: 28.608,
                  lng: 77.200,
                  city: "Region Alpha",
                  state: "Delhi NCR",
                  country: "India",
                });
              }}
              className="block text-left text-orange-400 hover:text-orange-300 transition-colors cursor-pointer"
            >
              • &quot;Road 17 is flooded near Shelter 7...&quot;
            </button>
            <button
              type="button"
              onClick={() => {
                setContent("Shelter Alpha water reserve exhausted — 80 units remaining for 420 individuals.");
                setSeverity("critical");
                setSelectedGeo({
                  place_id: "shelter-alpha",
                  display_name: "Shelter Alpha, Region Alpha",
                  name: "Shelter Alpha",
                  formatted_address: "Shelter Alpha Relief Sector",
                  lat: 28.618,
                  lng: 77.215,
                  city: "Region Alpha",
                  state: "Delhi NCR",
                  country: "India",
                });
              }}
              className="block text-left text-orange-400 hover:text-orange-300 transition-colors cursor-pointer"
            >
              • &quot;Shelter Alpha water reserve exhausted...&quot;
            </button>
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={submitting || !content.trim()}
              className="w-full py-3 px-4 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white font-mono font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-sm"
            >
              <Send className="w-4 h-4" />
              <span>
                {submitting
                  ? "TRANSMITTING TELEMETRY..."
                  : isOnline
                  ? "COMMIT INCIDENT TO COCKROACHDB"
                  : "SAVE TO OFFLINE SYNC OUTBOX"}
              </span>
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
