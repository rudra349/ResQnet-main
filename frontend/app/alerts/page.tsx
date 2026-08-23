"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/axios";
import { Alert } from "@/lib/types";
import { AlertOctagon, ShieldAlert, Plus, Radio } from "lucide-react";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  // Simulated alert form state
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState<"extreme" | "severe" | "moderate" | "minor">("severe");
  const [region, setRegion] = useState("Region Alpha");

  const fetchAlerts = async () => {
    try {
      const res = await api.get("/alerts");
      setAlerts(res.data);
    } catch (err) {
      console.error("Alerts error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    try {
      await api.post("/alerts", {
        source: "government",
        type: "disaster_warning",
        severity,
        region,
        message,
      });
      setMessage("");
      setShowForm(false);
      fetchAlerts();
    } catch (err) {
      console.error("Alert create error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Radio className="w-5 h-5 text-red-500 animate-pulse" />
              DISASTER WARNINGS & GOVERNMENT ALERTS
            </h1>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Public emergency warnings stored as operational memory for AI context
            </p>
          </div>

          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-medium text-xs shadow-lg shadow-red-600/20 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Simulate Government Alert</span>
          </button>
        </div>

        {/* Create Alert Form Modal/Panel */}
        {showForm && (
          <form onSubmit={handleCreateAlert} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-2xl">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Emit Simulated Emergency Alert
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Region</label>
                <input
                  type="text"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Severity</label>
                <select
                  value={severity}
                  onChange={(e: any) => setSeverity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white"
                >
                  <option value="extreme">Extreme</option>
                  <option value="severe">Severe</option>
                  <option value="moderate">Moderate</option>
                  <option value="minor">Minor</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">Alert Message</label>
              <textarea
                required
                rows={2}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="e.g. Flash flood warning issued for Sector 4. Evacuate immediately."
                className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 text-xs text-white"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-3 py-1.5 rounded bg-slate-800 text-slate-400 text-xs hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded bg-red-600 text-white text-xs font-bold hover:bg-red-500"
              >
                Publish Alert & Store Memory
              </button>
            </div>
          </form>
        )}

        {/* Alerts Feed */}
        <div className="space-y-3">
          {loading ? (
            <div className="text-xs text-slate-500 font-mono py-8 text-center">Loading warnings...</div>
          ) : alerts.length === 0 ? (
            <div className="text-xs text-slate-500 font-mono py-8 text-center">No active alerts.</div>
          ) : (
            alerts.map((a) => (
              <div
                key={a.id}
                className={`p-4 rounded-xl border flex items-start gap-4 shadow-lg ${
                  a.severity === "extreme"
                    ? "bg-red-950/60 border-red-500/50 text-red-100"
                    : "bg-orange-950/60 border-orange-500/50 text-orange-100"
                }`}
              >
                <AlertOctagon className="w-6 h-6 text-red-400 shrink-0 mt-1 animate-pulse" />
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-black uppercase tracking-wider text-red-300">
                      [{a.source.toUpperCase()}] {a.severity} — {a.region}
                    </span>
                    <span className="font-mono text-[10px] text-slate-400">
                      {new Date(a.issued_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed text-slate-200">{a.message}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
