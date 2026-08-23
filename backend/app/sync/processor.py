"""
ResQNet — Idempotent Sync Service
Handles offline operations submitted by clients.
Uses operation_id (client-generated UUID) to prevent duplicate processing.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.models import (
    SyncOperation, SyncStatus, Report, AidRequest,
    IncidentSeverity, RequestPriority,
)

logger = logging.getLogger("resqnet.sync")


async def process_sync_operation(
    session: AsyncSession,
    operation_id: uuid.UUID,
    operation_type: str,
    payload: dict,
    user_id: uuid.UUID | None = None,
    client_created_at: datetime | None = None,
) -> dict:
    """
    Idempotent sync handler.
    If operation_id already exists in sync_operations → return stored result.
    Otherwise → execute the operation and store result.
    """
    # ── Idempotency check ────────────────────────────────────────────────────
    existing = await session.execute(
        select(SyncOperation).where(SyncOperation.operation_id == operation_id)
    )
    existing_op = existing.scalar_one_or_none()

    if existing_op:
        logger.info(f"Duplicate sync operation {operation_id} — returning stored result")
        return {
            "operation_id": str(operation_id),
            "status": "already_synced",
            "result": existing_op.result,
        }

    # ── Execute the operation ─────────────────────────────────────────────────
    result = None
    error = None

    try:
        if operation_type == "create_report":
            result = await _create_report(session, payload, user_id)
        elif operation_type == "create_request":
            result = await _create_request(session, payload, user_id)
        elif operation_type == "update_resource":
            result = await _update_resource(session, payload, user_id)
        else:
            error = f"Unknown operation_type: {operation_type}"

    except Exception as e:
        error = str(e)
        logger.error(f"Sync operation {operation_id} failed: {e}")

    # ── Record in sync_operations ─────────────────────────────────────────────
    sync_op = SyncOperation(
        operation_id=operation_id,
        user_id=user_id,
        operation_type=operation_type,
        payload=payload,
        result=result,
        sync_status=SyncStatus.synced if not error else SyncStatus.failed,
        error_message=error,
        client_created_at=client_created_at,
        server_created_at=datetime.utcnow(),
    )
    session.add(sync_op)
    await session.flush()

    if error:
        return {"operation_id": str(operation_id), "status": "failed", "error": error}

    return {
        "operation_id": str(operation_id),
        "status": "synced",
        "result": result,
    }


async def _create_report(session: AsyncSession, payload: dict, user_id) -> dict:
    report = Report(
        operation_id=uuid.UUID(payload.get("operation_id", str(uuid.uuid4()))),
        incident_id=uuid.UUID(payload["incident_id"]) if payload.get("incident_id") else None,
        content=payload["content"],
        reporter_id=user_id,
        location_id=uuid.UUID(payload["location_id"]) if payload.get("location_id") else None,
        severity=payload.get("severity", IncidentSeverity.medium),
        created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.utcnow(),
    )
    session.add(report)
    await session.flush()
    return {"report_id": str(report.id)}


async def _create_request(session: AsyncSession, payload: dict, user_id) -> dict:
    req = AidRequest(
        type=payload.get("type", "general"),
        description=payload.get("description", ""),
        requester_id=user_id,
        location_id=uuid.UUID(payload["location_id"]) if payload.get("location_id") else None,
        priority=payload.get("priority", RequestPriority.medium),
        quantity_needed=payload.get("quantity_needed"),
        unit=payload.get("unit"),
    )
    session.add(req)
    await session.flush()
    return {"request_id": str(req.id)}


async def _update_resource(session: AsyncSession, payload: dict, user_id) -> dict:
    from app.db.models import Resource
    rid = uuid.UUID(payload["resource_id"])
    result = await session.execute(select(Resource).where(Resource.id == rid))
    resource = result.scalar_one_or_none()
    if not resource:
        raise ValueError(f"Resource {rid} not found")
    if payload.get("status"):
        resource.status = payload["status"]
    if payload.get("quantity") is not None:
        resource.quantity = payload["quantity"]
    resource.updated_at = datetime.utcnow()
    session.add(resource)
    return {"resource_id": str(rid)}
