import { offlineDB } from "./db";
import { OfflineQueueItem } from "../types";
import { api } from "../axios";

/**
 * Enqueue an operation locally when offline or online.
 * Uses client-generated UUID for idempotency.
 */
export async function enqueueOperation(
  operationType: "create_report" | "create_request" | "update_resource",
  payload: any
): Promise<OfflineQueueItem> {
  const item: OfflineQueueItem = {
    operation_id: payload.operation_id || crypto.randomUUID(),
    operation_type: operationType,
    payload: {
      ...payload,
      operation_id: payload.operation_id || crypto.randomUUID(),
    },
    sync_status: "pending",
    client_created_at: new Date().toISOString(),
    retries: 0,
  };

  const id = await offlineDB.syncQueue.add(item);
  item.id = id;

  // Try immediate sync if online
  if (typeof window !== "undefined" && navigator.onLine) {
    syncOfflineQueue().catch(console.error);
  }

  return item;
}

/**
 * Synchronize all pending items in IndexedDB with the backend server.
 * Uses POST /sync endpoint.
 */
export async function syncOfflineQueue(): Promise<{ synced: number; failed: number }> {
  if (typeof window === "undefined" || !navigator.onLine) {
    return { synced: 0, failed: 0 };
  }

  const pending = await offlineDB.syncQueue
    .where("sync_status")
    .equals("pending")
    .toArray();

  if (pending.length === 0) {
    return { synced: 0, failed: 0 };
  }

  // Mark status as syncing
  await offlineDB.syncQueue
    .where("id")
    .anyOf(pending.map((p) => p.id!))
    .modify({ sync_status: "syncing" });

  try {
    const payload = {
      operations: pending.map((item) => ({
        operation_id: item.operation_id,
        operation_type: item.operation_type,
        payload: item.payload,
        client_created_at: item.client_created_at,
      })),
    };

    const res = await api.post("/sync", payload);
    const { results } = res.data;

    let syncedCount = 0;
    let failedCount = 0;

    for (const r of results) {
      const queueItem = pending.find((p) => p.operation_id === r.operation_id);
      if (!queueItem || !queueItem.id) continue;

      if (r.status === "synced" || r.status === "already_synced") {
        await offlineDB.syncQueue.update(queueItem.id, {
          sync_status: "synced",
        });
        syncedCount++;
      } else {
        await offlineDB.syncQueue.update(queueItem.id, {
          sync_status: "failed",
          error_message: r.error || "Sync failed",
          retries: queueItem.retries + 1,
        });
        failedCount++;
      }
    }

    return { synced: syncedCount, failed: failedCount };
  } catch (err: any) {
    console.error("Batch sync request failed:", err);
    // Reset syncing status back to pending for retry
    await offlineDB.syncQueue
      .where("id")
      .anyOf(pending.map((p) => p.id!))
      .modify({ sync_status: "pending" });

    return { synced: 0, failed: pending.length };
  }
}
