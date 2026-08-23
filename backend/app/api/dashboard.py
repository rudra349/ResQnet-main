"""ResQNet — Dashboard API"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select as sa_select
from sqlmodel import select, desc
from app.db.engine import get_session
from app.db.models import (
    Incident, Resource, AidRequest, Shelter, Hospital,
    Alert, Location, ReliefTeam, IncidentStatus,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(session: AsyncSession = Depends(get_session)):
    # Active incidents
    active_inc = await session.execute(
        select(func.count(Incident.id)).where(Incident.status == IncidentStatus.active)
    )
    critical_inc = await session.execute(
        select(func.count(Incident.id))
        .where(Incident.status == IncidentStatus.active)
        .where(Incident.severity == "critical")
    )
    # Open requests
    open_req = await session.execute(
        select(func.count(AidRequest.id)).where(AidRequest.status == "open")
    )
    # Shelters
    shelters_result = await session.execute(select(Shelter))
    shelters = shelters_result.scalars().all()
    # Hospitals
    hospitals_result = await session.execute(select(Hospital))
    hospitals = hospitals_result.scalars().all()
    # Low resources
    low_res_result = await session.execute(
        select(Resource).where(Resource.quantity < 100).order_by(Resource.quantity).limit(8)
    )
    low_resources = low_res_result.scalars().all()
    # Recent alerts
    alerts_result = await session.execute(
        select(Alert).where(Alert.is_active == True).order_by(desc(Alert.issued_at)).limit(5)
    )
    recent_alerts = alerts_result.scalars().all()
    # Recent incidents for map
    recent_inc_result = await session.execute(
        select(Incident).where(Incident.status == IncidentStatus.active)
        .order_by(desc(Incident.created_at)).limit(50)
    )
    recent_incidents = recent_inc_result.scalars().all()
    # Locations for map
    locs_result = await session.execute(select(Location))
    all_locs = locs_result.scalars().all()
    loc_map = {str(l.id): l for l in all_locs}
    # Relief teams
    teams_result = await session.execute(select(ReliefTeam))
    teams = teams_result.scalars().all()

    def loc_to_dict(l):
        return {"id": str(l.id), "name": l.name, "lat": l.lat, "lng": l.lng, "type": l.type, "region": l.region}

    return {
        "active_incidents": active_inc.scalar() or 0,
        "critical_incidents": critical_inc.scalar() or 0,
        "open_requests": open_req.scalar() or 0,
        "total_shelters": len(shelters),
        "people_sheltered": sum(s.current_occupancy for s in shelters),
        "total_hospitals": len(hospitals),
        "low_resources": [
            {"id": str(r.id), "type": r.type, "quantity": r.quantity, "unit": r.unit, "status": r.status}
            for r in low_resources
        ],
        "recent_alerts": [
            {"id": str(a.id), "source": a.source, "type": a.type, "severity": a.severity,
             "region": a.region, "message": a.message, "issued_at": a.issued_at.isoformat()}
            for a in recent_alerts
        ],
        "recent_incidents": [
            {
                "id": str(i.id),
                "type": i.type.value if hasattr(i.type, "value") else str(i.type),
                "description": i.description,
                "severity": i.severity.value if hasattr(i.severity, "value") else str(i.severity),
                "status": i.status.value if hasattr(i.status, "value") else str(i.status),
                "location_id": str(i.location_id) if i.location_id else None,
                "created_at": i.created_at.isoformat(),
                "updated_at": i.updated_at.isoformat(),
            }
            for i in recent_incidents
        ],
        "map_data": {
            "incidents": [
                {
                    "id": str(i.id), "type": i.type, "severity": i.severity,
                    "description": i.description[:80],
                    "lat": loc_map[str(i.location_id)].lat if i.location_id and str(i.location_id) in loc_map else None,
                    "lng": loc_map[str(i.location_id)].lng if i.location_id and str(i.location_id) in loc_map else None,
                }
                for i in recent_incidents if i.location_id and str(i.location_id) in loc_map
            ],
            "shelters": [
                {
                    "id": str(s.id), "name": s.name, "capacity": s.capacity,
                    "occupancy": s.current_occupancy, "water_units": s.water_units,
                    "lat": loc_map[str(s.location_id)].lat if str(s.location_id) in loc_map else None,
                    "lng": loc_map[str(s.location_id)].lng if str(s.location_id) in loc_map else None,
                }
                for s in shelters if str(s.location_id) in loc_map
            ],
            "hospitals": [
                {
                    "id": str(h.id), "name": h.name,
                    "bed_available": h.bed_available, "bed_total": h.bed_total,
                    "lat": loc_map[str(h.location_id)].lat if str(h.location_id) in loc_map else None,
                    "lng": loc_map[str(h.location_id)].lng if str(h.location_id) in loc_map else None,
                }
                for h in hospitals if str(h.location_id) in loc_map
            ],
            "relief_teams": [
                {
                    "id": str(t.id), "name": t.name, "status": t.status,
                    "lat": loc_map[str(t.location_id)].lat if t.location_id and str(t.location_id) in loc_map else None,
                    "lng": loc_map[str(t.location_id)].lng if t.location_id and str(t.location_id) in loc_map else None,
                }
                for t in teams if t.location_id and str(t.location_id) in loc_map
            ],
        },
    }
