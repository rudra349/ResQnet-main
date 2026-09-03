# ResQNet

> **Persistent-memory AI coordination system for disaster response — offline-first, vector-powered, and built on CockroachDB.**

[![GitHub](https://img.shields.io/badge/GitHub-rudra349-181717?style=flat-square&logo=github)](https://github.com/rudra349)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![CockroachDB](https://img.shields.io/badge/Database-CockroachDB-6933FF?style=flat-square&logo=cockroachlabs&logoColor=white)](https://cockroachlabs.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

---

## Why ResQNet?

When natural disasters like floods, hurricanes, or earthquakes strike, cellular networks and power grids are often the first infrastructure to collapse. This creates critical blind spots for field rescue teams, relief coordinators, and emergency healthcare workers:

- **Responders are cut off:** Most modern apps freeze or lose data when disconnected.
- **AI tools lose context:** Generic AI chatbots are stateless — they forget previous supply runs, road blockages, and operational decisions the moment a session resets.
- **Fragmented data silos:** Managing separate operational databases and vector stores causes synchronization lag and consistency bugs right when reliability matters most.

**ResQNet** solves this by combining an **offline-first Progressive Web App (PWA)** with a **persistent-memory AI agent** backed by **CockroachDB's native vector search**. Whether responders are in a blackout zone or at headquarters, ResQNet logs reports locally, synchronizes seamlessly when connectivity returns, and retains operational intelligence across the full lifecycle of crisis response.

---

## Key Features

- **Offline-First Resilience:** Field workers can submit incident reports, manage resources, and review data without a live connection. All offline data is stored in browser IndexedDB via Dexie.js with automatic sync when connectivity returns.
- **Idempotent Background Sync:** Queued operations use client-generated UUIDs as idempotency keys, guaranteeing zero duplicate submissions on reconnection via a dedicated `/sync` batch endpoint.
- **Persistent AI Operational Memory:** A single-agent AI coordinator with a tool-calling loop retrieves episodic, semantic, operational, decision, and audit memories from CockroachDB before making evidence-backed recommendations.
- **Unified SQL + Vector Store:** CockroachDB stores both relational crisis data and high-dimensional vector embeddings natively, using C-SPANN distributed indexing and the `<->` cosine distance operator for semantic search.
- **Interactive Crisis Command Map:** Real-time geospatial visualization of incidents, shelters, hospitals, supply depots, and relief teams using Leaflet with CartoDB dark tiles.
- **Real-Time Geocoded Location Search:** Uber/Rapido-style free-text location search when reporting incidents — search any city, road, landmark, or address globally and pin it on the crisis map.
- **Google Gemini AI Engine:** Powered by Google Gemini (gemini-3.6-flash + gemini-embedding-001) for intelligent tool calling and vector embeddings, with a deterministic mock provider fallback for testing without API keys.
- **JWT Authentication:** Secure user authentication with role-based access (field worker, coordinator, hospital, admin) using bcrypt password hashing and JWT tokens.
- **16+ Database Models:** Comprehensive data model covering organizations, users, incidents, reports, resources, shelters, hospitals, relief teams, alerts, memories, decisions, evidence, sync operations, audit logs, and more.

---

## System Architecture

```
                    ┌─────────────────────────┐
                    │  Field Worker / HQ App  │
                    │   Next.js 16 PWA        │
                    │   (6 Pages + Navbar)    │
                    └────────────┬────────────┘
                                 │
                   Online / Intermittent / Offline
                                 │
                    ┌────────────▼────────────┐
                    │   Dexie.js (IndexedDB)  │
                    │   Offline Sync Queue    │
                    └────────────┬────────────┘
                                 │
                    Idempotent batch sync (POST /sync)
                                 │
                    ┌────────────▼────────────┐
                    │    FastAPI Backend       │
                    │    (Async Python 3.12)   │
                    │    12 API Routers        │
                    └───────┬─────────┬───────┘
                            │         │
                ┌───────────┘         └──────────────┐
                ▼                                    ▼
       ┌──────────────────┐                ┌──────────────────┐
       │   AI Agent        │               │   Local File     │
       │   (Tool Loop)     │               │   Evidence Storage│
       │   10 Tools        │               │   (Uploads Dir)  │
       │   Google Gemini   │               └──────────────────┘
       └────────┬──────────┘
                │
                │  Query & persist memory
                ▼
       ┌─────────────────────────────────────┐
       │            CockroachDB              │
       │  • 16+ Relational Tables           │
       │  • Vector Embeddings (C-SPANN)     │
       │  • 5 Memory Types                  │
       │  • Audit Logs & Decisions          │
       └─────────────────────────────────────┘
```

---

## Frontend Pages

| Page | Route | Description |
|---|---|---|
| **Command Center** | `/` | Live dashboard with geospatial crisis map, incident telemetry, resource shortages, shelter/hospital metrics, and active alert banners. Auto-refreshes every 15 seconds. |
| **Report Incident** | `/report` | Submit field observations with real-time geocoded location search, severity classification, and scenario shortcuts. Supports offline queuing. |
| **AI Operator** | `/ai` | Query the persistent-memory AI agent. Includes demo scenario presets and displays full agent reasoning with tool calls, retrieved memories, and confidence scores. |
| **Inventory** | `/resources` | View and manage resource stocks and aid requests. Restock, fulfill, or delete entries with optimistic UI updates. |
| **Alerts** | `/alerts` | View and simulate government disaster warnings stored as operational memory for AI context. |
| **Sync Queue** | `/queue` | Inspect the IndexedDB offline queue, trigger manual sync, or clear stuck items. |

---

## AI Agent — Tool-Calling Loop

The AI agent executes a multi-step reasoning loop with **10 controlled tools** as its only interface to the database:

| Tool | Purpose |
|---|---|
| `search_memories` | Semantic vector similarity search across all memory types using CockroachDB's `<->` operator |
| `search_incidents` | Query active/resolved incidents filtered by status, severity, or region |
| `search_resources` | Find available supplies, shortages, and distribution records |
| `search_locations` | Locate shelters, hospitals, villages, and supply depots by name or region |
| `search_previous_events` | Search historical reports, distributions, or aid requests for pattern matching |
| `create_report` | Store a new field observation as operational memory |
| `create_resource_request` | Generate an aid request for resources at a specific location |
| `update_resource_status` | Modify resource quantity or status (distributions, receipts) |
| `create_recommendation` | Store the agent's final evidence-based recommendation as decision memory |
| `retrieve_current_crisis_state` | Get a comprehensive snapshot: active incidents, resource shortages, shelter occupancy, hospital capacity, open requests |

Every agent interaction is persisted as a `Decision` record and a corresponding `decision` memory with vector embedding for future retrieval.

---

## Memory Types in ResQNet

| Memory Type | What It Does | Real-World Example |
|---|---|---|
| **Episodic** | Tracks historical disaster events and past outcomes | *"During the 2024 monsoon flood, Route 5 was the only safe bypass to Shelter Alpha."* |
| **Semantic** | Vector similarity index of ground reports and field notes | Matches vague queries like *"bridge submerged"* to specific incident logs. |
| **Operational** | Real-time live inventory and status tracking | Tracks shelter bed occupancy, water units remaining, and medicine shortages. |
| **Decision** | Retains reasons and confidence scores for past AI choices | Explains why a convoy was diverted to a secondary hospital. |
| **Audit** | Immutable ledger of who updated what resource and when | Maintains full accountability for supply dispatches and status overrides. |

---

## Tech Stack

### Frontend
- **Next.js 16** (App Router) with React 19 and TypeScript
- **Tailwind CSS v4** with `@tailwindcss/postcss`
- **Dexie.js** (IndexedDB) for offline storage and sync queue
- **Leaflet / React-Leaflet** with CartoDB dark tiles for crisis mapping
- **@ducanh2912/next-pwa** for Progressive Web App support
- **@tanstack/react-query** for server state management
- **Lucide React** for icons
- **Axios** for API communication

### Backend
- **Python 3.12**, **FastAPI 0.115**, **Uvicorn**
- **SQLModel / SQLAlchemy 2.0** (Async) with **asyncpg**
- **Pydantic v2** + **pydantic-settings** for config management
- **12 API routers**: auth, incidents, reports, resources, alerts, agent, sync, evidence, memories, dashboard, requests, locations
- **JWT auth** (python-jose + bcrypt/passlib)
- **Alembic** for database migrations

### Database
- **CockroachDB** (PostgreSQL wire-compatible)
- **C-SPANN** distributed vector index for semantic memory search
- **16+ tables**: organizations, users, incidents, reports, resources, resource_transactions, aid_requests, shelters, hospitals, relief_teams, alerts, memories, decisions, evidence, sync_operations, audit_logs

### AI & ML
- **Google Gemini** (gemini-3.6-flash for chat, gemini-embedding-001 for 768-D embeddings) via `google-genai` SDK
- **Mock Provider** for testing/CI without API credentials (deterministic hash-based pseudo-embeddings)

---

## Quick Start

### Prerequisites

- **Python 3.12+** and `pip`
- **Node.js 18+** and `npm`
- **Git**
- **Docker & Docker Compose** *(required for CockroachDB, or install CockroachDB locally)*

---

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/rudra349/ResQnet-main.git
cd ResQnet-main

# 2. Set up environment variables
cp .env.example .env
# Edit .env — set your GEMINI_API_KEY

# 3. Build and launch all containers (CockroachDB + Backend + Frontend)
docker compose up --build
```

Access the app at `http://localhost:3000`. Backend API docs at `http://localhost:8000/docs`.

---

### Option 2: Run Locally (Manual Setup)

#### 1. Clone & Prepare Environment

```bash
git clone https://github.com/rudra349/ResQnet-main.git
cd ResQnet-main
cp .env.example .env
# Edit .env — set GEMINI_API_KEY (get one free at https://aistudio.google.com/app/apikey)
```

#### 2. Start CockroachDB

```bash
# Using Docker (simplest):
docker run -d --name cockroachdb -p 26257:26257 -p 8080:8080 \
  cockroachdb/cockroach:latest-v24.3 start-single-node --insecure --store=type=mem,size=512MB
```

> **Note:** CockroachDB Admin UI will be available at [http://localhost:8080](http://localhost:8080).

#### 3. Start the Backend

In a dedicated terminal:

```bash
cd backend

# Create and activate Python virtual environment
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# (Optional) Seed demo data — shelters, hospitals, resources, sample memories
python ../scripts/seed_demo_data.py

# Launch FastAPI with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Note:** Backend interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

#### 4. Start the Frontend

In a second terminal:

```bash
cd frontend

# Install Node dependencies
npm install

# Run the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

### Makefile Shortcuts

```bash
make dev              # Docker Compose up (all services)
make dev-backend      # Backend only (uvicorn)
make dev-frontend     # Frontend only (next dev)
make seed             # Seed demo data into CockroachDB
make test             # Run backend tests
make install          # Install all dependencies (pip + npm)
```

---

## Environment Variables

Key variables in `.env` (see [`.env.example`](.env.example) for the full list):

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | CockroachDB connection string | `postgresql+asyncpg://root@localhost:26257/resqnet` |
| `AI_PROVIDER` | AI backend | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key ([get one free](https://aistudio.google.com/app/apikey)) | *(required for AI)* |
| `GEMINI_MODEL` | Gemini chat model | `gemini-3.6-flash` |
| `EMBEDDING_DIM` | Embedding vector dimension (768 for Gemini) | `768` |
| `NEXT_PUBLIC_API_URL` | Backend URL for the frontend | `http://localhost:8000` |

---

## Interactive Walkthrough Demo

Here's a walkthrough simulating a live flood crisis:

1. **Open the Command Center** at `http://localhost:3000` — see the geospatial crisis map with active incidents, shelters, and hospitals plotted in real-time.
2. **Report an Incident:** Navigate to **Report Incident**, search for a real location (e.g., "YMCA Road, Jubilee Hills"), type *"Road 17 is heavily flooded near Shelter 7. Vehicles cannot pass."*, set severity to **Critical**, and submit. Watch it appear instantly on the Command Center map.
3. **Ask the AI Agent:** Go to **AI Operator** and ask: *"How can Team 4 reach Shelter Alpha with Road 17 flooded?"* — the agent searches vector memories, retrieves historical flood data, and recommends an alternate route with confidence scores.
4. **Simulate Offline Mode:** In DevTools (F12 → Network tab), switch to **Offline**. The navbar sync badge changes to **OFFLINE MODE**.
5. **Submit While Disconnected:** Report a supply shortage: *"Shelter Alpha running out of potable water (need 300 units)."* — it saves safely to IndexedDB. Visit **Sync Queue** to see the pending item.
6. **Reconnect & Auto-Sync:** Switch back to **Online**. Click **Sync Now** on the queue page — the operation syncs to CockroachDB with idempotency guarantees.
7. **AI Remembers:** Ask the AI: *"Where is water urgently needed?"* — it immediately factors in the newly synced report and recommends dispatching water to Shelter Alpha.

---

## Repository Structure

```text
ResQnet-main/
├── backend/                      # FastAPI Application
│   ├── app/
│   │   ├── agents/               # AI agent, LLM providers (Gemini/Mock), 10 tools
│   │   │   ├── agent.py          # Tool-calling loop: retrieve → reason → recommend → store
│   │   │   ├── provider.py       # AIProvider ABC + Gemini, Mock implementations
│   │   │   └── tools.py          # 10 tool definitions & executors
│   │   ├── api/                  # 12 REST API routers
│   │   │   ├── agent.py          # POST /agent/chat
│   │   │   ├── alerts.py         # CRUD alerts
│   │   │   ├── auth.py           # Register/login, JWT tokens
│   │   │   ├── dashboard.py      # GET /dashboard/summary
│   │   │   ├── evidence.py       # File uploads
│   │   │   ├── incidents.py      # CRUD incidents with memory creation
│   │   │   ├── locations.py      # CRUD locations
│   │   │   ├── memories.py       # Memory retrieval API
│   │   │   ├── reports.py        # Field report CRUD
│   │   │   ├── requests_api.py   # Aid request CRUD
│   │   │   ├── resources.py      # Resource inventory management
│   │   │   └── sync.py           # Batch sync endpoint (idempotent)
│   │   ├── auth/                 # JWT + bcrypt auth utilities
│   │   ├── db/                   # SQLAlchemy engine, CockroachDB compatibility, 16+ models
│   │   ├── memory/               # Vector embeddings & similarity retrieval
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── sync/                 # Offline sync processor
│   │   ├── config.py             # pydantic-settings configuration
│   │   └── main.py               # FastAPI app entrypoint & lifespan
│   ├── tests/                    # pytest test suite
│   ├── uploads/                  # Local media storage directory
│   └── requirements.txt          # Python dependencies
├── frontend/                     # Next.js 16 PWA
│   ├── app/                      # App Router pages
│   │   ├── page.tsx              # Command Center dashboard
│   │   ├── report/page.tsx       # Incident reporting with geocoding
│   │   ├── ai/page.tsx           # AI Operator dispatch assistant
│   │   ├── resources/page.tsx    # Resource inventory & aid requests
│   │   ├── alerts/page.tsx       # Disaster warnings & simulated alerts
│   │   ├── queue/page.tsx        # Offline sync queue inspector
│   │   ├── layout.tsx            # Root layout
│   │   ├── manifest.ts           # PWA manifest
│   │   └── globals.css           # Global styles
│   ├── components/               # Reusable UI components
│   │   ├── AgentResponse.tsx     # AI agent response card with tool trace
│   │   ├── LeafletMapInner.tsx   # Crisis map with markers & popups
│   │   ├── LocationSearch.tsx    # Geocoded location search (Uber-style)
│   │   ├── Map.tsx               # Dynamic map wrapper
│   │   ├── Navbar.tsx            # App navigation with mobile support
│   │   ├── SyncBadge.tsx         # Online/offline status badge
│   │   └── SystemTelemetryBar.tsx # System status telemetry bar
│   ├── hooks/                    # Custom React hooks
│   │   ├── useOnline.ts          # Network connectivity detection
│   │   └── useSync.ts            # Sync queue state management
│   ├── lib/                      # Utilities & offline infrastructure
│   │   ├── axios.ts              # Axios API client
│   │   ├── types.ts              # TypeScript type definitions
│   │   └── offline/              # Dexie.js IndexedDB + queue logic
│   │       ├── db.ts             # IndexedDB schema (5 tables)
│   │       └── queue.ts          # Enqueue & sync operations
│   └── public/                   # PWA icons & static assets
├── docs/                         # Architecture & demo documentation
│   ├── architecture.md
│   └── demo.md
├── scripts/
│   └── seed_demo_data.py         # Database seeding script (30KB+ of demo data)
├── docker-compose.yml            # CockroachDB + Backend + Frontend orchestration
├── Makefile                      # Developer convenience commands
├── .env.example                  # Environment variable template
├── LICENSE                       # MIT License
└── README.md
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Contributing

Contributions, feedback, and issue reports are welcome!

1. Fork the Project (`https://github.com/rudra349/ResQnet-main`)
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## Author

Developed and maintained by **Rudra** ([@rudra349](https://github.com/rudra349)).

- **GitHub:** [https://github.com/rudra349](https://github.com/rudra349)

---

## License

This project is open source and available under the [MIT License](LICENSE).
