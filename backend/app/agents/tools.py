"""
ResQNet — AI Agent Tools
10 controlled tool functions the agent can call.
These are the ONLY ways the agent interacts with the database.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, desc
from sqlmodel import select as sm_select

from app.db.models import (
    Memory, Incident, Resource, Location, Report, AidRequest,
    ResourceTransaction, Decision, Shelter, Hospital, Alert,
    MemoryType, IncidentStatus, ResourceStatus, ResourceOperation,
    SyncStatus,
)
from app.config import settings

logger = logging.getLogger("resqnet.agent.tools")


# ── Tool definitions for the AI ───────────────────────────────────────────────
# These are passed to the LLM as function definitions

TOOL_DEFINITIONS = [
    {
        "name": "search_memories",
        "description": (
            "Search operational memory using semantic similarity. "
            "Use this to find historical events, past decisions, and prior reports "
            "that are relevant to the current query. ALWAYS call this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"},
                "limit": {"type": "integer", "description": "Max results (1-10)", "default": 5},
                "memory_type": {
                    "type": "string",
                    "enum": ["episodic", "semantic", "operational", "decision", "audit"],
                    "description": "Filter by memory type (optional)"
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_incidents",
        "description": "Retrieve recent incidents, optionally filtered by status, severity, or region.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status (active, resolved, etc.)"},
                "severity": {"type": "string", "description": "Filter by severity (critical, high, medium, low)"},
                "region": {"type": "string", "description": "Filter by region name"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "search_resources",
        "description": "Search current resource inventory. Use to find available supplies, shortages, and distributions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "description": "Type of resource (water, food, medicine, etc.)"},
                "status": {"type": "string", "description": "Resource status (available, requested, distributed)"},
                "region": {"type": "string", "description": "Region or location name to search near"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "search_locations",
        "description": "Find shelters, hospitals, villages, and supply depots by name or region.",
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string"},
                "type": {"type": "string", "description": "Location type (shelter, hospital, village, supply_depot)"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "search_previous_events",
        "description": "Search historical events of a specific type (reports, distributions, requests) for pattern matching.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Type of event: report, distribution, request"},
                "region": {"type": "string", "description": "Optional region filter"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "create_report",
        "description": "Store a new field report as operational memory. Use when the agent needs to record an observation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Report content"},
                "severity": {"type": "string", "description": "critical, high, medium, low"},
                "location_name": {"type": "string", "description": "Name of the location this report is about"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "create_resource_request",
        "description": "Create an aid request for resources at a specific location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string"},
                "quantity": {"type": "number"},
                "unit": {"type": "string"},
                "location_name": {"type": "string"},
                "priority": {"type": "string", "default": "medium"},
            },
            "required": ["resource_type", "location_name"],
        },
    },
    {
        "name": "update_resource_status",
        "description": "Update the status or quantity of a resource. Use to record distributions and receipts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_id": {"type": "string", "description": "UUID of the resource"},
                "new_status": {"type": "string"},
                "quantity_change": {"type": "number", "description": "Positive for addition, negative for deduction"},
            },
            "required": ["resource_id"],
        },
    },
    {
        "name": "create_recommendation",
        "description": "Store the agent's recommendation as decision memory. ALWAYS call this at the end of an analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendation": {"type": "string", "description": "Clear, actionable recommendation"},
                "reasoning": {"type": "string", "description": "Evidence-based reasoning"},
                "confidence": {"type": "number", "description": "Confidence score 0.0-1.0"},
                "memory_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "UUIDs of memories used as evidence",
                },
            },
            "required": ["recommendation", "reasoning", "confidence"],
        },
    },
    {
        "name": "retrieve_current_crisis_state",
        "description": "Retrieve a comprehensive snapshot of the current crisis state: active incidents, resource shortages, shelter status, hospital capacity.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

class AgentTools:
    """Executes tool calls in the agent's tool-calling loop."""

    def __init__(self, session: AsyncSession, embedding_fn):
        self.session = session
        self.embed = embedding_fn  # async function: str -> list[float]

    async def execute(self, tool_name: str, arguments: dict) -> Any:
        """Dispatch a tool call and return its result."""
        handler = getattr(self, f"_tool_{tool_name}", None)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return await handler(**arguments)
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e)}

    # ── Tool implementations ──────────────────────────────────────────────

    async def _tool_search_memories(
        self,
        query: str,
        limit: int = 5,
        memory_type: str | None = None,
    ) -> dict:
        """
        CockroachDB Capability #1: Vector similarity search using <-> operator.
        Falls back to recent memories if embedding is unavailable.
        """
        from app.memory.retrieval import search_similar_memories
        results = await search_similar_memories(
            session=self.session,
            query=query,
            embed_fn=self.embed,
            limit=limit,
            memory_type=memory_type,
        )

        # Collect incident IDs to check their live status
        incident_ids = [m.source_id for m in results if m.source_type == "incident" and m.source_id]
        incident_status_map = {}
        if incident_ids:
            inc_res = await self.session.execute(
                sm_select(Incident).where(Incident.id.in_(incident_ids))
            )
            for inc in inc_res.scalars().all():
                incident_status_map[str(inc.id)] = inc.status

        formatted_memories = []
        for m in results:
            content = m.content
            if m.source_type == "incident" and m.source_id:
                inc_status = incident_status_map.get(str(m.source_id))
                if not inc_status:
                    content = f"[DELETED INCIDENT ARCHIVE]: {content}"
                elif inc_status in ("resolved", "closed"):
                    content = f"[HISTORICAL - INCIDENT ALREADY RESOLVED]: {content}"
                else:
                    content = f"[ACTIVE INCIDENT]: {content}"
            elif m.source_type == "decision":
                content = f"[PAST DECISION LOG]: {content}"

            formatted_memories.append({
                "id": str(m.id),
                "type": m.memory_type,
                "content": content,
                "confidence": m.confidence,
                "created_at": m.created_at.isoformat(),
                "source_type": m.source_type,
                "source_id": str(m.source_id) if m.source_id else None,
            })

        return {
            "memories": formatted_memories,
            "count": len(formatted_memories),
        }

    async def _tool_search_incidents(
        self,
        status: str | None = None,
        severity: str | None = None,
        region: str | None = None,
        limit: int = 10,
    ) -> dict:
        stmt = sm_select(Incident).order_by(desc(Incident.created_at)).limit(limit)
        if status:
            stmt = stmt.where(Incident.status == status)
        if severity:
            stmt = stmt.where(Incident.severity == severity)
        result = await self.session.execute(stmt)
        incidents = result.scalars().all()
        return {
            "incidents": [
                {
                    "id": str(i.id),
                    "type": i.type,
                    "description": i.description,
                    "severity": i.severity,
                    "status": i.status,
                    "created_at": i.created_at.isoformat(),
                }
                for i in incidents
            ],
            "count": len(incidents),
        }

    async def _tool_search_resources(
        self,
        resource_type: str | None = None,
        status: str | None = None,
        region: str | None = None,
        limit: int = 10,
    ) -> dict:
        stmt = sm_select(Resource).order_by(desc(Resource.updated_at)).limit(limit)
        if resource_type:
            stmt = stmt.where(Resource.type == resource_type)
        if status:
            stmt = stmt.where(Resource.status == status)
        result = await self.session.execute(stmt)
        resources = result.scalars().all()
        return {
            "resources": [
                {
                    "id": str(r.id),
                    "type": r.type,
                    "quantity": r.quantity,
                    "unit": r.unit,
                    "status": r.status,
                    "location_id": str(r.location_id) if r.location_id else None,
                    "updated_at": r.updated_at.isoformat(),
                }
                for r in resources
            ],
            "count": len(resources),
        }

    async def _tool_search_locations(
        self,
        region: str | None = None,
        type: str | None = None,
        limit: int = 10,
    ) -> dict:
        stmt = sm_select(Location).limit(limit)
        if region:
            stmt = stmt.where(Location.region.ilike(f"%{region}%"))
        if type:
            stmt = stmt.where(Location.type == type)
        result = await self.session.execute(stmt)
        locations = result.scalars().all()
        return {
            "locations": [
                {
                    "id": str(loc.id),
                    "name": loc.name,
                    "type": loc.type,
                    "region": loc.region,
                    "lat": loc.lat,
                    "lng": loc.lng,
                }
                for loc in locations
            ],
            "count": len(locations),
        }

    async def _tool_search_previous_events(
        self,
        event_type: str,
        region: str | None = None,
        limit: int = 10,
    ) -> dict:
        if event_type == "report":
            stmt = sm_select(Report).order_by(desc(Report.created_at)).limit(limit)
            result = await self.session.execute(stmt)
            rows = result.scalars().all()
            return {
                "events": [
                    {"id": str(r.id), "content": r.content, "severity": r.severity, "created_at": r.created_at.isoformat()}
                    for r in rows
                ],
                "count": len(rows),
            }
        elif event_type == "distribution":
            stmt = sm_select(ResourceTransaction).where(
                ResourceTransaction.operation == ResourceOperation.resource_distributed
            ).order_by(desc(ResourceTransaction.created_at)).limit(limit)
            result = await self.session.execute(stmt)
            rows = result.scalars().all()
            return {
                "events": [
                    {"id": str(r.id), "quantity": r.quantity, "created_at": r.created_at.isoformat()}
                    for r in rows
                ],
                "count": len(rows),
            }
        elif event_type == "request":
            stmt = sm_select(AidRequest).order_by(desc(AidRequest.created_at)).limit(limit)
            result = await self.session.execute(stmt)
            rows = result.scalars().all()
            return {
                "events": [
                    {"id": str(r.id), "type": r.type, "status": r.status, "priority": r.priority, "created_at": r.created_at.isoformat()}
                    for r in rows
                ],
                "count": len(rows),
            }
        return {"events": [], "count": 0, "note": f"Unknown event_type: {event_type}"}

    async def _tool_create_report(
        self,
        content: str,
        severity: str = "medium",
        location_name: str | None = None,
    ) -> dict:
        report = Report(
            operation_id=uuid.uuid4(),
            content=content,
            severity=severity,
            created_at=datetime.utcnow(),
        )
        self.session.add(report)
        await self.session.flush()
        return {"report_id": str(report.id), "created": True}

    async def _tool_create_resource_request(
        self,
        resource_type: str,
        location_name: str,
        quantity: float = 0,
        unit: str = "units",
        priority: str = "medium",
    ) -> dict:
        # Find location by name
        loc_result = await self.session.execute(
            sm_select(Location).where(Location.name.ilike(f"%{location_name}%")).limit(1)
        )
        location = loc_result.scalar_one_or_none()
        req = AidRequest(
            type=resource_type,
            description=f"Agent-created request for {quantity} {unit} of {resource_type}",
            location_id=location.id if location else None,
            priority=priority,
            quantity_needed=quantity,
            unit=unit,
        )
        self.session.add(req)
        await self.session.flush()
        return {"request_id": str(req.id), "created": True}

    async def _tool_update_resource_status(
        self,
        resource_id: str,
        new_status: str | None = None,
        quantity_change: float = 0,
    ) -> dict:
        try:
            rid = uuid.UUID(resource_id)
        except ValueError:
            return {"error": "Invalid resource_id UUID"}
        result = await self.session.execute(sm_select(Resource).where(Resource.id == rid))
        resource = result.scalar_one_or_none()
        if not resource:
            return {"error": f"Resource {resource_id} not found"}
        if new_status:
            resource.status = new_status
        if quantity_change != 0:
            resource.quantity = max(0, resource.quantity + quantity_change)
        resource.updated_at = datetime.utcnow()
        self.session.add(resource)
        return {"resource_id": resource_id, "updated": True, "new_quantity": resource.quantity}

    async def _tool_create_recommendation(
        self,
        recommendation: str,
        reasoning: str,
        confidence: float,
        memory_ids: list[str] | None = None,
    ) -> dict:
        # Stored by the agent loop after tool calls complete
        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "confidence": confidence,
            "memory_ids": memory_ids or [],
            "stored": True,
        }

    async def _tool_retrieve_current_crisis_state(self) -> dict:
        # Active incidents
        inc_result = await self.session.execute(
            sm_select(Incident).where(Incident.status == IncidentStatus.active)
            .order_by(desc(Incident.created_at)).limit(20)
        )
        active_incidents = inc_result.scalars().all()

        # Critical resources
        res_result = await self.session.execute(
            sm_select(Resource).where(Resource.quantity < 100)
            .order_by(Resource.quantity).limit(10)
        )
        low_resources = res_result.scalars().all()

        # Shelters
        shelter_result = await self.session.execute(sm_select(Shelter).limit(10))
        shelters = shelter_result.scalars().all()

        # Hospitals
        hosp_result = await self.session.execute(sm_select(Hospital).limit(5))
        hospitals = hosp_result.scalars().all()

        # Open requests
        req_result = await self.session.execute(
            sm_select(AidRequest).where(AidRequest.status == "open")
            .order_by(desc(AidRequest.created_at)).limit(10)
        )
        open_requests = req_result.scalars().all()

        return {
            "active_incidents": len(active_incidents),
            "incidents": [
                {"id": str(i.id), "type": i.type, "severity": i.severity, "description": i.description[:100]}
                for i in active_incidents
            ],
            "low_resources": [
                {"id": str(r.id), "type": r.type, "quantity": r.quantity, "unit": r.unit, "status": r.status}
                for r in low_resources
            ],
            "shelters": [
                {"name": s.name, "capacity": s.capacity, "occupancy": s.current_occupancy, "water_units": s.water_units}
                for s in shelters
            ],
            "hospitals": [
                {"name": h.name, "bed_available": h.bed_available, "bed_total": h.bed_total}
                for h in hospitals
            ],
            "open_requests": len(open_requests),
        }
