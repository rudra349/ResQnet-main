"""ResQNet — Agent API (Chat + Report Analysis)"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.engine import get_session
from app.agents.agent import run_agent
from app.schemas.schemas import AgentChatRequest, AgentChatResponse, MemoryOut

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    body: AgentChatRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Main AI agent endpoint.
    The agent retrieves persistent memory, reasons, recommends, and stores the decision.
    """
    try:
        response = await run_agent(
            user_query=body.message,
            session=session,
            user_id=None,
            conversation_history=body.conversation_history,
        )
        return AgentChatResponse(
            request_id=str(response.request_id),
            answer=response.answer,
            tools_used=response.tools_used,
            memories_retrieved=[
                MemoryOut(
                    id=m.get("id", ""),
                    type=m.get("type", ""),
                    content=m.get("content", ""),
                    confidence=m.get("confidence", 0.0),
                    created_at=m.get("created_at", ""),
                    source_type=m.get("source_type"),
                    source_id=m.get("source_id"),
                )
                for m in response.memories_retrieved
            ],
            recommendation=response.recommendation,
            reasoning=response.reasoning,
            confidence=response.confidence,
            decision_id=str(response.decision_id) if response.decision_id else None,
            ai_available=True,
        )
    except Exception as e:
        import logging
        logging.getLogger("resqnet").error(f"Agent error: {e}")
        return AgentChatResponse(
            request_id=str(uuid.uuid4()),
            answer=f"Report stored. AI analysis unavailable: {str(e)[:200]}",
            tools_used=[],
            memories_retrieved=[],
            confidence=0.0,
            ai_available=False,
        )


@router.post("/analyze-report")
async def analyze_report(
    report_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Trigger AI analysis of a specific report."""
    from sqlalchemy import select
    from app.db.models import Report
    result = await session.execute(select(Report).where(Report.id == uuid.UUID(report_id)))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")

    response = await run_agent(
        user_query=f"Analyze this field report and provide operational recommendations: {report.content}",
        session=session,
    )
    return {
        "report_id": report_id,
        "analysis": response.answer,
        "recommendation": response.recommendation,
        "confidence": response.confidence,
        "memories_used": len(response.memories_retrieved),
    }
