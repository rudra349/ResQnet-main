"use client";

import { useSync } from "@/hooks/useSync";
import { Wifi, WifiOff, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react";

export function SyncBadge() {
  const { pendingCount, isSyncing, isOnline, triggerSync, lastSyncResult } = useSync();

  return (
    <div className="flex items-center gap-2 text-xs font-mono">
      {/* Online / Offline Status */}
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border transition-all ${
          isOnline
            ? "bg-emerald-950/60 border-emerald-500/30 text-emerald-400"
            : "bg-amber-950/80 border-amber-500/40 text-amber-300 animate-pulse"
        }`}
      >
        {isOnline ? (
          <>
            <Wifi className="w-3.5 h-3.5 text-emerald-400" />
            <span>ONLINE</span>
          </>
        ) : (
          <>
            <WifiOff className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-bold">OFFLINE MODE</span>
          </>
        )}
      </div>

      {/* Sync Queue Status */}
      {pendingCount > 0 ? (
        <button
          onClick={triggerSync}
          disabled={!isOnline || isSyncing}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full border font-semibold transition-all ${
            isSyncing
              ? "bg-blue-950/80 border-blue-500/50 text-blue-300"
              : isOnline
              ? "bg-orange-950/80 border-orange-500/50 text-orange-300 hover:bg-orange-900/80 cursor-pointer"
              : "bg-slate-900 border-slate-700 text-slate-400"
          }`}
          title={isOnline ? "Click to synchronize pending items now" : "Connect to network to sync"}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin text-blue-400" : ""}`} />
          <span>
            {isSyncing ? "Syncing..." : `${pendingCount} pending sync`}
          </span>
        </button>
      ) : (
        lastSyncResult && (
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-slate-400">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
            <span>Synced</span>
          </div>
        )
      )}
    </div>
  );
}
