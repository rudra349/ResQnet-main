"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Map } from "@/components/Map";
import { api } from "@/lib/axios";
import { DashboardSummary } from "@/lib/types";
import {
  AlertOctagon,
  PlusCircle,
  Bot,
  Package,
  Users,
  Activity,
  ShieldAlert,
  CheckCircle2,
  Trash2,
  Radio,
  Flame,
  Clock,
  Compass,
  Database,
  ArrowUpRight,
  Layers,
} from "lucide-react";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFeedFilter, setSelectedFeedFilter] = useState<string>("all");

  const fetchDashboard = async () => {
    try {
      const res = await api.get("/dashboard/summary");
      setData(res.data);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolveIncident = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      // Optimistically remove from dashboard & map
      setData((prev) => {
        if (!prev) return prev;
        const target = prev.recent_incidents.find((i) => i.id === id);
        const wasCritical = target?.severity === "critical";
        return {
          ...prev,
          active_incidents: Math.max(0, prev.active_incidents - 1),
          critical_incidents: wasCritical ? Math.max(0, prev.critical_incidents - 1) : prev.critical_incidents,
          recent_incidents: prev.recent_incidents.filter((i) => i.id !== id),
          map_data: {
            ...prev.map_data,
            incidents: prev.map_data.incidents.filter((i) => i.id !== id),
          },
        };
      });
      await api.patch(`/incidents/${id}`, { status: "resolved" });
    } catch (err) {
      console.error("Error resolving incident:", err);
      fetchDashboard();
    }
  };

  const handleDeleteIncident = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Permanently delete this incident report?")) return;
    try {
      setData((prev) => {
        if (!prev) return prev;
        const target = prev.recent_incidents.find((i) => i.id === id);
        const wasCritical = target?.severity === "critical";
        return {
          ...prev,
          active_incidents: Math.max(0, prev.active_incidents - 1),
          critical_incidents: wasCritical ? Math.max(0, prev.critical_incidents - 1) : prev.critical_incidents,
          recent_incidents: prev.recent_incidents.filter((i) => i.id !== id),
          map_data: {
            ...prev.map_data,
            incidents: prev.map_data.incidents.filter((i) => i.id !== id),
          },
        };
      });
      await api.delete(`/incidents/${id}`);
    } catch (err) {
      console.error("Error deleting incident:", err);
      fetchDashboard();
    }
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#080B10] text-slate-100 flex flex-col font-sans selection:bg-orange-500 selection:text-white">
      <Navbar />

      <main className="flex-1 max-w-[1600px] w-full mx-auto px-3 sm:px-6 py-4 space-y-4">
        {/* TOP COMMAND SUB-HEADER */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#0D121D] border border-[#1E293B] p-3.5 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-orange-600/20 border border-orange-500/40 flex items-center justify-center text-orange-400 font-bold shrink-0">
              <Radio className="w-5 h-5 text-orange-500 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-white tracking-wider uppercase">
                  Live Operations Command
                </h1>
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                  LIVE TELEMETRY
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Disaster Sector: Region Alpha • CockroachDB Vector Memory Synchronized
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/report"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-orange-600 hover:bg-orange-500 text-white font-semibold text-xs transition-colors shadow-sm cursor-pointer"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Report Incident</span>
            </Link>

            <Link
              href="/ai"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#162032] hover:bg-[#1E2C44] text-cyan-400 border border-cyan-800/60 font-semibold text-xs transition-colors cursor-pointer"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>AI Dispatcher</span>
            </Link>
          </div>
        </div>

        {/* 4 CORE SITUATION METRICS */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 font-mono">
          <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span className="uppercase text-[10px] tracking-wider text-slate-400 font-bold">Active Incidents</span>
              <ShieldAlert className="w-4 h-4 text-red-500" />
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {loading ? "..." : data?.active_incidents || 0}
            </div>
            <div className="text-[10px] text-red-400 flex items-center gap-1 mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
              <span>{data?.critical_incidents || 0} CRITICAL THREATS</span>
            </div>
          </div>

          <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span className="uppercase text-[10px] tracking-wider text-slate-400 font-bold">People Sheltered</span>
              <Users className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {loading ? "..." : (data?.people_sheltered || 0).toLocaleString()}
            </div>
            <div className="text-[10px] text-blue-400 mt-1">
              {data?.total_shelters || 0} ESTABLISHED SHELTERS
            </div>
          </div>

          <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span className="uppercase text-[10px] tracking-wider text-slate-400 font-bold">Open Aid Requests</span>
              <Package className="w-4 h-4 text-orange-400" />
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {loading ? "..." : data?.open_requests || 0}
            </div>
            <div className="text-[10px] text-orange-400 mt-1">
              AWAITING DISPATCH
            </div>
          </div>

          <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span className="uppercase text-[10px] tracking-wider text-slate-400 font-bold">Hospital Readiness</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {loading ? "..." : data?.total_hospitals || 0} <span className="text-xs text-slate-500">FACILITIES</span>
            </div>
            <div className="text-[10px] text-emerald-400 mt-1">
              ALL UNITS TRIAGING
            </div>
          </div>
        </div>

        {/* ACTIVE BROADCAST ALERT BANNER */}
        {data?.recent_alerts && data.recent_alerts.length > 0 && (
          <div className="bg-red-950/30 border border-red-800/60 rounded-lg p-3 flex items-start gap-3">
            <AlertOctagon className="w-4 h-4 text-red-400 shrink-0 mt-0.5 animate-pulse" />
            <div className="flex-1 text-xs">
              <div className="font-mono text-[10px] font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
                <span>CRITICAL BROADCAST: {data.recent_alerts[0].region}</span>
                <span className="text-slate-500">•</span>
                <span className="text-slate-400">{data.recent_alerts[0].source}</span>
              </div>
              <p className="text-slate-200 mt-0.5 leading-relaxed">
                {data.recent_alerts[0].message}
              </p>
            </div>
          </div>
        )}

        {/* MAIN COMMAND GRID: TACTICAL MAP + OPERATIONS DISPATCH */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
          {/* TACTICAL MAP (Canvas) - 8 Cols */}
          <div className="xl:col-span-8 bg-[#0D121D] border border-[#1E293B] rounded-lg overflow-hidden flex flex-col">
            <div className="bg-[#111722] border-b border-[#1E293B] px-3 py-2 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-slate-300 font-bold">
                <Compass className="w-3.5 h-3.5 text-orange-400" />
                <span>GEOSPATIAL CRISIS GRID</span>
              </div>
              <div className="flex items-center gap-3 text-[10px] text-slate-400">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Incidents
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /> Shelters
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Hospitals
                </span>
              </div>
            </div>

            <div className="h-[460px] w-full relative">
              <Map data={data?.map_data} />
            </div>
          </div>

          {/* RIGHT SIDE: LIVE FEED & CRITICAL INVENTORY - 4 Cols */}
          <div className="xl:col-span-4 space-y-4">
            {/* Real-time incident logs */}
            <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3.5 flex flex-col">
              <div className="flex items-center justify-between pb-2 border-b border-[#1E293B] mb-2.5">
                <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-300">
                  <Clock className="w-3.5 h-3.5 text-orange-400" />
                  <span>INCIDENT TELEMETRY LOG</span>
                </div>
                <span className="text-[10px] font-mono text-slate-500">REALTIME</span>
              </div>

              <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
                {data?.recent_incidents && data.recent_incidents.length > 0 ? (
                  data.recent_incidents.slice(0, 8).map((inc) => (
                    <div
                      key={inc.id}
                      className="bg-[#111722] border border-[#1E293B] p-2.5 rounded text-xs space-y-1.5 hover:border-slate-600 transition-colors"
                    >
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span
                          className={`px-1.5 py-0.2 rounded font-bold uppercase ${
                            inc.severity === "critical"
                              ? "bg-red-950 text-red-400 border border-red-800"
                              : inc.severity === "high"
                              ? "bg-orange-950 text-orange-400 border border-orange-800"
                              : "bg-slate-800 text-slate-300"
                          }`}
                        >
                          {inc.severity}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-slate-500">
                            {new Date(inc.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                          <button
                            onClick={(e) => handleResolveIncident(inc.id, e)}
                            className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-950/60 border border-emerald-800/60 px-1.5 py-0.5 rounded text-[10px] font-mono flex items-center gap-1 transition-colors cursor-pointer"
                            title="Mark incident as resolved and remove from active map"
                          >
                            <CheckCircle2 className="w-2.5 h-2.5" />
                            <span>Resolve</span>
                          </button>
                          <button
                            onClick={(e) => handleDeleteIncident(inc.id, e)}
                            className="text-slate-500 hover:text-red-400 hover:bg-red-950/60 p-0.5 rounded transition-colors cursor-pointer"
                            title="Delete incident report"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <p className="text-slate-200 text-xs line-clamp-2 leading-relaxed">
                        {inc.description}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6 text-xs text-slate-500 font-mono">
                    NO ACTIVE INCIDENTS REPORTED
                  </div>
                )}
              </div>
            </div>

            {/* Critical Resource Shortages */}
            <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3.5">
              <div className="flex items-center justify-between pb-2 border-b border-[#1E293B] mb-2.5">
                <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-300">
                  <Package className="w-3.5 h-3.5 text-amber-400" />
                  <span>SUPPLY CRITICALITIES</span>
                </div>
                <span className="text-[10px] font-mono text-amber-400">LOW STOCK</span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {data?.low_resources && data.low_resources.length > 0 ? (
                  data.low_resources.slice(0, 4).map((res) => (
                    <div
                      key={res.id}
                      className="bg-[#111722] border border-[#1E293B] p-2 rounded flex flex-col justify-between"
                    >
                      <span className="text-[11px] text-slate-300 font-medium capitalize truncate">
                        {res.type}
                      </span>
                      <span className="text-xs font-mono text-orange-400 font-bold mt-1">
                        {res.quantity} <span className="text-[10px] text-slate-500 font-normal">{res.unit}</span>
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="col-span-2 text-center py-3 text-xs text-slate-500 font-mono">
                    ALL RESOURCE RESERVES SUFFICIENT
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* BOTTOM MEMORY TIMELINE ANCHOR */}
        <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300 font-semibold">COCKROACHDB PERSISTENT MEMORY TRAIL:</span>
            <span className="text-slate-400">All field reports, aid requests, & decisions committed as vectors.</span>
          </div>
          <Link
            href="/ai"
            className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold transition-colors"
          >
            <span>Query Memory Graph</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </main>
    </div>
  );
}
