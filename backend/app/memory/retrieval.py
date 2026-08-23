"""
ResQNet — Memory: Vector Similarity Retrieval
Uses CockroachDB's <-> cosine distance operator for semantic search.
Falls back to recent memories if vector search is unavailable.
"""
from __future__ import annotations

import logging
from typing import Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, desc
from sqlmodel import select as sm_select

from app.db.models import Memory, MemoryType

logger = logging.getLogger("resqnet.memory.retrieval")


async def search_similar_memories(
    session: AsyncSession,
    query: str,
    embed_fn: Callable[[str], Awaitable[list[float]]],
    limit: int = 5,
    memory_type: str | None = None,
) -> list[Memory]:
    """
    Search memories by vector similarity using CockroachDB's <-> operator.
    CockroachDB Capability #1: Distributed Vector Indexing.

    Falls back to most-recent memories if embedding fails.
    """
    # Generate query embedding
    try:
        query_embedding = await embed_fn(query)
    except Exception as e:
        logger.warning(f"Embedding failed, falling back to recency sort: {e}")
        query_embedding = None

    if query_embedding:
        try:
            # CockroachDB vector similarity search using <-> (L2 distance)
            # The VECTOR INDEX (C-SPANN) accelerates this query
            embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
            type_filter = f"AND memory_type = '{memory_type}'" if memory_type else ""
            sql = text(f"""
                SELECT id FROM memories
                WHERE embedding IS NOT NULL
                {type_filter}
                ORDER BY embedding <-> '{embedding_str}'::VECTOR
                LIMIT :limit
            """)
            result = await session.execute(sql, {"limit": limit})
            memory_ids = [row[0] for row in result.fetchall()]

            if memory_ids:
                mem_result = await session.execute(
                    sm_select(Memory).where(Memory.id.in_(memory_ids))
                )
                memories = mem_result.scalars().all()
                # Preserve similarity order
                id_order = {mid: i for i, mid in enumerate(memory_ids)}
                return sorted(memories, key=lambda m: id_order.get(m.id, 999))
        except Exception as e:
            logger.warning(f"Vector search failed, falling back to recency: {e}")
            await session.rollback()

    # Fallback: most recent memories
    stmt = sm_select(Memory).order_by(desc(Memory.created_at)).limit(limit)
    if memory_type:
        stmt = stmt.where(Memory.memory_type == memory_type)
    result = await session.execute(stmt)
    return result.scalars().all()


async def store_memory(
    session: AsyncSession,
    memory_type: str,
    content: str,
    embed_fn: Callable[[str], Awaitable[list[float]]],
    source_type: str | None = None,
    source_id=None,
    location_id=None,
    confidence: float = 1.0,
    metadata: dict | None = None,
) -> Memory:
    """Store a new memory with embedding."""
    try:
        embedding = await embed_fn(content)
    except Exception:
        embedding = None

    memory = Memory(
        memory_type=memory_type,
        content=content,
        embedding=embedding,
        source_type=source_type,
        source_id=source_id,
        location_id=location_id,
        confidence=confidence,
        metadata_=metadata,
    )
    session.add(memory)
    await session.flush()
    return memory
