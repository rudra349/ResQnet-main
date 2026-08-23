export type IncidentSeverity = "critical" | "high" | "medium" | "low";
export type IncidentStatus = "active" | "investigating" | "resolved" | "closed";
export type ResourceStatus = "available" | "requested" | "in_transit" | "distributed" | "received" | "depleted";

export interface Location {
  id: string;
  name: string;
  lat: number;
  lng: number;
  region: string;
  type: string;
  description?: string;
}

export interface Incident {
  id: string;
  type: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  location_id?: string;
  reporter_id?: string;
  created_at: string;
  updated_at: string;
  location?: Location;
}

export interface Report {
  id: string;
  operation_id: string;
  content: string;
  severity: IncidentSeverity;
  incident_id?: string;
  location_id?: string;
  reporter_id?: string;
  ai_analyzed: boolean;
  created_at: string;
  location?: Location;
}

export interface Resource {
  id: string;
  type: string;
  quantity: number;
  unit: string;
  status: ResourceStatus;
  location_id?: string;
  org_id?: string;
  notes?: string;
  updated_at: string;
  location?: Location;
}

export interface AidRequest {
  id: string;
  type: string;
  description: string;
  status: string;
  priority: string;
  location_id?: string;
  quantity_needed?: number;
  unit?: string;
  created_at: string;
  location?: Location;
}

export interface Alert {
  id: string;
  source: string;
  type: string;
  severity: "extreme" | "severe" | "moderate" | "minor";
  region: string;
  message: string;
  issued_at: string;
  expires_at?: string;
  is_active: boolean;
}

export interface Memory {
  id: string;
  type: string;
  content: string;
  confidence: number;
  created_at: string;
  source_type?: string;
  source_id?: string;
}

export interface AgentResponse {
  request_id: string;
  answer: string;
  tools_used: string[];
  memories_retrieved: Memory[];
  recommendation?: string;
  reasoning?: string;
  confidence: number;
  decision_id?: string;
  ai_available: boolean;
}

export interface DashboardSummary {
  active_incidents: number;
  critical_incidents: number;
  open_requests: number;
  total_shelters: number;
  people_sheltered: number;
  total_hospitals: number;
  low_resources: Array<{
    id: string;
    type: string;
    quantity: number;
    unit: string;
    status: string;
  }>;
  recent_alerts: Alert[];
  recent_incidents: Incident[];
  map_data: {
    incidents: Array<{
      id: string;
      type: string;
      severity: string;
      description: string;
      lat: number | null;
      lng: number | null;
    }>;
    shelters: Array<{
      id: string;
      name: string;
      capacity: number;
      occupancy: number;
      water_units: number;
      lat: number | null;
      lng: number | null;
    }>;
    hospitals: Array<{
      id: string;
      name: string;
      bed_available: number;
      bed_total: number;
      lat: number | null;
      lng: number | null;
    }>;
    relief_teams: Array<{
      id: string;
      name: string;
      status: string;
      lat: number | null;
      lng: number | null;
    }>;
  };
}

export interface OfflineQueueItem {
  id?: number;
  operation_id: string;
  operation_type: "create_report" | "create_request" | "update_resource";
  payload: any;
  sync_status: "pending" | "syncing" | "synced" | "failed";
  error_message?: string;
  client_created_at: string;
  retries: number;
}
