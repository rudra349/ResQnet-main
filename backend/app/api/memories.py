"""ResQNet — Memory Search API"""
from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.engine import get_session
from app.memory.retrieval import search_similar_memories
from app.agents.provider import provider
from app.schemas.schemas import MemorySearchRequest, MemoryOut

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("/search", response_model=List[MemoryOut])
async def search_memories(
    body: MemorySearchRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Semantic similarity search over operational memory.
    Uses CockroachDB vector search (<-> operator).
    """
    memories = await search_similar_memories(
        session=session,
        query=body.query,
        embed_fn=provider().embed,
        limit=body.limit,
        memory_type=body.memory_type,
    )
    return [
        MemoryOut(
            id=str(m.id),
            type=m.memory_type,
            content=m.content,
            confidence=m.confidence,
            created_at=m.created_at.isoformat(),
            source_type=m.source_type,
            source_id=str(m.source_id) if m.source_id else None,
        )
        for m in memories
    ]
