"""
ResQNet — AI Provider Abstraction
Supports Amazon Bedrock (Claude Haiku) and Google Gemini.
Switch between them via AI_PROVIDER env var.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger("resqnet.ai")


# ── Data classes ──────────────────────────────────────────────────────────────

class ToolCall:
    def __init__(self, name: str, arguments: dict):
        self.name = name
        self.arguments = arguments


class AIMessage:
    def __init__(
        self,
        content: str,
        tool_calls: list[ToolCall] | None = None,
        finish_reason: str = "stop",
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.finish_reason = finish_reason


# ── Abstract base ─────────────────────────────────────────────────────────────

class AIProvider(ABC):
    """Protocol-like ABC for AI providers. Add new providers by subclassing."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> AIMessage:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate a text embedding vector."""
        ...

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Dimension of the embedding vectors."""
        ...


# ── Bedrock Provider ──────────────────────────────────────────────────────────

class BedrockProvider(AIProvider):
    """Amazon Bedrock with Claude and Titan Embeddings."""

    def __init__(self):
        import boto3
        self._bedrock = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        self._chat_model = settings.bedrock_chat_model
        self._embed_model = settings.bedrock_embed_model

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> AIMessage:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_chat, messages, tools, system)

    def _sync_chat(self, messages, tools, system) -> AIMessage:
        body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            body["system"] = system
        if tools:
            body["tools"] = tools

        response = self._bedrock.invoke_model(
            modelId=self._chat_model,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        content_blocks = result.get("content", [])
        text = ""
        tool_calls = []
        for block in content_blocks:
            if block.get("type") == "text":
                text += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    name=block["name"],
                    arguments=block.get("input", {}),
                ))
        return AIMessage(
            content=text,
            tool_calls=tool_calls,
            finish_reason=result.get("stop_reason", "stop"),
        )

    async def embed(self, text: str) -> list[float]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_embed, text)

    def _sync_embed(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text[:8192]})
        response = self._bedrock.invoke_model(
            modelId=self._embed_model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    @property
    def embedding_dim(self) -> int:
        return 1536  # Titan Embed v2


# ── Gemini Provider ───────────────────────────────────────────────────────────

# ── Gemini Provider ───────────────────────────────────────────────────────────

class GeminiProvider(AIProvider):
    """Google Gemini (chat + embeddings) using google-genai SDK."""

    def __init__(self):
        from google import genai
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model_name = getattr(settings, "gemini_model", None) or settings.gemini_chat_model
        self._embed_model_name = getattr(settings, "gemini_embed_model", "gemini-embedding-001")

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> AIMessage:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_chat, messages, tools, system)

    def _convert_tool(self, tool_dict: dict):
        from google.genai import types
        name = tool_dict["name"]
        description = tool_dict.get("description", "")
        schema = tool_dict.get("input_schema", tool_dict.get("parameters", {}))
        
        properties = {}
        for k, v in schema.get("properties", {}).items():
            prop_copy = dict(v)
            if "type" in prop_copy:
                prop_copy["type"] = prop_copy["type"].upper()
            if "items" in prop_copy and isinstance(prop_copy["items"], dict) and "type" in prop_copy["items"]:
                prop_copy["items"] = dict(prop_copy["items"])
                prop_copy["items"]["type"] = prop_copy["items"]["type"].upper()
            properties[k] = prop_copy
            
        param_schema = {
            "type": "OBJECT",
            "properties": properties,
            "required": schema.get("required", []),
        }
        return types.FunctionDeclaration(
            name=name,
            description=description,
            parameters=param_schema,
        )

    def _sync_chat(self, messages, tools, system) -> AIMessage:
        from google.genai import types
        import time

        # Build tools if provided
        tool_objs = None
        if tools:
            declarations = [self._convert_tool(t) for t in tools]
            tool_objs = [types.Tool(function_declarations=declarations)]

        # Build contents from messages
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content_str = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            if not content_str or not content_str.strip():
                content_str = "Processing disaster response tool results."
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content_str)]
                )
            )

        config = types.GenerateContentConfig(
            system_instruction=system if system else None,
            tools=tool_objs,
            temperature=0.2,
        )

        candidate_models = list(dict.fromkeys([
            self._model_name or "gemini-3.6-flash",
            "gemini-3.6-flash",
            "gemini-3.1-flash-lite",
        ]))

        response = None
        last_err = None
        for model in candidate_models:
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                if response:
                    break
            except Exception as e:
                err_str = str(e)
                last_err = e
                # If rate limited (429) or model not found (404), immediately try next model without waiting
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "NOT_FOUND" in err_str or "404" in err_str:
                    continue
                # For transient 503, brief pause before trying next
                time.sleep(0.5)

        if response is None:
            # If all live models hit rate limits, return a graceful fallback response
            return AIMessage(
                content=f"Operational intelligence query processed. Real-time Gemini models temporarily reached rate limits ({str(last_err)[:100]}). Please retry in a few moments.",
                tool_calls=[],
                finish_reason="stop",
            )

        text_content = ""
        tool_calls = []

        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text:
                        text_content += part.text
                    if part.function_call:
                        fc = part.function_call
                        args = dict(fc.args) if fc.args else {}
                        tool_calls.append(ToolCall(name=fc.name, arguments=args))

        return AIMessage(
            content=text_content,
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
        )

    async def embed(self, text: str) -> list[float]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_embed, text)

    def _sync_embed(self, text: str) -> list[float]:
        try:
            embed_model = getattr(settings, "gemini_embed_model", "gemini-embedding-001")
            result = self._client.models.embed_content(
                model=embed_model,
                contents=text[:8000],
            )
            if result.embeddings:
                vals = list(result.embeddings[0].values)
                target_dim = settings.embedding_dim
                if len(vals) > target_dim:
                    vals = vals[:target_dim]
                elif len(vals) < target_dim:
                    vals = vals + [0.0] * (target_dim - len(vals))
                return vals
            return MockProvider()._sync_embed_fallback(text)
        except Exception as e:
            logger.warning(f"Gemini embed API call failed ({e}) — falling back to deterministic mock embedding")
            return MockProvider()._sync_embed_fallback(text)

    @property
    def embedding_dim(self) -> int:
        return 768  # text-embedding-004


# ── Mock Provider (tests / no credentials) ────────────────────────────────────

class MockProvider(AIProvider):
    """Deterministic mock for testing and CI without credentials."""

    async def chat(self, messages, tools=None, system=None) -> AIMessage:
        return AIMessage(
            content=(
                "**Insufficient operational data.**\n\n"
                "This is a mock AI response for testing. "
                "Configure AI_PROVIDER=bedrock or AI_PROVIDER=gemini with valid credentials "
                "to enable real AI responses."
            ),
            tool_calls=[],
            finish_reason="stop",
        )

    async def embed(self, text: str) -> list[float]:
        return self._sync_embed_fallback(text)

    def _sync_embed_fallback(self, text: str) -> list[float]:
        import hashlib
        # Deterministic pseudo-embedding from text hash for testing
        h = hashlib.sha256(text.encode()).digest()
        dim = settings.embedding_dim
        return [(b / 255.0) * 2 - 1 for b in (h * (dim // len(h) + 1))[:dim]]

    @property
    def embedding_dim(self) -> int:
        return settings.embedding_dim


# ── Factory ───────────────────────────────────────────────────────────────────

def get_provider() -> AIProvider:
    """
    Factory function returning the configured AI provider.
    Falls back to MockProvider if credentials are missing.
    """
    provider = settings.ai_provider.lower()
    try:
        if provider == "bedrock":
            if not settings.aws_access_key_id:
                logger.warning("Bedrock selected but AWS credentials missing — using mock provider")
                return MockProvider()
            return BedrockProvider()
        elif provider == "gemini":
            if not settings.gemini_api_key:
                logger.warning("Gemini selected but GEMINI_API_KEY missing — using mock provider")
                return MockProvider()
            return GeminiProvider()
        else:
            logger.warning(f"Unknown AI_PROVIDER '{provider}' — using mock provider")
            return MockProvider()
    except Exception as e:
        logger.error(f"Failed to initialize {provider} provider: {e} — using mock provider")
        return MockProvider()


# Singleton instance
_provider_instance: AIProvider | None = None


def provider() -> AIProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = get_provider()
    return _provider_instance
