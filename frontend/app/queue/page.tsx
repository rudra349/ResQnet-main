"use client";

import { useSync } from "@/hooks/useSync";
import { offlineDB } from "@/lib/offline/db";
import { Navbar } from "@/components/Navbar";
import { Database, RefreshCw, CheckCircle2, Wifi, WifiOff, Trash2 } from "lucide-react";

export default function SyncQueuePage() {
  const { pendingCount, isSyncing, isOnline, triggerSync, pendingItems } = useSync();

  const clearAllPending = async () => {
    if (!confirm("Clear all pending/stuck items from the local queue? They will NOT be sent to CockroachDB.")) return;
    const all = await offlineDB.syncQueue.toArray();
    await offlineDB.syncQueue.bulkDelete(all.map((i) => i.id!));
    // Force a page refresh to update the badge
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-[#080B10] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-4xl w-full mx-auto px-3 sm:px-6 py-6 space-y-4">
        {/* Header */}
        <div className="bg-[#0D121D] border border-[#1E293B] p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-base font-bold text-white tracking-wider uppercase flex items-center gap-2">
              <Database className="w-5 h-5 text-orange-500" />
              OFFLINE SYNC QUEUE
            </h1>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              IndexedDB local operations awaiting synchronization with CockroachDB
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={triggerSync}
              disabled={!isOnline || isSyncing || pendingCount === 0}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white font-bold text-xs transition-all cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
              <span>{isSyncing ? "Syncing..." : "Sync Now"}</span>
            </button>

            {pendingCount > 0 && (
              <button
                onClick={clearAllPending}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-950/80 hover:bg-red-900 border border-red-800 text-red-300 font-bold text-xs transition-all cursor-pointer"
                title="Discard stuck items from local queue"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear Queue</span>
              </button>
            )}
          </div>
        </div>

        {/* Network Status Banner */}
        <div className={`p-3.5 rounded-lg border flex items-center justify-between text-xs font-mono ${
          isOnline
            ? "bg-emerald-950/30 border-emerald-800 text-emerald-300"
            : "bg-amber-950/40 border-amber-800 text-amber-300"
        }`}>
          <div className="flex items-center gap-2.5">
            {isOnline ? (
              <Wifi className="w-4 h-4 text-emerald-400" />
            ) : (
              <WifiOff className="w-4 h-4 text-amber-400" />
            )}
            <div>
              <span className="font-bold block">{isOnline ? "NETWORK LINK: CONNECTED" : "OFFLINE MODE ACTIVE"}</span>
              <span className="text-[10px] opacity-80">
                {isOnline
                  ? "Click 'Sync Now' to flush pending items to CockroachDB."
                  : "All submissions enter this queue. Auto-sync fires when connectivity returns."}
              </span>
            </div>
          </div>
          <div className="font-bold text-sm ml-4 shrink-0">
            {pendingCount} Pending
          </div>
        </div>

        {/* Queue List */}
        <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-4 space-y-3">
          <h2 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400">
            Pending Queue Items ({pendingCount})
          </h2>

          {pendingCount === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 font-mono space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-500/60 mx-auto" />
              <div>Queue is clean — all local operations synchronized with CockroachDB!</div>
            </div>
          ) : (
            <div className="space-y-2.5">
              {pendingItems.map((item) => (
                <div key={item.operation_id} className="bg-[#080B10] p-3.5 rounded border border-[#1E293B] space-y-2 text-xs font-mono">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-orange-400 uppercase">{item.operation_type}</span>
                    <span className="text-[10px] text-slate-500">ID: {item.operation_id.substring(0, 8)}...</span>
                  </div>
                  <pre className="bg-[#0D121D] p-2.5 rounded border border-[#1E293B] text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap break-all">
                    {JSON.stringify(item.payload, null, 2)}
                  </pre>
                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                    <span>Created: {new Date(item.client_created_at).toLocaleTimeString()}</span>
                    <span className="text-amber-400 font-bold uppercase">● {item.sync_status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3 text-[11px] font-mono text-slate-400 space-y-1">
          <span className="font-bold text-slate-300 block">HOW THIS WORKS:</span>
          <span>When you submit a report while offline (or if the network request fails), it is saved here in browser IndexedDB storage. When you come back online, clicking &quot;Sync Now&quot; sends everything to CockroachDB with idempotency keys — so no duplicates are ever created. If items are permanently stuck, use &quot;Clear Queue&quot; to discard them.</span>
        </div>
      </main>
    </div>
  );
}
