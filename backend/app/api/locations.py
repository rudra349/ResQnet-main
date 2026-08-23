"""ResQNet — Locations API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from app.db.engine import get_session
from app.db.models import Location
from app.schemas.schemas import LocationOut

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=List[LocationOut])
async def list_locations(
    region: Optional[str] = None,
    type: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Location)
    if region:
        stmt = stmt.where(Location.region.ilike(f"%{region}%"))
    if type:
        stmt = stmt.where(Location.type == type)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=LocationOut, status_code=201)
async def create_location(body: dict, session: AsyncSession = Depends(get_session)):
    loc = Location(**body)
    session.add(loc)
    await session.flush()
    return loc
