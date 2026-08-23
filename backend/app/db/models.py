"""
ResQNet — SQLModel ORM Models
All database tables with relationships, indexes, and the VECTOR column for semantic memory.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import Column, Index, text, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, ARRAY
from sqlalchemy import Float as SAFloat
from sqlmodel import Field, SQLModel, Relationship


# ── Enumerations ──────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    field_worker = "field_worker"
    coordinator = "coordinator"
    hospital = "hospital"
    admin = "admin"

class IncidentType(str, Enum):
    flood = "flood"
    road_blocked = "road_blocked"
    shelter_needed = "shelter_needed"
    medical = "medical"
    supply_shortage = "supply_shortage"
    structural_damage = "structural_damage"
    evacuation = "evacuation"
    other = "other"

class IncidentSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class IncidentStatus(str, Enum):
    active = "active"
    investigating = "investigating"
    resolved = "resolved"
    closed = "closed"

class ResourceType(str, Enum):
    water = "water"
    food = "food"
    medicine = "medicine"
    blankets = "blankets"
    fuel = "fuel"
    medical_supplies = "medical_supplies"
    vehicles = "vehicles"
    shelter_materials = "shelter_materials"
    clothing = "clothing"
    other = "other"

class ResourceStatus(str, Enum):
    available = "available"
    requested = "requested"
    in_transit = "in_transit"
    distributed = "distributed"
    received = "received"
    depleted = "depleted"

class ResourceOperation(str, Enum):
    resource_available = "RESOURCE_AVAILABLE"
    resource_requested = "RESOURCE_REQUESTED"
    resource_distributed = "RESOURCE_DISTRIBUTED"
    resource_received = "RESOURCE_RECEIVED"

class RequestStatus(str, Enum):
    open = "open"
    acknowledged = "acknowledged"
    in_progress = "in_progress"
    fulfilled = "fulfilled"
    cancelled = "cancelled"

class RequestPriority(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class AlertSeverity(str, Enum):
    extreme = "extreme"
    severe = "severe"
    moderate = "moderate"
    minor = "minor"

class MemoryType(str, Enum):
    episodic = "episodic"
    semantic = "semantic"
    operational = "operational"
    decision = "decision"
    audit = "audit"

class SyncStatus(str, Enum):
    pending = "pending"
    syncing = "syncing"
    synced = "synced"
    failed = "failed"

class LocationType(str, Enum):
    shelter = "shelter"
    hospital = "hospital"
    supply_depot = "supply_depot"
    village = "village"
    relief_team_base = "relief_team_base"
    road = "road"
    other = "other"

class OrgType(str, Enum):
    ngo = "ngo"
    government = "government"
    hospital = "hospital"
    military = "military"
    community = "community"


# ── Organizations ─────────────────────────────────────────────────────────────

class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(index=True)
    type: OrgType = Field(index=True)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    users: List["User"] = Relationship(back_populates="organization")
    resources: List["Resource"] = Relationship(back_populates="organization")
    relief_teams: List["ReliefTeam"] = Relationship(back_populates="organization")


# ── Locations ─────────────────────────────────────────────────────────────────

class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(index=True)
    lat: float
    lng: float
    region: str = Field(index=True)
    type: LocationType = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    incidents: List["Incident"] = Relationship(back_populates="location")
    reports: List["Report"] = Relationship(back_populates="location")
    resources: List["Resource"] = Relationship(back_populates="location")
    requests: List["AidRequest"] = Relationship(back_populates="location")
    shelter: Optional["Shelter"] = Relationship(back_populates="location")
    hospital: Optional["Hospital"] = Relationship(back_populates="location")
    relief_teams: List["ReliefTeam"] = Relationship(back_populates="location")


# ── Users ─────────────────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    email: str = Field(unique=True, index=True)
    name: str
    hashed_password: str
    role: UserRole = Field(default=UserRole.field_worker, index=True)
    org_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Optional[Organization] = Relationship(back_populates="users")
    reports: List["Report"] = Relationship(back_populates="reporter")


# ── Incidents ─────────────────────────────────────────────────────────────────

class Incident(SQLModel, table=True):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("idx_incidents_severity_status", "severity", "status"),
        Index("idx_incidents_location_created", "location_id", "created_at"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    type: IncidentType = Field(index=True)
    description: str
    severity: IncidentSeverity = Field(index=True)
    status: IncidentStatus = Field(default=IncidentStatus.active, index=True)
    location_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    )
    reporter_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    location: Optional[Location] = Relationship(back_populates="incidents")
    reports: List["Report"] = Relationship(back_populates="incident")
    evidence: List["Evidence"] = Relationship(back_populates="incident")


# ── Reports ───────────────────────────────────────────────────────────────────

class Report(SQLModel, table=True):
    __tablename__ = "reports"
    __table_args__ = (
        Index("idx_reports_incident_created", "incident_id", "created_at"),
        Index("idx_reports_severity", "severity"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    # operation_id is the client-generated UUID for idempotent sync
    operation_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), unique=True, nullable=False)
    )
    incident_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)
    )
    content: str
    reporter_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    )
    location_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    )
    severity: IncidentSeverity = Field(default=IncidentSeverity.medium)
    ai_analyzed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    incident: Optional[Incident] = Relationship(back_populates="reports")
    location: Optional[Location] = Relationship(back_populates="reports")
    reporter: Optional[User] = Relationship(back_populates="reports")


# ── Resources ─────────────────────────────────────────────────────────────────

class Resource(SQLModel, table=True):
    __tablename__ = "resources"
    __table_args__ = (
        Index("idx_resources_type_status", "type", "status"),
        Index("idx_resources_location", "location_id"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    type: ResourceType = Field(index=True)
    quantity: float
    unit: str = Field(default="units")
    location_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    )
    org_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    )
    status: ResourceStatus = Field(default=ResourceStatus.available, index=True)
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    location: Optional[Location] = Relationship(back_populates="resources")
    organization: Optional[Organization] = Relationship(back_populates="resources")
    transactions: List["ResourceTransaction"] = Relationship(back_populates="resource")


class ResourceTransaction(SQLModel, table=True):
    __tablename__ = "resource_transactions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    resource_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False)
    )
    operation: ResourceOperation
    quantity: float
    from_location_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), ForeignKey("locations.id"), nullable=True)
    )
    to_location_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), ForeignKey("locations.id"), nullable=True)
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    )
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    resource: Optional[Resource] = Relationship(back_populates="transactions")


# ── Aid Requests ──────────────────────────────────────────────────────────────

class AidRequest(SQLModel, table=True):
    __tablename__ = "requests"
    __table_args__ = (
        Index("idx_requests_status_priority", "status", "priority"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    type: str = Field(index=True)
    description: str
    requester_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    )
    location_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    )
    status: RequestStatus = Field(default=RequestStatus.open, index=True)
    priority: RequestPriority = Field(default=RequestPriority.medium, index=True)
    quantity_needed: Optional[float] = None
    unit: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    location: Optional[Location] = Relationship(back_populates="requests")


# ── Shelters ──────────────────────────────────────────────────────────────────

class Shelter(SQLModel, table=True):
    __tablename__ = "shelters"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(index=True)
    location_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    )
    capacity: int
    current_occupancy: int = Field(default=0)
    status: str = Field(default="open")
    water_units: float = Field(default=0)
    food_units: float = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    location: Optional[Location] = Relationship(back_populates="shelter")


# ── Hospitals ─────────────────────────────────────────────────────────────────

class Hospital(SQLModel, table=True):
    __tablename__ = "hospitals"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(index=True)
    location_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    )
    bed_total: int
    bed_available: int
    icu_total: int = Field(default=0)
    icu_available: int = Field(default=0)
    status: str = Field(default="operational")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    location: Optional[Location] = Relationship(back_populates="hospital")


# ── Relief Teams ──────────────────────────────────────────────────────────────

class ReliefTeam(SQLModel, table=True):
    __tablename__ = "relief_teams"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(index=True)
    org_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    )
    location_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    )
    status: str = Field(default="standby")
    member_count: int = Field(default=0)
    vehicle_count: int = Field(default=0)
    specialization: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Optional[Organization] = Relationship(back_populates="relief_teams")
    location: Optional[Location] = Relationship(back_populates="relief_teams")


# ── Alerts ────────────────────────────────────────────────────────────────────

class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alerts_severity_issued", "severity", "issued_at"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    source: str = Field(index=True)           # "government", "weather", "simulated"
    type: str = Field(index=True)
    severity: AlertSeverity = Field(index=True)
    region: str = Field(index=True)
    message: str
    issued_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    expires_at: Optional[datetime] = None
    is_active: bool = Field(default=True)


# ── Memory (CockroachDB Vector Search) ───────────────────────────────────────

class Memory(SQLModel, table=True):
    """
    CockroachDB Capability #1: Distributed Vector Indexing
    The embedding column uses VECTOR type and is indexed with C-SPANN.
    """
    __tablename__ = "memories"
    __table_args__ = (
        Index("idx_memories_type_created", "memory_type", "created_at"),
        Index("idx_memories_source", "source_type", "source_id"),
        Index("idx_memories_location", "location_id"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    memory_type: MemoryType = Field(index=True)
    content: str
    # embedding stored as ARRAY(Float) — compatible with CockroachDB VECTOR type
    # The VECTOR INDEX is created separately in init_vector_index()
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(ARRAY(SAFloat), nullable=True)
    )
    source_type: Optional[str] = Field(default=None, index=True)  # "report", "incident", "decision"
    source_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), nullable=True)
    )
    location_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    )
    org_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    )
    confidence: float = Field(default=1.0)
    metadata_: Optional[dict] = Field(
        default=None,
        sa_column=Column("metadata", JSONB, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


# ── Decisions ─────────────────────────────────────────────────────────────────

class Decision(SQLModel, table=True):
    __tablename__ = "decisions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    agent_request_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False)
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    )
    user_query: str
    recommendation: str
    reasoning: str
    confidence: float = Field(default=0.5)
    tools_used: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String), nullable=True)  # text[]
    )
    memory_ids_used: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String), nullable=True)  # uuid[]
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


# ── Evidence ──────────────────────────────────────────────────────────────────

class Evidence(SQLModel, table=True):
    __tablename__ = "evidence"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    incident_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    )
    s3_key: str
    file_type: str
    original_filename: str
    uploaded_by: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    incident: Optional[Incident] = Relationship(back_populates="evidence")


# ── Sync Operations ───────────────────────────────────────────────────────────

class SyncOperation(SQLModel, table=True):
    """
    Stores all client-submitted operations for idempotent sync.
    The client generates a UUID operation_id before any network call.
    If the same operation_id is submitted twice, the server deduplicates.
    """
    __tablename__ = "sync_operations"
    __table_args__ = (
        Index("idx_sync_user_status", "user_id", "sync_status"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    # operation_id is the client-generated UUID (idempotency key)
    operation_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), unique=True, nullable=False)
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    )
    operation_type: str = Field(index=True)   # "create_report", "create_request", etc.
    payload: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    result: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    sync_status: SyncStatus = Field(default=SyncStatus.synced, index=True)
    error_message: Optional[str] = None
    client_created_at: Optional[datetime] = None
    server_created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Audit Logs ────────────────────────────────────────────────────────────────

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    entity_type: str = Field(index=True)
    entity_id: Optional[str] = Field(default=None, index=True)
    action: str = Field(index=True)          # "create", "update", "delete"
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    )
    before: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    after: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
