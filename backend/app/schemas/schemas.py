"""ResQNet — Pydantic Schemas for all API request/response models."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    org_id: Optional[uuid.UUID] = None

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "field_worker"
    org_id: Optional[uuid.UUID] = None


# ── Locations ─────────────────────────────────────────────────────────────────

class LocationOut(BaseModel):
    id: uuid.UUID
    name: str
    lat: float
    lng: float
    region: str
    type: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ── Incidents ─────────────────────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    type: str
    description: str
    severity: str
    location_id: Optional[uuid.UUID] = None
    operation_id: Optional[uuid.UUID] = None

class IncidentOut(BaseModel):
    id: uuid.UUID
    type: str
    description: str
    severity: str
    status: str
    location_id: Optional[uuid.UUID] = None
    reporter_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    location: Optional[LocationOut] = None

    class Config:
        from_attributes = True

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None


# ── Reports ───────────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    content: str
    incident_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    severity: str = "medium"
    operation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: Optional[datetime] = None

class ReportOut(BaseModel):
    id: uuid.UUID
    operation_id: uuid.UUID
    content: str
    severity: str
    incident_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    reporter_id: Optional[uuid.UUID] = None
    ai_analyzed: bool
    created_at: datetime
    location: Optional[LocationOut] = None

    class Config:
        from_attributes = True


# ── Resources ─────────────────────────────────────────────────────────────────

class ResourceCreate(BaseModel):
    type: str
    quantity: float
    unit: str = "units"
    location_id: Optional[uuid.UUID] = None
    org_id: Optional[uuid.UUID] = None
    status: str = "available"
    notes: Optional[str] = None

class ResourceOut(BaseModel):
    id: uuid.UUID
    type: str
    quantity: float
    unit: str
    status: str
    location_id: Optional[uuid.UUID] = None
    org_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    updated_at: datetime
    location: Optional[LocationOut] = None

    class Config:
        from_attributes = True

class ResourceTransactionCreate(BaseModel):
    resource_id: uuid.UUID
    operation: str
    quantity: float
    from_location_id: Optional[uuid.UUID] = None
    to_location_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None

class ResourceTransactionOut(BaseModel):
    id: uuid.UUID
    resource_id: uuid.UUID
    operation: str
    quantity: float
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResourceUpdate(BaseModel):
    type: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    location_id: Optional[uuid.UUID] = None


# ── Requests ──────────────────────────────────────────────────────────────────

class AidRequestCreate(BaseModel):
    type: str
    description: str
    location_id: Optional[uuid.UUID] = None
    priority: str = "medium"
    quantity_needed: Optional[float] = None
    unit: Optional[str] = None

class AidRequestUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    quantity_needed: Optional[float] = None
    unit: Optional[str] = None

class AidRequestOut(BaseModel):
    id: uuid.UUID
    type: str
    description: str
    status: str
    priority: str
    location_id: Optional[uuid.UUID] = None
    quantity_needed: Optional[float] = None
    unit: Optional[str] = None
    created_at: datetime
    location: Optional[LocationOut] = None

    class Config:
        from_attributes = True


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    source: str
    type: str
    severity: str
    region: str
    message: str
    expires_at: Optional[datetime] = None

class AlertOut(BaseModel):
    id: uuid.UUID
    source: str
    type: str
    severity: str
    region: str
    message: str
    issued_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


# ── Agent ─────────────────────────────────────────────────────────────────────

class AgentChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = None

class MemoryOut(BaseModel):
    id: str
    type: str
    content: str
    confidence: float
    created_at: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None

class AgentChatResponse(BaseModel):
    request_id: str
    answer: str
    tools_used: List[str]
    memories_retrieved: List[MemoryOut]
    recommendation: Optional[str] = None
    reasoning: Optional[str] = None
    confidence: float
    decision_id: Optional[str] = None
    ai_available: bool = True


# ── Sync ──────────────────────────────────────────────────────────────────────

class SyncOperationItem(BaseModel):
    operation_id: uuid.UUID
    operation_type: str
    payload: dict
    client_created_at: Optional[datetime] = None

class SyncBatchRequest(BaseModel):
    operations: List[SyncOperationItem]

class SyncResultItem(BaseModel):
    operation_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

class SyncBatchResponse(BaseModel):
    synced: int
    failed: int
    results: List[SyncResultItem]


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceOut(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    s3_key: str
    file_type: str
    original_filename: str
    url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    active_incidents: int
    critical_incidents: int
    open_requests: int
    total_shelters: int
    people_sheltered: int
    total_hospitals: int
    low_resources: List[dict]
    recent_alerts: List[AlertOut]
    recent_incidents: List[IncidentOut]
    map_data: "MapData"

class MapData(BaseModel):
    incidents: List[dict]
    shelters: List[dict]
    hospitals: List[dict]
    relief_teams: List[dict]
    supply_depots: List[dict]


# ── Memory Search ─────────────────────────────────────────────────────────────

class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 10
    memory_type: Optional[str] = None
