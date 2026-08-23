"""ResQNet — Memory: Embeddings"""
from __future__ import annotations

import logging
from app.agents.provider import provider

logger = logging.getLogger("resqnet.memory")


async def get_embedding(text: str) -> list[float] | None:
    """Generate embedding for a text string using the configured provider."""
    try:
        ai = provider()
        return await ai.embed(text[:8000])
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None
