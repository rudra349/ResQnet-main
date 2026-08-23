# ResQNet

> **"Persistent intelligence for crisis response."**

ResQNet is a low-bandwidth, offline-first Progressive Web App (PWA) for disaster-response coordination powered by a **single AI agent** with **persistent operational memory** stored in **CockroachDB**.

---

## 1. Project Overview

During natural disasters (floods, earthquakes, hurricanes), cellular networks and internet connectivity become degraded or intermittent. Existing disaster maps and AI tools lose state when field workers go offline, creating fragmented data silos and poor coordination.

ResQNet solves this with a **unified operational and semantic memory architecture**. Field workers, relief teams, hospitals, and coordinators interact with a single AI agent that retains experience across sessions and connectivity losses.

---

## 2. The Problem

- **Data Loss During Outages:** Field workers cannot submit incident reports when offline, delaying emergency response.
- **Stateless AI Assistance:** Generic AI chatbots do not remember past decisions, resource allocations, or historical route blockages.
- **Fragmented Database Infrastructure:** Syncing operational state between primary databases and separate vector stores causes sync lag and consistency failures during crises.

---

## 3. The Solution

ResQNet combines:
1. **Offline-First PWA:** Local IndexedDB queue (Dexie.js) allows workers to create reports offline.
2. **Idempotent Synchronization:** Operations auto-sync when online, preventing duplicate reports using client-generated UUID operation IDs.
3. **Single AI Agent:** Controlled tool interfaces query CockroachDB persistent operational and vector memories before reasoning.
4. **CockroachDB Unified Memory:** CockroachDB serves as BOTH the authoritative operational database AND the vector store (using native `VECTOR` types and C-SPANN distributed indexing).

---

## 4. Why Persistent Memory Matters

AI disaster coordination requires remembering experience:
- *“When Road 17 flooded in 2024, relief teams used Road 5 as an alternate route to Shelter Alpha.”*
- *“Shelter Alpha consumes 200 water units per day; with 80 units remaining, resupply is required within 10 hours.”*

Without persistent memory, every AI interaction starts from zero. With CockroachDB, the AI remembers historical events, past recommendations, current inventory, and field reports submitted hours or months ago.

---

## 5. High-Level Architecture

```
                    ┌─────────────────────┐
                    │   Field Worker      │
                    │   PWA / Mobile Web  │
                    └──────────┬──────────┘
                               │
                     Online / Offline
                               │
                    ┌──────────▼──────────┐
                    │  Service Worker     │
                    │  IndexedDB / Queue  │
                    └──────────┬──────────┘
                               │
                         Sync when online
                               │
                    ┌──────────▼──────────┐
                    │     FastAPI         │
                    │      Backend        │
                    └───────┬─────┬───────┘
                            │     │
                ┌───────────┘     └──────────────┐
                ▼                                ▼
       ┌─────────────────┐              ┌────────────────┐
       │  AI Agent       │              │   Amazon S3    │
       │  Single Agent   │              │ Evidence/media │
       └────────┬────────┘              └────────────────┘
                │
                │ read/write memory
                ▼
       ┌────────────────────────────┐
       │       CockroachDB          │
       │                            │
       │ Operational state          │
       │ Incident reports           │
       │ Resource inventory          │
       │ Aid distributions          │
       │ Locations                   │
       │ Agent memories              │
       │ Embeddings                  │
       │ Sync metadata               │
       │ Audit history               │
       └────────────────────────────┘
```

---

## 6. Tech Stack

- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS, `@ducanh2912/next-pwa`, Service Worker, Dexie.js (IndexedDB), Leaflet (CartoDB dark maps), Lucide icons.
- **Backend:** Python 3.12, FastAPI, SQLModel / SQLAlchemy (Async), Pydantic v2, asyncpg, Uvicorn.
- **Database:** CockroachDB Cloud (PostgreSQL-compatible), C-SPANN Distributed Vector Indexing.
- **AI Engine:** Provider abstraction supporting Amazon Bedrock (Claude 3 Haiku + Titan Embeddings v2) and Google Gemini 1.5 Flash (free fallback).
- **AWS Services:** Amazon S3 (evidence storage with local mock option), AWS Lambda (async report analysis trigger).

---

## 7. CockroachDB Capabilities & Features Used

| CockroachDB Feature | How It Is Used in ResQNet |
|---|---|
| **1. Distributed Vector Indexing (C-SPANN)** | The `memories` table stores 1536-dim embeddings. `CREATE VECTOR INDEX ... USING CSPANN` enables sub-linear semantic similarity queries across distributed nodes. |
| **2. Managed MCP Server** | Configured in Claude Desktop / Cursor IDE. Developers and agents inspect live operational memory, audit logs, and schema definitions safely with read-only controls. |
| **3. Unified Operational + Vector Store** | Relational incident state and vector embeddings coexist in CockroachDB, eliminating vector sync latency and guaranteeing ACID consistency. |
| **4. ccloud CLI** | Used for automated cluster provisioning, schema migrations, and real-time database monitoring. |

### Why CockroachDB?
- **PostgreSQL Compatibility:** Uses standard `asyncpg` and SQLAlchemy drivers.
- **Resilience:** Survives node failures during disaster scenarios.
- **Vector + Relational Unity:** No separate vector database required.
- **Consistency:** ACID transactions prevent race conditions during concurrent field syncs.

---

## 8. AWS Services Used

1. **Amazon S3:** Uploads photos, PDFs, and evidence for disaster reports (`/api/evidence/upload`). Includes `USE_S3_MOCK=true` fallback for zero-cost offline development.
2. **AWS Lambda:** `resqnet-report-analyzer` function processes incoming reports asynchronously, generating semantic embeddings and storing AI observations.

---

## 9. Database Schema

- `users` (id, email, hashed_password, role, org_id)
- `organizations` (id, name, type)
- `locations` (id, name, lat, lng, region, type)
- `incidents` (id, type, description, severity, status, location_id)
- `reports` (id, operation_id, content, severity, incident_id, location_id)
- `resources` (id, type, quantity, unit, location_id, status)
- `resource_transactions` (id, resource_id, operation, quantity)
- `shelters` (id, name, location_id, capacity, current_occupancy, water_units)
- `hospitals` (id, name, location_id, bed_total, bed_available)
- `relief_teams` (id, name, org_id, location_id, status)
- `alerts` (id, source, type, severity, region, message, issued_at)
- `memories` (id, memory_type, content, embedding VECTOR(1536), confidence, metadata)
- `decisions` (id, agent_request_id, user_query, recommendation, reasoning, memory_ids_used)
- `sync_operations` (id, operation_id, operation_type, payload, result, sync_status)

---

## 10. AI Memory Architecture

ResQNet categorizes persistent operational memory into 5 distinct categories:
- **Episodic Memory:** Past events ("Truck 17 delivered 100 water units to Shelter 4 in 2024").
- **Semantic Memory:** Embedded vector index of reports and documents for similarity search.
- **Operational Memory:** Real-time state (shelter capacities, road statuses, available supplies).
- **Decision Memory:** Past AI recommendations, confidence scores, and reasoning evidence.
- **Audit Memory:** Change history tracking who updated what resource and when.

---

## 11. Offline Synchronization Design

```
Client (PWA)                     Server (FastAPI + CockroachDB)
  │                                           │
  ├─ User creates report offline               │
  ├─ Store in IndexedDB (Dexie)                │
  │  { operation_id: UUID, status: "pending" } │
  │                                           │
  ├─ Connection Returns ──────────────────────► POST /sync
  │                                           │  Check operation_id in DB
  │                                           │  If exists → return cached result
  │                                           │  If new → process & commit DB
  │  Update IndexedDB ◄───────────────────────┤
  │  { status: "synced" }                      │
```

---

## 12. Local Setup & Quick Start

### Prerequisites
- Node.js 18+ & npm
- Python 3.12+
- Docker & Docker Compose (optional for local CockroachDB)

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/resqnet.git
cd resqnet
```

### Step 2: Configure Environment
```bash
cp .env.example .env
```

### Step 3: Run with Docker (Recommended)
```bash
docker-compose up --build
```
Or start Backend and Frontend manually:

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python ../scripts/seed_demo_data.py
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open browser at `http://localhost:3000`.

---

## 13. Primary Hackathon Demo Scenario (10-Step Story)

1. **Step 1:** Government flood alert published: *"Severe flooding expected in Region Alpha."*
2. **Step 2:** Field Worker A reports: *"Road 17 is flooded and completely inaccessible."*
3. **Step 3:** AI Agent automatically stores the report as semantic & episodic memory in CockroachDB.
4. **Step 4:** Field Worker B asks AI: *"How can Team 4 reach Shelter Alpha with Road 17 flooded?"*
5. **Step 5:** AI retrieves historical memory of the 2024 flood and recommends alternate route via **Road 5**.
6. **Step 6:** Field Worker A temporarily loses internet connectivity (PWA shows **OFFLINE MODE**).
7. **Step 7:** Field Worker A submits report offline: *"Water shortage at Shelter Alpha: 300 units needed."* (Enters local IndexedDB queue).
8. **Step 8:** Connectivity returns. PWA automatically syncs queued reports with CockroachDB (`2 operations synchronized`).
9. **Step 9:** AI Agent is asked: *"Where is water most urgently needed right now?"*
10. **Step 10:** AI retrieves the newly synchronized offline report and recommends dispatching water to Shelter Alpha.

---

## 14. License

This project is licensed under the [MIT License](LICENSE).
