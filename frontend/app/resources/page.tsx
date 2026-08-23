"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/axios";
import { Resource, AidRequest } from "@/lib/types";
import { Package, PlusCircle, Clock, MapPin, AlertCircle, CheckCircle2, Trash2, Plus, RefreshCw } from "lucide-react";

export default function ResourcesPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [requests, setRequests] = useState<AidRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [requestFilter, setRequestFilter] = useState<"active" | "fulfilled" | "all">("active");

  const fetchData = async () => {
    try {
      const [resData, reqData] = await Promise.all([
        api.get("/resources"),
        api.get("/requests"),
      ]);
      setResources(resData.data);
      setRequests(reqData.data);
    } catch (err) {
      console.error("Resources fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFulfillRequest = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setRequests((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: "fulfilled" } : r))
      );
      await api.patch(`/requests/${id}`, { status: "fulfilled" });
    } catch (err) {
      console.error("Error fulfilling request:", err);
      fetchData();
    }
  };

  const handleDeleteRequest = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Permanently delete this aid request?")) return;
    try {
      setRequests((prev) => prev.filter((r) => r.id !== id));
      await api.delete(`/requests/${id}`);
    } catch (err) {
      console.error("Error deleting request:", err);
      fetchData();
    }
  };

  const handleRestockResource = async (id: string, currentQty: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const newQty = currentQty + 100;
    try {
      setResources((prev) =>
        prev.map((r) => (r.id === id ? { ...r, quantity: newQty, status: "available" } : r))
      );
      await api.patch(`/resources/${id}`, { quantity: newQty, status: "available" });
    } catch (err) {
      console.error("Error restocking resource:", err);
      fetchData();
    }
  };

  const handleDeleteResource = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Permanently delete this resource entry?")) return;
    try {
      setResources((prev) => prev.filter((r) => r.id !== id));
      await api.delete(`/resources/${id}`);
    } catch (err) {
      console.error("Error deleting resource:", err);
      fetchData();
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredRequests = requests.filter((r) => {
    if (requestFilter === "active") return r.status === "open" || r.status === "in_progress" || r.status === "acknowledged";
    if (requestFilter === "fulfilled") return r.status === "fulfilled";
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              RESOURCE INVENTORY & AID REQUESTS
            </h1>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Live tracking & replenishment for emergency logistics across CockroachDB
            </p>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg text-xs font-mono text-slate-300 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh State</span>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Current Resources */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Package className="w-4 h-4 text-orange-400" />
                <span>Current Inventory Stocks</span>
              </h2>
              <span className="text-[10px] font-mono text-slate-500">
                {resources.length} STOCKS
              </span>
            </div>

            {loading ? (
              <div className="text-xs text-slate-500 font-mono py-8 text-center">Loading inventory...</div>
            ) : resources.length === 0 ? (
              <div className="text-xs text-slate-500 font-mono py-8 text-center">No inventory stocks recorded.</div>
            ) : (
              <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
                {resources.map((res) => (
                  <div
                    key={res.id}
                    className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 flex items-center justify-between text-xs hover:border-slate-700 transition-colors"
                  >
                    <div className="space-y-0.5">
                      <div className="font-bold text-white capitalize flex items-center gap-2">
                        <span>{res.type}</span>
                        {res.quantity < 100 && (
                          <span className="bg-amber-950/80 text-amber-400 border border-amber-800/60 text-[9px] font-mono px-1 rounded uppercase">
                            Low Stock
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {res.location?.name || "Command Hub"} • Status: {res.status}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="font-mono text-base font-extrabold text-orange-400">
                          {res.quantity} <span className="text-xs text-slate-400 font-normal">{res.unit}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => handleRestockResource(res.id, res.quantity, e)}
                          className="bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 px-2 py-1 rounded text-[10px] font-mono flex items-center gap-1 cursor-pointer transition-colors"
                          title="Add 100 units to stock"
                        >
                          <Plus className="w-2.5 h-2.5" />
                          <span>+100</span>
                        </button>
                        <button
                          onClick={(e) => handleDeleteResource(res.id, e)}
                          className="text-slate-500 hover:text-red-400 hover:bg-red-950/60 p-1 rounded transition-colors cursor-pointer"
                          title="Delete resource"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Aid Requests */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span>Aid Requests Log</span>
              </h2>
              <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded p-0.5 text-[10px] font-mono">
                <button
                  onClick={() => setRequestFilter("active")}
                  className={`px-2 py-0.5 rounded cursor-pointer ${
                    requestFilter === "active" ? "bg-slate-800 text-white font-bold" : "text-slate-400"
                  }`}
                >
                  Active
                </button>
                <button
                  onClick={() => setRequestFilter("fulfilled")}
                  className={`px-2 py-0.5 rounded cursor-pointer ${
                    requestFilter === "fulfilled" ? "bg-slate-800 text-white font-bold" : "text-slate-400"
                  }`}
                >
                  Fulfilled
                </button>
                <button
                  onClick={() => setRequestFilter("all")}
                  className={`px-2 py-0.5 rounded cursor-pointer ${
                    requestFilter === "all" ? "bg-slate-800 text-white font-bold" : "text-slate-400"
                  }`}
                >
                  All
                </button>
              </div>
            </div>

            {loading ? (
              <div className="text-xs text-slate-500 font-mono py-8 text-center">Loading requests...</div>
            ) : filteredRequests.length === 0 ? (
              <div className="text-xs text-slate-500 font-mono py-8 text-center">
                {requestFilter === "active" ? "No active aid requests pending." : "No aid requests found in this filter."}
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
                {filteredRequests.map((req) => (
                  <div
                    key={req.id}
                    className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs space-y-2 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-[10px]">
                        <span
                          className={`uppercase font-bold px-2 py-0.5 rounded ${
                            req.priority === "critical"
                              ? "bg-red-950 text-red-400 border border-red-800"
                              : req.priority === "high"
                              ? "bg-orange-950 text-orange-400 border border-orange-800"
                              : "bg-slate-800 text-slate-300"
                          }`}
                        >
                          {req.priority}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 rounded ${
                            req.status === "fulfilled"
                              ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                              : "text-slate-400"
                          }`}
                        >
                          {req.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {req.status !== "fulfilled" && (
                          <button
                            onClick={(e) => handleFulfillRequest(req.id, e)}
                            className="bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 px-2 py-0.5 rounded text-[10px] font-mono flex items-center gap-1 cursor-pointer transition-colors"
                            title="Mark request as fulfilled"
                          >
                            <CheckCircle2 className="w-2.5 h-2.5" />
                            <span>Fulfill</span>
                          </button>
                        )}
                        <button
                          onClick={(e) => handleDeleteRequest(req.id, e)}
                          className="text-slate-500 hover:text-red-400 hover:bg-red-950/60 p-1 rounded transition-colors cursor-pointer"
                          title="Delete request"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                    <p className="text-slate-200 text-xs leading-relaxed">{req.description}</p>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-900">
                      <span>{req.location?.name || "Region Alpha"}</span>
                      {req.quantity_needed && (
                        <span className="text-orange-400 font-bold">
                          Needed: {req.quantity_needed} {req.unit}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
