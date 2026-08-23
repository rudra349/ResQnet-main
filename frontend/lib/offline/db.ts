import Dexie, { Table } from "dexie";
import { OfflineQueueItem, Report, Incident, Resource, Alert } from "../types";

export class ResQNetDB extends Dexie {
  syncQueue!: Table<OfflineQueueItem>;
  cachedReports!: Table<Report>;
  cachedIncidents!: Table<Incident>;
  cachedResources!: Table<Resource>;
  cachedAlerts!: Table<Alert>;

  constructor() {
    super("ResQNetOfflineDB");
    this.version(1).stores({
      syncQueue: "++id, operation_id, sync_status, operation_type, client_created_at",
      cachedReports: "id, operation_id, created_at, severity",
      cachedIncidents: "id, created_at, status, severity",
      cachedResources: "id, type, status",
      cachedAlerts: "id, issued_at, is_active",
    });
  }
}

export const offlineDB = new ResQNetDB();
