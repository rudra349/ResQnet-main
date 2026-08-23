"""ResQNet — Alerts API"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from app.db.engine import get_session
from app.db.models import Alert, Memory, MemoryType
from app.schemas.schemas import AlertCreate, AlertOut
from app.memory.retrieval import store_memory
from app.agents.provider import provider

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertOut])
async def list_alerts(
    active_only: bool = True,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Alert).order_by(desc(Alert.issued_at)).limit(limit)
    if active_only:
        stmt = stmt.where(Alert.is_active == True)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=AlertOut, status_code=201)
async def create_alert(body: AlertCreate, session: AsyncSession = Depends(get_session)):
    alert = Alert(**body.model_dump())
    session.add(alert)
    await session.flush()

    # Store as operational memory so AI can use alerts as context
    content = (
        f"Government Alert [{alert.severity.upper()}] — {alert.type}: "
        f"{alert.message} Region: {alert.region}."
    )
    await store_memory(
        session=session, memory_type=MemoryType.operational,
        content=content, embed_fn=provider().embed,
        source_type="alert", source_id=alert.id,
    )
    return alert


@router.delete("/{alert_id}")
async def deactivate_alert(alert_id: str, session: AsyncSession = Depends(get_session)):
    import uuid
    result = await session.execute(select(Alert).where(Alert.id == uuid.UUID(alert_id)))
    alert = result.scalar_one_or_none()
    if alert:
        alert.is_active = False
        session.add(alert)
    return {"status": "deactivated"}
