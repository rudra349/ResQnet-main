# ResQNet — Architecture Deep Dive

## Overview

ResQNet is an offline-first crisis coordination system designed around a single AI agent with persistent operational memory stored in CockroachDB.

## System Topology

```
┌─────────────────────────────────────────────────────────────┐
│                       PWA Frontend                          │
│  Next.js 15 + React 19 + TypeScript + Tailwind CSS          │
│  - Service Worker (Workbox)                                 │
│  - IndexedDB Store (Dexie.js)                               │
│  - Reactive Sync Queue Hook (useSync)                       │
│  - Leaflet CartoDB Dark Maps                                │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  Python 3.12 + SQLModel + AsyncPG                           │
│  - Idempotent Sync Processor (operation_id deduplication)   │
│  - Controlled AI Agent Tool Functions (10 tools)            │
│  - Provider Abstraction (Amazon Bedrock / Google Gemini)    │
│  - AWS S3 Evidence Client (with local mock option)          │
│  - AWS Lambda Trigger (report analyzer)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Async SQL / pgvector
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    CockroachDB Cloud                        │
│  Distributed SQL + Native VECTOR Storage                    │
│  - Operational Tables (incidents, resources, shelters)      │
│  - Memories Table with VECTOR(1536) & C-SPANN Index         │
│  - Idempotency Ledger (sync_operations)                     │
│  - Managed MCP Server                                       │
└─────────────────────────────────────────────────────────────┘
```

## Core Architectural Guarantees

1. **Idempotency**: Every client action generates a UUID `operation_id` before transmission. The server checks `sync_operations` before processing.
2. **ACID Operational + Vector Memory**: Relational state and embeddings live in the same CockroachDB instance, avoiding sync lag.
3. **Graceful Fallbacks**: If AI services fail, core report creation and resource tracking remain 100% operational.
