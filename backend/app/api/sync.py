"""ResQNet — Sync API (batch idempotent sync)"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.engine import get_session
from app.schemas.schemas import SyncBatchRequest, SyncBatchResponse, SyncResultItem
from app.sync.processor import process_sync_operation

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncBatchResponse)
async def sync_operations(
    body: SyncBatchRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Process a batch of offline operations from the client.
    Each operation has a client-generated UUID for idempotency.
    """
    results = []
    synced = 0
    failed = 0

    for op in body.operations:
        result = await process_sync_operation(
            session=session,
            operation_id=op.operation_id,
            operation_type=op.operation_type,
            payload=op.payload,
            client_created_at=op.client_created_at,
        )
        results.append(SyncResultItem(
            operation_id=str(op.operation_id),
            status=result["status"],
            result=result.get("result"),
            error=result.get("error"),
        ))
        if result["status"] in ("synced", "already_synced"):
            synced += 1
        else:
            failed += 1

    return SyncBatchResponse(synced=synced, failed=failed, results=results)


@router.get("/status")
async def sync_status(session: AsyncSession = Depends(get_session)):
    """Return overall sync statistics."""
    from sqlalchemy import func, select
    from app.db.models import SyncOperation, SyncStatus
    total = await session.execute(select(func.count(SyncOperation.id)))
    synced = await session.execute(
        select(func.count(SyncOperation.id)).where(SyncOperation.sync_status == SyncStatus.synced)
    )
    failed = await session.execute(
        select(func.count(SyncOperation.id)).where(SyncOperation.sync_status == SyncStatus.failed)
    )
    return {
        "total": total.scalar(),
        "synced": synced.scalar(),
        "failed": failed.scalar(),
    }
