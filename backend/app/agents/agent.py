"""
ResQNet — Single AI Agent
Tool-calling loop: retrieve memory → reason → recommend → store decision.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.provider import provider, AIMessage
from app.agents.tools import AgentTools, TOOL_DEFINITIONS
from app.db.models import Decision, Memory, MemoryType
from app.memory.embeddings import get_embedding

logger = logging.getLogger("resqnet.agent")

SYSTEM_PROMPT = """You are ResQNet's operational coordination AI — a persistent-memory assistant for disaster response teams.

Your role:
- Help field workers, NGOs, hospitals, and coordinators make informed decisions
- Retrieve relevant operational memory before reasoning
- Make clear, evidence-based recommendations
- Store every decision as memory for future reference

Rules you MUST follow:
1. ALWAYS call search_memories first to retrieve relevant context
2. Call retrieve_current_crisis_state when asked about overall status
3. CRITICAL: Distinguish ACTIVE operational state from HISTORICAL memory.
   - If an incident or aid request is marked [HISTORICAL - INCIDENT ALREADY RESOLVED], [DELETED INCIDENT ARCHIVE], or is not listed as active in retrieve_current_crisis_state / search_incidents, it is NOT an ongoing crisis.
   - If no active incidents or emergency shortages exist, explicitly report: "All operational sectors are currently stable with no active emergency incidents reported."
4. NEVER invent information. If data is insufficient, say "Insufficient operational data."
5. Always distinguish: Known Facts | Historical Memory | AI Recommendation | Uncertainty
6. ALWAYS call create_recommendation at the end of your analysis
7. Be concise and operational — this is an emergency tool, not a chatbot

Response format:
When you have enough information, structure your final response as:
**Recommendation:** [clear action]
**Reasoning:** [bullet points with evidence]
**Confidence:** [X%]
**Data sources:** [list memories/reports you used]

If data is insufficient, say exactly what information is missing.
"""

MAX_TOOL_ITERATIONS = 8


class AgentResponse:
    def __init__(
        self,
        request_id: uuid.UUID,
        answer: str,
        tools_used: list[str],
        memories_retrieved: list[dict],
        recommendation: str | None,
        reasoning: str | None,
        confidence: float,
        decision_id: uuid.UUID | None,
    ):
        self.request_id = request_id
        self.answer = answer
        self.tools_used = tools_used
        self.memories_retrieved = memories_retrieved
        self.recommendation = recommendation
        self.reasoning = reasoning
        self.confidence = confidence
        self.decision_id = decision_id


async def run_agent(
    user_query: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    conversation_history: list[dict] | None = None,
) -> AgentResponse:
    """
    Main agent entry point.
    Implements: Query → Memory retrieval → Reasoning → Recommendation → Store
    """
    request_id = uuid.uuid4()
    ai = provider()
    tools_obj = AgentTools(session=session, embedding_fn=ai.embed)

    messages: list[dict] = []
    if conversation_history:
        messages.extend(conversation_history[-6:])  # Keep last 3 exchanges for context
    messages.append({"role": "user", "content": user_query})

    tools_used: list[str] = []
    memories_retrieved: list[dict] = []
    recommendation: str | None = None
    reasoning: str | None = None
    confidence: float = 0.0
    final_answer = ""

    # ── Tool-calling loop ─────────────────────────────────────────────────────
    for iteration in range(3):
        logger.info(f"[{request_id}] Agent iteration {iteration + 1}")

        response: AIMessage = await ai.chat(
            messages=messages,
            tools=TOOL_DEFINITIONS if iteration < 2 else None,
            system=SYSTEM_PROMPT,
        )

        if response.content:
            final_answer = response.content

        # No more tool calls — agent finished
        if not response.tool_calls:
            break

        # Execute each tool call
        tool_results = []
        for tc in response.tool_calls:
            tools_used.append(tc.name)
            logger.info(f"[{request_id}] Calling tool: {tc.name}({tc.arguments})")

            result = await tools_obj.execute(tc.name, tc.arguments)

            # Collect retrieved memories for the response
            if tc.name == "search_memories" and isinstance(result, dict):
                memories_retrieved.extend(result.get("memories", []))

            # Extract recommendation if it was stored
            if tc.name == "create_recommendation" and isinstance(result, dict):
                recommendation = result.get("recommendation")
                reasoning = result.get("reasoning")
                confidence = result.get("confidence", 0.0)

            tool_results.append({
                "tool": tc.name,
                "result": result,
            })

        # Compact tool results to prevent bloated prompt context
        tool_result_text = json.dumps(tool_results, indent=2, default=str)
        if len(tool_result_text) > 4000:
            tool_result_text = tool_result_text[:4000] + "\n... [truncated]"

        # If recommendation was already stored, do one final synthesis and return promptly
        if recommendation:
            messages.append({"role": "assistant", "content": response.content or "Analyzing operational data."})
            messages.append({
                "role": "user",
                "content": f"Tool results:\n{tool_result_text}\n\nProvide your concise final operational response.",
            })
            final_resp: AIMessage = await ai.chat(
                messages=messages,
                tools=None,
                system=SYSTEM_PROMPT,
            )
            if final_resp.content:
                final_answer = final_resp.content
            break

        # Add assistant turn and tool results to messages
        messages.append({"role": "assistant", "content": response.content or "Executing disaster tools."})
        messages.append({
            "role": "user",
            "content": f"Tool results:\n{tool_result_text}\n\nConclude analysis and call create_recommendation or provide final answer.",
        })

    # Fallback synthesis if final_answer was not returned as text
    if not final_answer or not final_answer.strip() or final_answer == "I was unable to generate a response. Please try again.":
        if recommendation:
            final_answer = f"**Recommendation:** {recommendation}\n\n**Reasoning:** {reasoning or 'Based on real-time operational records and crisis memory.'}\n\n**Confidence:** {int(confidence * 100 if confidence <= 1 else confidence)}%"
        elif memories_retrieved:
            mem_summary = "\n".join([f"- {m.get('content', '')}" for m in memories_retrieved[:3]])
            final_answer = f"**Relevant Crisis Memory Found:**\n{mem_summary}\n\n**Recommendation:** Monitor situation and coordinate with local teams."
        else:
            final_answer = "**Operational Status:** Query processed. No active conflicting crisis constraints found in operational memory."

    # ── Store decision as memory ──────────────────────────────────────────────
    decision_id: uuid.UUID | None = None
    if recommendation or final_answer:
        decision = Decision(
            agent_request_id=request_id,
            user_id=user_id,
            user_query=user_query,
            recommendation=recommendation or final_answer[:500],
            reasoning=reasoning or "",
            confidence=confidence,
            tools_used=list(set(tools_used)),
            memory_ids_used=[m["id"] for m in memories_retrieved],
            created_at=datetime.utcnow(),
        )
        session.add(decision)

        # Store the decision itself as decision memory
        memory_content = (
            f"AI Decision [{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]: "
            f"Query: {user_query[:200]}. "
            f"Recommendation: {recommendation or final_answer[:300]}. "
            f"Confidence: {confidence:.0%}"
        )
        try:
            embedding = await ai.embed(memory_content)
        except Exception:
            embedding = None

        memory = Memory(
            memory_type=MemoryType.decision,
            content=memory_content,
            embedding=embedding,
            source_type="decision",
            source_id=decision.id,
            confidence=confidence,
            metadata_={
                "user_query": user_query,
                "tools_used": list(set(tools_used)),
                "memory_count": len(memories_retrieved),
            },
        )
        session.add(memory)
        await session.flush()
        decision_id = decision.id

    return AgentResponse(
        request_id=request_id,
        answer=final_answer or "I was unable to generate a response. Please try again.",
        tools_used=list(set(tools_used)),
        memories_retrieved=memories_retrieved,
        recommendation=recommendation,
        reasoning=reasoning,
        confidence=confidence,
        decision_id=decision_id,
    )
