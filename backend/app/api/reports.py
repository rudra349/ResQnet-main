"""ResQNet — Reports API"""
from __future__ import annotations
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import selectinload
from sqlmodel import select, desc
from app.db.engine import get_session
from app.db.models import Report, Memory, MemoryType
from app.schemas.schemas import ReportCreate, ReportOut
from app.memory.retrieval import store_memory
from app.agents.provider import provider
from app.aws.lambda_client import trigger_report_analysis

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=List[ReportOut])
async def list_reports(
    limit: int = 50,
    incident_id: Optional[uuid.UUID] = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Report).options(selectinload(Report.location)).order_by(desc(Report.created_at)).limit(limit)
    if incident_id:
        stmt = stmt.where(Report.incident_id == incident_id)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    body: ReportCreate,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_session),
):
    # Check idempotency: if operation_id exists, return stored report
    existing = await session.execute(
        select(Report).options(selectinload(Report.location)).where(Report.operation_id == body.operation_id)
    )
    existing_report = existing.scalar_one_or_none()
    if existing_report:
        return existing_report

    report = Report(
        operation_id=body.operation_id,
        incident_id=body.incident_id,
        content=body.content,
        location_id=body.location_id,
        severity=body.severity,
        created_at=body.created_at or __import__("datetime").datetime.utcnow(),
    )
    session.add(report)
    await session.flush()

    # Store as semantic memory (embedding generated in background)
    if background_tasks:
        background_tasks.add_task(
            _store_report_memory_and_trigger_lambda,
            report_id=str(report.id),
            content=report.content,
            location_id=report.location_id,
        )
    else:
        await _store_report_memory_and_trigger_lambda(
            report_id=str(report.id),
            content=report.content,
            location_id=report.location_id,
        )

    return report


async def _store_report_memory_and_trigger_lambda(
    report_id: str, content: str, location_id
):
    """Background task: store semantic memory + trigger Lambda analysis."""
    from app.db.engine import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        try:
            await store_memory(
                session=session,
                memory_type=MemoryType.semantic,
                content=content,
                embed_fn=provider().embed,
                source_type="report",
                source_id=uuid.UUID(report_id),
                location_id=location_id,
            )
            await session.commit()
        except Exception as e:
            import logging
            logging.getLogger("resqnet").error(f"Background memory store failed: {e}")

    # Trigger Lambda for deeper analysis (async, non-blocking)
    await trigger_report_analysis(report_id, content)
