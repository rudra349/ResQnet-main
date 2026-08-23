"""ResQNet — Resources API"""
from __future__ import annotations
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, desc
from app.db.engine import get_session
from app.db.models import Resource, ResourceTransaction, Memory, MemoryType
from app.schemas.schemas import (
    ResourceCreate, ResourceOut, ResourceUpdate,
    ResourceTransactionCreate, ResourceTransactionOut,
)
from app.memory.retrieval import store_memory
from app.agents.provider import provider

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=List[ResourceOut])
async def list_resources(
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Resource).options(selectinload(Resource.location)).order_by(desc(Resource.updated_at)).limit(limit)
    if resource_type:
        stmt = stmt.where(Resource.type == resource_type)
    if status:
        stmt = stmt.where(Resource.status == status)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ResourceOut, status_code=201)
async def create_resource(body: ResourceCreate, session: AsyncSession = Depends(get_session)):
    resource = Resource(**body.model_dump())
    session.add(resource)
    await session.flush()

    # Store as operational memory
    content = f"Resource available: {resource.quantity} {resource.unit} of {resource.type}. Status: {resource.status}."
    await store_memory(
        session=session, memory_type=MemoryType.operational,
        content=content, embed_fn=provider().embed,
        source_type="resource", source_id=resource.id,
        location_id=resource.location_id,
    )
    res = await session.execute(
        select(Resource).options(selectinload(Resource.location)).where(Resource.id == resource.id)
    )
    return res.scalar_one()


@router.get("/{resource_id}", response_model=ResourceOut)
async def get_resource(resource_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Resource).options(selectinload(Resource.location)).where(Resource.id == resource_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        from fastapi import HTTPException
        raise HTTPException(404, "Resource not found")
    return r


@router.patch("/{resource_id}", response_model=ResourceOut)
async def update_resource(
    resource_id: uuid.UUID,
    body: ResourceUpdate,
    session: AsyncSession = Depends(get_session),
):
    from fastapi import HTTPException
    result = await session.execute(
        select(Resource).options(selectinload(Resource.location)).where(Resource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(404, "Resource not found")
    
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)
    resource.updated_at = datetime.utcnow()
    session.add(resource)
    await session.commit()
    await session.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=200)
async def delete_resource(
    resource_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    from fastapi import HTTPException
    from sqlalchemy import delete
    result = await session.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(404, "Resource not found")
    
    await session.execute(delete(Memory).where(Memory.source_id == resource_id))
    await session.delete(resource)
    await session.commit()
    return {"status": "deleted", "id": str(resource_id)}


@router.post("/transactions", response_model=ResourceTransactionOut, status_code=201)
async def create_transaction(
    body: ResourceTransactionCreate,
    session: AsyncSession = Depends(get_session),
):
    # Fetch resource and update quantity/status
    result = await session.execute(select(Resource).where(Resource.id == body.resource_id))
    resource = result.scalar_one_or_none()

    tx = ResourceTransaction(**body.model_dump())
    session.add(tx)

    if resource:
        if body.operation in ("RESOURCE_DISTRIBUTED", "RESOURCE_RECEIVED"):
            resource.quantity = max(0, resource.quantity - body.quantity)
        elif body.operation == "RESOURCE_AVAILABLE":
            resource.quantity += body.quantity
        resource.status = body.operation.replace("RESOURCE_", "").lower()
        resource.updated_at = datetime.utcnow()
        session.add(resource)

        # Store as episodic memory
        content = (
            f"Resource transaction: {body.operation} — {body.quantity} "
            f"{resource.unit} of {resource.type}."
        )
        await store_memory(
            session=session, memory_type=MemoryType.episodic,
            content=content, embed_fn=provider().embed,
            source_type="resource_transaction", source_id=tx.id,
        )

    await session.flush()
    return tx


@router.get("/transactions/recent", response_model=List[ResourceTransactionOut])
async def recent_transactions(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(ResourceTransaction).order_by(desc(ResourceTransaction.created_at)).limit(limit)
    )
    return result.scalars().all()
