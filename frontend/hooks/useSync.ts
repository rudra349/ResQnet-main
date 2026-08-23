import { useLiveQuery } from "dexie-react-hooks";
import { offlineDB } from "../lib/offline/db";
import { syncOfflineQueue } from "../lib/offline/queue";
import { useState, useEffect } from "react";
import { useOnline } from "./useOnline";

export function useSync() {
  const isOnline = useOnline();
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<{ synced: number; failed: number } | null>(null);

  const pendingItems = useLiveQuery(
    () => offlineDB.syncQueue.where("sync_status").equals("pending").toArray(),
    []
  );

  const pendingCount = pendingItems ? pendingItems.length : 0;

  // Automatically trigger sync when coming online if there are pending items
  useEffect(() => {
    if (isOnline && pendingCount > 0 && !isSyncing) {
      triggerSync();
    }
  }, [isOnline, pendingCount]);

  const triggerSync = async () => {
    if (isSyncing || !isOnline) return;
    setIsSyncing(true);
    try {
      const res = await syncOfflineQueue();
      setLastSyncResult(res);
    } catch (err) {
      console.error("Manual sync failed:", err);
    } finally {
      setIsSyncing(false);
    }
  };

  return {
    pendingCount,
    isSyncing,
    isOnline,
    triggerSync,
    lastSyncResult,
    pendingItems: pendingItems || [],
  };
}
