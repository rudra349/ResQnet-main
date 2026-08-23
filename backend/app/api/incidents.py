"""ResQNet — Incidents API"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, desc
from app.db.engine import get_session, AsyncSessionLocal
from app.db.models import Incident, Memory, MemoryType, Location
from app.schemas.schemas import IncidentCreate, IncidentOut, IncidentUpdate
from app.memory.retrieval import store_memory
from app.agents.provider import provider

logger = logging.getLogger("resqnet.incidents")

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=List[IncidentOut])
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Incident).options(selectinload(Incident.location)).order_by(desc(Incident.created_at)).limit(limit)
    if status:
        stmt = stmt.where(Incident.status == status)
    if severity:
        stmt = stmt.where(Incident.severity == severity)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=IncidentOut, status_code=201)
async def create_incident(
    body: IncidentCreate,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_session),
):
    # If location_id is missing, auto-assign to first active location or create default
    location_id = body.location_id
    if not location_id:
        loc_res = await session.execute(select(Location).limit(1))
        existing_loc = loc_res.scalar_one_or_none()
        if existing_loc:
            location_id = existing_loc.id
        else:
            default_loc = Location(
                name="Region Alpha Command Sector",
                lat=28.6139,
                lng=77.2090,
                region="Region Alpha",
                type="village",
                description="Default crisis operational sector",
            )
            session.add(default_loc)
            await session.flush()
            location_id = default_loc.id

    incident = Incident(
        type=body.type,
        description=body.description,
        severity=body.severity,
        location_id=location_id,
    )
    session.add(incident)
    await session.flush()

    # Store episodic memory asynchronously in background (non-blocking for fast HTTP response)
    content = f"Incident [{incident.type}] reported: {incident.description}. Severity: {incident.severity}."
    if background_tasks:
        background_tasks.add_task(
            _store_incident_memory_bg,
            incident_id=str(incident.id),
            content=content,
            location_id=incident.location_id,
        )
    else:
        await _store_incident_memory_bg(
            incident_id=str(incident.id),
            content=content,
            location_id=incident.location_id,
        )

    # Pre-load location relationship to avoid MissingGreenlet lazy load error during response serialization
    res = await session.execute(
        select(Incident).options(selectinload(Incident.location)).where(Incident.id == incident.id)
    )
    return res.scalar_one()


async def _store_incident_memory_bg(incident_id: str, content: str, location_id):
    """Background task to generate Gemini vector embedding and persist episodic memory."""
    async with AsyncSessionLocal() as session:
        try:
            await store_memory(
                session=session,
                memory_type=MemoryType.episodic,
                content=content,
                embed_fn=provider().embed,
                source_type="incident",
                source_id=uuid.UUID(incident_id),
                location_id=location_id,
            )
            await session.commit()
            logger.info(f"Episodic memory stored for incident {incident_id}")
        except Exception as e:
            logger.error(f"Background incident memory store failed: {e}")


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(incident_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Incident).options(selectinload(Incident.location)).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
async def update_incident(
    incident_id: uuid.UUID,
    body: IncidentUpdate,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Incident).options(selectinload(Incident.location)).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    old_status = incident.status
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)
    incident.updated_at = datetime.utcnow()
    session.add(incident)
    await session.commit()
    await session.refresh(incident)

    # If resolved or closed, remove active distress memories and record resolution memory
    if incident.status in ("resolved", "closed") and old_status not in ("resolved", "closed"):
        from sqlalchemy import delete
        await session.execute(
            delete(Memory).where(Memory.source_id == incident.id)
        )
        await session.commit()
        content = f"RESOLUTION NOTICE: Incident [{incident.type}] has been marked RESOLVED and closed. Active emergency is now cleared."
        if background_tasks:
            background_tasks.add_task(
                _store_incident_memory_bg,
                incident_id=str(incident.id),
                content=content,
                location_id=incident.location_id,
            )

    return incident


@router.delete("/{incident_id}", status_code=200)
async def delete_incident(
    incident_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import delete
    result = await session.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Cascade delete all memories and reports associated with this incident
    await session.execute(delete(Memory).where(Memory.source_id == incident_id))
    await session.execute(delete(Report).where(Report.incident_id == incident_id))
    await session.delete(incident)
    await session.commit()
    return {"status": "deleted", "id": str(incident_id)}
