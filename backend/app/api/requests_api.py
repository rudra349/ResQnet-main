from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from sqlmodel import select, desc
from typing import List, Optional
import uuid
from app.db.engine import get_session
from app.db.models import AidRequest, Location, Memory
from app.schemas.schemas import AidRequestCreate, AidRequestOut, AidRequestUpdate, LocationOut

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=List[AidRequestOut])
async def list_requests(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AidRequest).options(selectinload(AidRequest.location)).order_by(desc(AidRequest.created_at)).limit(limit)
    if status:
        stmt = stmt.where(AidRequest.status == status)
    if priority:
        stmt = stmt.where(AidRequest.priority == priority)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=AidRequestOut, status_code=201)
async def create_request(body: AidRequestCreate, session: AsyncSession = Depends(get_session)):
    req = AidRequest(**body.model_dump())
    session.add(req)
    await session.flush()
    res = await session.execute(
        select(AidRequest).options(selectinload(AidRequest.location)).where(AidRequest.id == req.id)
    )
    return res.scalar_one()


@router.patch("/{request_id}", response_model=AidRequestOut)
async def update_request(
    request_id: uuid.UUID,
    body: AidRequestUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(AidRequest).options(selectinload(AidRequest.location)).where(AidRequest.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Aid request not found")
    
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(req, field, value)
    req.updated_at = datetime.utcnow()
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req


@router.delete("/{request_id}", status_code=200)
async def delete_request(
    request_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(AidRequest).where(AidRequest.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Aid request not found")
    
    # Delete associated memories
    await session.execute(delete(Memory).where(Memory.source_id == request_id))
    await session.delete(req)
    await session.commit()
    return {"status": "deleted", "id": str(request_id)}
