"""
ResQNet — Demo Data Seeder
Seeds realistic fictional disaster scenario data.
Scenario: Severe flooding in Region Alpha.
Run: python scripts/seed_demo_data.py
"""
from __future__ import annotations

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta
import random

# Configure stdout for Windows console UTF-8 support
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.engine import create_db_and_tables, init_vector_index, AsyncSessionLocal
from app.db.models import (
    Organization, Location, User, Incident, Report, Resource,
    ResourceTransaction, AidRequest, Shelter, Hospital, ReliefTeam,
    Alert, Memory, Decision,
    OrgType, LocationType, UserRole, IncidentType, IncidentSeverity,
    IncidentStatus, ResourceType, ResourceStatus, ResourceOperation,
    RequestStatus, RequestPriority, AlertSeverity, MemoryType,
)
from app.auth.auth import hash_password
from app.memory.retrieval import store_memory
from app.agents.provider import provider

NOW = datetime.utcnow()
ago = lambda **kw: NOW - timedelta(**kw)


async def seed():
    print("🌱 Seeding ResQNet demo data...")
    await create_db_and_tables()
    await init_vector_index()

    ai = provider()

    async with AsyncSessionLocal() as session:
        # ── Organizations ────────────────────────────────────────────────────
        print("  Creating organizations...")
        orgs = {
            "central": Organization(name="Region Alpha Coordination Center", type=OrgType.government),
            "relief": Organization(name="Alpha Relief Foundation", type=OrgType.ngo),
            "hospital_org": Organization(name="Alpha Medical Services", type=OrgType.hospital),
            "community": Organization(name="Village Alpha Community", type=OrgType.community),
        }
        for o in orgs.values():
            session.add(o)
        await session.flush()

        # ── Locations ────────────────────────────────────────────────────────
        print("  Creating locations...")
        locs = {
            # Villages
            "village_alpha": Location(name="Village Alpha", lat=28.6139, lng=77.2090, region="Region Alpha", type=LocationType.village, description="Primary village, population ~1200"),
            "village_bravo": Location(name="Village Bravo", lat=28.6250, lng=77.2200, region="Region Alpha", type=LocationType.village, description="Elevated village, population ~800"),
            "village_charlie": Location(name="Village Charlie", lat=28.6050, lng=77.1980, region="Region Alpha", type=LocationType.village, description="Low-lying, flood-prone, population ~600"),
            # Shelters
            "shelter_alpha": Location(name="Shelter Alpha", lat=28.6180, lng=77.2150, region="Region Alpha", type=LocationType.shelter),
            "shelter_bravo": Location(name="Shelter Bravo", lat=28.6300, lng=77.2260, region="Region Alpha", type=LocationType.shelter),
            "shelter_charlie": Location(name="Shelter Charlie", lat=28.6100, lng=77.2020, region="Region Alpha", type=LocationType.shelter),
            # Hospitals
            "hospital_central": Location(name="Hospital Central", lat=28.6200, lng=77.2100, region="Region Alpha", type=LocationType.hospital),
            "hospital_east": Location(name="Hospital East", lat=28.6320, lng=77.2350, region="Region Alpha", type=LocationType.hospital),
            # Supply depots
            "depot_main": Location(name="Main Supply Depot", lat=28.6150, lng=77.2050, region="Region Alpha", type=LocationType.supply_depot),
            # Road points
            "road_17": Location(name="Road 17 Junction", lat=28.6080, lng=77.2000, region="Region Alpha", type=LocationType.road, description="Key access road between Village Charlie and Shelter Alpha"),
            "road_5": Location(name="Road 5 (Alternate)", lat=28.6070, lng=77.2030, region="Region Alpha", type=LocationType.road, description="Alternate elevated route, passable in flood"),
            # Relief team bases
            "team_base_1": Location(name="Team Base Alpha", lat=28.6160, lng=77.2080, region="Region Alpha", type=LocationType.relief_team_base),
            "team_base_2": Location(name="Team Base Bravo", lat=28.6280, lng=77.2240, region="Region Alpha", type=LocationType.relief_team_base),
        }
        for l in locs.values():
            session.add(l)
        await session.flush()

        # ── Shelters ─────────────────────────────────────────────────────────
        print("  Creating shelters...")
        shelter_objs = {
            "alpha": Shelter(name="Shelter Alpha", location_id=locs["shelter_alpha"].id, capacity=500, current_occupancy=420, water_units=80, food_units=150, status="open"),
            "bravo": Shelter(name="Shelter Bravo", location_id=locs["shelter_bravo"].id, capacity=350, current_occupancy=280, water_units=220, food_units=200, status="open"),
            "charlie": Shelter(name="Shelter Charlie", location_id=locs["shelter_charlie"].id, capacity=250, current_occupancy=180, water_units=300, food_units=280, status="open"),
        }
        for s in shelter_objs.values():
            session.add(s)

        # ── Hospitals ────────────────────────────────────────────────────────
        print("  Creating hospitals...")
        hosp_objs = {
            "central": Hospital(name="Hospital Central", location_id=locs["hospital_central"].id, bed_total=120, bed_available=23, icu_total=12, icu_available=2, status="operational"),
            "east": Hospital(name="Hospital East", location_id=locs["hospital_east"].id, bed_total=80, bed_available=41, icu_total=8, icu_available=5, status="operational"),
        }
        for h in hosp_objs.values():
            session.add(h)

        # ── Relief Teams ─────────────────────────────────────────────────────
        print("  Creating relief teams...")
        teams = [
            ReliefTeam(name="Team Alpha-1", org_id=orgs["relief"].id, location_id=locs["team_base_1"].id, status="deployed", member_count=8, vehicle_count=2, specialization="search_rescue"),
            ReliefTeam(name="Team Alpha-2", org_id=orgs["relief"].id, location_id=locs["team_base_1"].id, status="deployed", member_count=6, vehicle_count=2, specialization="medical"),
            ReliefTeam(name="Team Alpha-3", org_id=orgs["central"].id, location_id=locs["team_base_2"].id, status="standby", member_count=10, vehicle_count=3, specialization="logistics"),
            ReliefTeam(name="Team Alpha-4", org_id=orgs["relief"].id, location_id=locs["team_base_2"].id, status="deployed", member_count=7, vehicle_count=2, specialization="water_sanitation"),
            ReliefTeam(name="Team Alpha-5", org_id=orgs["hospital_org"].id, location_id=locs["hospital_central"].id, status="on_call", member_count=5, vehicle_count=1, specialization="trauma_medical"),
        ]
        for t in teams:
            session.add(t)

        # ── Users ────────────────────────────────────────────────────────────
        print("  Creating demo users...")
        users = [
            User(email="demo@resqnet.io", name="Demo User", hashed_password=hash_password("demo1234"), role=UserRole.coordinator),
            User(email="field1@resqnet.io", name="Field Worker A", hashed_password=hash_password("demo1234"), role=UserRole.field_worker, org_id=orgs["relief"].id),
            User(email="field2@resqnet.io", name="Field Worker B", hashed_password=hash_password("demo1234"), role=UserRole.field_worker, org_id=orgs["relief"].id),
            User(email="hospital@resqnet.io", name="Dr. Hospital Central", hashed_password=hash_password("demo1234"), role=UserRole.hospital, org_id=orgs["hospital_org"].id),
        ]
        for u in users:
            session.add(u)
        await session.flush()

        # ── Alerts ───────────────────────────────────────────────────────────
        print("  Creating alerts...")
        alerts = [
            Alert(source="government", type="flood_warning", severity=AlertSeverity.extreme,
                  region="Region Alpha", issued_at=ago(hours=6), is_active=True,
                  message="SEVERE FLOOD WARNING: Region Alpha — Major flooding expected. All low-lying areas must evacuate immediately. Road 17 may become inaccessible."),
            Alert(source="weather", type="rainfall_alert", severity=AlertSeverity.severe,
                  region="Region Alpha", issued_at=ago(hours=4), is_active=True,
                  message="Continuous heavy rainfall forecast for next 48 hours. River levels critically elevated."),
            Alert(source="government", type="evacuation_order", severity=AlertSeverity.extreme,
                  region="Village Charlie", issued_at=ago(hours=3), is_active=True,
                  message="MANDATORY EVACUATION: Village Charlie. Proceed to Shelter Alpha or Shelter Charlie via Road 5."),
        ]
        for a in alerts:
            session.add(a)

        # ── Resources ────────────────────────────────────────────────────────
        print("  Creating resources...")
        resources = [
            Resource(type=ResourceType.water, quantity=80, unit="units", location_id=locs["shelter_alpha"].id, org_id=orgs["relief"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.food, quantity=150, unit="meal_packs", location_id=locs["shelter_alpha"].id, org_id=orgs["relief"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.water, quantity=220, unit="units", location_id=locs["shelter_bravo"].id, org_id=orgs["relief"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.food, quantity=200, unit="meal_packs", location_id=locs["shelter_bravo"].id, org_id=orgs["relief"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.water, quantity=300, unit="units", location_id=locs["shelter_charlie"].id, org_id=orgs["relief"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.medicine, quantity=45, unit="kits", location_id=locs["depot_main"].id, org_id=orgs["hospital_org"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.blankets, quantity=600, unit="pieces", location_id=locs["depot_main"].id, org_id=orgs["relief"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.fuel, quantity=200, unit="liters", location_id=locs["team_base_1"].id, org_id=orgs["central"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.medical_supplies, quantity=30, unit="kits", location_id=locs["hospital_central"].id, org_id=orgs["hospital_org"].id, status=ResourceStatus.available),
            Resource(type=ResourceType.vehicles, quantity=3, unit="trucks", location_id=locs["depot_main"].id, org_id=orgs["central"].id, status=ResourceStatus.available),
        ]
        for r in resources:
            session.add(r)
        await session.flush()

        # ── Incidents ────────────────────────────────────────────────────────
        print("  Creating incidents (20)...")
        incidents = [
            Incident(type=IncidentType.flood, description="Major flooding in Village Charlie low-lying areas. 3 homes submerged.", severity=IncidentSeverity.critical, status=IncidentStatus.active, location_id=locs["village_charlie"].id, created_at=ago(hours=5, minutes=30)),
            Incident(type=IncidentType.road_blocked, description="Road 17 completely flooded and inaccessible. No vehicle passage possible.", severity=IncidentSeverity.critical, status=IncidentStatus.active, location_id=locs["road_17"].id, created_at=ago(hours=4, minutes=45)),
            Incident(type=IncidentType.supply_shortage, description="Shelter Alpha critically low on water. Only 80 units remaining for 420 people.", severity=IncidentSeverity.critical, status=IncidentStatus.active, location_id=locs["shelter_alpha"].id, created_at=ago(hours=0, minutes=18)),
            Incident(type=IncidentType.medical, description="Hospital Central ICU at 83% capacity. Critical patient overflow risk.", severity=IncidentSeverity.high, status=IncidentStatus.active, location_id=locs["hospital_central"].id, created_at=ago(hours=2)),
            Incident(type=IncidentType.evacuation, description="Village Charlie evacuation in progress. 180/600 residents relocated.", severity=IncidentSeverity.high, status=IncidentStatus.active, location_id=locs["village_charlie"].id, created_at=ago(hours=3)),
            Incident(type=IncidentType.structural_damage, description="Bridge on Road 17 has structural damage from flood water pressure.", severity=IncidentSeverity.high, status=IncidentStatus.investigating, location_id=locs["road_17"].id, created_at=ago(hours=3, minutes=30)),
            Incident(type=IncidentType.supply_shortage, description="Medicine kits running low at field clinic in Village Alpha.", severity=IncidentSeverity.high, status=IncidentStatus.active, location_id=locs["village_alpha"].id, created_at=ago(hours=1, minutes=30)),
            Incident(type=IncidentType.flood, description="Water level rising near Village Alpha perimeter. Monitoring required.", severity=IncidentSeverity.medium, status=IncidentStatus.active, location_id=locs["village_alpha"].id, created_at=ago(hours=2, minutes=15)),
            Incident(type=IncidentType.shelter_needed, description="Family of 7 stranded at high point near Village Charlie — awaiting rescue.", severity=IncidentSeverity.critical, status=IncidentStatus.active, location_id=locs["village_charlie"].id, created_at=ago(minutes=45)),
            Incident(type=IncidentType.road_blocked, description="Road 5 partially blocked by debris but passable for high-clearance vehicles.", severity=IncidentSeverity.medium, status=IncidentStatus.active, location_id=locs["road_5"].id, created_at=ago(hours=1)),
            # Historical incidents (resolved) — these make the AI retrieve useful memories
            Incident(type=IncidentType.road_blocked, description="Road 7 blocked during 2024 monsoon — alternate via Road 5 used successfully.", severity=IncidentSeverity.high, status=IncidentStatus.resolved, location_id=locs["road_17"].id, created_at=ago(days=365)),
            Incident(type=IncidentType.supply_shortage, description="Shelter Alpha water shortage in 2024 monsoon — resolved by routing from Depot Main.", severity=IncidentSeverity.high, status=IncidentStatus.resolved, location_id=locs["shelter_alpha"].id, created_at=ago(days=362)),
            Incident(type=IncidentType.flood, description="Village Charlie 2024 flood — elevated areas remained safe.", severity=IncidentSeverity.critical, status=IncidentStatus.resolved, location_id=locs["village_charlie"].id, created_at=ago(days=363)),
            Incident(type=IncidentType.medical, description="Hospital Central 2024 flood surge — overflow patients sent to Hospital East.", severity=IncidentSeverity.high, status=IncidentStatus.resolved, location_id=locs["hospital_central"].id, created_at=ago(days=360)),
            Incident(type=IncidentType.supply_shortage, description="2024: Blanket shortage at Shelter Bravo resolved in 4 hours via Depot Main.", severity=IncidentSeverity.medium, status=IncidentStatus.resolved, location_id=locs["shelter_bravo"].id, created_at=ago(days=358)),
            Incident(type=IncidentType.flood, description="2023: Village Alpha east-side road flooded — passable 6 hours after rainfall stopped.", severity=IncidentSeverity.medium, status=IncidentStatus.resolved, location_id=locs["village_alpha"].id, created_at=ago(days=730)),
            Incident(type=IncidentType.road_blocked, description="2023: Truck 9 diverted via Road 5 alternate when Road 17 blocked.", severity=IncidentSeverity.medium, status=IncidentStatus.resolved, location_id=locs["road_17"].id, created_at=ago(days=728)),
            Incident(type=IncidentType.evacuation, description="2023: Village Charlie partial evacuation — 240 residents to Shelter Alpha.", severity=IncidentSeverity.high, status=IncidentStatus.resolved, location_id=locs["village_charlie"].id, created_at=ago(days=727)),
            Incident(type=IncidentType.medical, description="Mass casualty drill revealed Hospital East as best surge facility.", severity=IncidentSeverity.low, status=IncidentStatus.resolved, location_id=locs["hospital_east"].id, created_at=ago(days=180)),
            Incident(type=IncidentType.supply_shortage, description="2024 post-flood: Water distribution optimized to 1 unit per 2 people per day.", severity=IncidentSeverity.medium, status=IncidentStatus.resolved, location_id=locs["depot_main"].id, created_at=ago(days=355)),
        ]
        for i in incidents:
            session.add(i)
        await session.flush()

        # ── Reports ──────────────────────────────────────────────────────────
        print("  Creating reports (30)...")
        report_texts = [
            ("Road 17 is flooded and completely inaccessible. Truck 17 cannot pass. Water depth estimated at 1.5 meters.", IncidentSeverity.critical, locs["road_17"]),
            ("Shelter Alpha has 420 people and only 80 water units left. Urgent resupply needed immediately.", IncidentSeverity.critical, locs["shelter_alpha"]),
            ("Family of 7 stranded at house near Village Charlie perimeter. Need boat rescue.", IncidentSeverity.critical, locs["village_charlie"]),
            ("Hospital Central ICU has only 2 beds left. Diverting non-critical patients to Hospital East.", IncidentSeverity.high, locs["hospital_central"]),
            ("Road 5 is passable but slow — debris on one side. High clearance vehicles can proceed.", IncidentSeverity.medium, locs["road_5"]),
            ("Village Charlie evacuation: 180 people moved to Shelter Alpha. 420 remaining.", IncidentSeverity.high, locs["village_charlie"]),
            ("Medicine kits running low at Village Alpha field clinic. Need resupply from Depot Main.", IncidentSeverity.high, locs["village_alpha"]),
            ("Shelter Bravo has sufficient supplies. 280 people, 220 water units, 200 food packs.", IncidentSeverity.low, locs["shelter_bravo"]),
            ("Water level at Village Charlie creek rising 10cm per hour. Monitor closely.", IncidentSeverity.high, locs["village_charlie"]),
            ("Team Alpha-4 reached Shelter Charlie via Road 5. Distributing water sanitation kits.", IncidentSeverity.medium, locs["shelter_charlie"]),
            # Historical reports (AI retrieves these for context)
            ("2024: During last flood, Road 17 remained blocked for 36 hours. Road 5 was the only viable alternate.", IncidentSeverity.high, locs["road_17"]),
            ("2024: Shelter Alpha water crisis resolved by emergency transfer of 500 units from Depot Main.", IncidentSeverity.high, locs["shelter_alpha"]),
            ("2024: Village Charlie high ground remained dry throughout flood. Recommend pre-positioning there.", IncidentSeverity.medium, locs["village_charlie"]),
            ("2024: Hospital East absorbed 34 overflow patients from Hospital Central during peak flood.", IncidentSeverity.medium, locs["hospital_east"]),
            ("2024: Truck 4 used Road 5 alternate to reach Shelter Alpha in 28 minutes vs 15 via Road 17.", IncidentSeverity.low, locs["road_5"]),
            ("2024: Water distribution ratio of 0.5 units/person/day proved sustainable for 72-hour emergency.", IncidentSeverity.medium, locs["depot_main"]),
            ("2023: Shelter Alpha reliably receives supply trucks via Road 5 during flood season.", IncidentSeverity.low, locs["shelter_alpha"]),
            ("2023: Village Charlie residents most vulnerable during flooding — lowest elevation in region.", IncidentSeverity.high, locs["village_charlie"]),
            ("2023: Team Alpha-3 logistics team successfully coordinated 3 simultaneous shelter resupplies.", IncidentSeverity.low, locs["team_base_2"]),
            ("2023: Hospital Central should initiate overflow protocol when ICU exceeds 80% capacity.", IncidentSeverity.medium, locs["hospital_central"]),
            # More current reports
            ("Shelter Charlie currently comfortable — 180 people, supplies adequate. Can accept 70 more.", IncidentSeverity.low, locs["shelter_charlie"]),
            ("Team Alpha-1 conducting search and rescue in Village Charlie low ground.", IncidentSeverity.high, locs["village_charlie"]),
            ("Fuel stocks at Team Base Alpha running low — 200L remaining for 4 vehicles.", IncidentSeverity.medium, locs["team_base_1"]),
            ("Depot Main has 600 blankets and 10 trucks worth of supplies ready to deploy.", IncidentSeverity.low, locs["depot_main"]),
            ("Team Alpha-2 medical team treating 12 patients at Village Alpha field clinic.", IncidentSeverity.medium, locs["village_alpha"]),
            ("Bridge on Road 17 shows cracks — engineering assessment needed before reopening.", IncidentSeverity.high, locs["road_17"]),
            ("Hospital East reports 41 beds available and willing to accept flood patients.", IncidentSeverity.low, locs["hospital_east"]),
            ("Village Bravo elevated position — no flooding. Residents safe. Can host 200 additional evacuees.", IncidentSeverity.low, locs["village_bravo"]),
            ("Shelter Alpha sanitation becoming strained with 420 occupants. Extra portable facilities needed.", IncidentSeverity.medium, locs["shelter_alpha"]),
            ("Road 5 alternate confirmed passable as of 30 minutes ago. Route: Village Charlie → Road 5 → Shelter Alpha.", IncidentSeverity.low, locs["road_5"]),
        ]
        report_objs = []
        for i, (content, severity, location) in enumerate(report_texts):
            r = Report(
                operation_id=uuid.uuid4(),
                content=content,
                severity=severity,
                location_id=location.id,
                created_at=ago(hours=random.randint(0, 48), minutes=random.randint(0, 59)),
            )
            session.add(r)
            report_objs.append((r, content, location))
        await session.flush()

        # ── Aid Requests ─────────────────────────────────────────────────────
        print("  Creating aid requests...")
        aid_requests = [
            AidRequest(type="water", description="Shelter Alpha urgently needs 500 water units.", location_id=locs["shelter_alpha"].id, status=RequestStatus.open, priority=RequestPriority.critical, quantity_needed=500, unit="units"),
            AidRequest(type="medicine", description="Village Alpha field clinic needs 20 medicine kits.", location_id=locs["village_alpha"].id, status=RequestStatus.open, priority=RequestPriority.high, quantity_needed=20, unit="kits"),
            AidRequest(type="rescue_boat", description="Boat needed for Village Charlie stranded family rescue.", location_id=locs["village_charlie"].id, status=RequestStatus.in_progress, priority=RequestPriority.critical),
            AidRequest(type="food", description="Shelter Alpha food stocks depleting — need 200 meal packs.", location_id=locs["shelter_alpha"].id, status=RequestStatus.open, priority=RequestPriority.high, quantity_needed=200, unit="meal_packs"),
            AidRequest(type="sanitation", description="Portable sanitation facilities for Shelter Alpha (420 people).", location_id=locs["shelter_alpha"].id, status=RequestStatus.open, priority=RequestPriority.medium),
            AidRequest(type="fuel", description="Team Base Alpha needs 300L of fuel to continue operations.", location_id=locs["team_base_1"].id, status=RequestStatus.acknowledged, priority=RequestPriority.high, quantity_needed=300, unit="liters"),
            AidRequest(type="medical_team", description="Hospital Central overflow — need additional medical staff.", location_id=locs["hospital_central"].id, status=RequestStatus.open, priority=RequestPriority.high),
            AidRequest(type="blankets", description="Shelter Charlie needs 100 blankets for new evacuees.", location_id=locs["shelter_charlie"].id, status=RequestStatus.fulfilled, priority=RequestPriority.medium),
        ]
        for req in aid_requests:
            session.add(req)

        await session.flush()

        # ── Memories (pre-seeded for AI retrieval) ───────────────────────────
        print("  Creating operational memories (10 historical)...")
        memory_contents = [
            ("Episodic: During the 2024 monsoon flood, Road 17 was blocked for 36 hours. Relief trucks successfully used Road 5 as an alternate route to reach Shelter Alpha and Shelter Charlie. Road 5 added 15 minutes to each delivery.", MemoryType.episodic, locs["road_17"]),
            ("Episodic: Shelter Alpha water shortage in 2024. Resolution: Emergency transfer of 500 water units from Depot Main via Road 5. Took 45 minutes. Current shortage pattern matches 2024 incident.", MemoryType.episodic, locs["shelter_alpha"]),
            ("Operational: Shelter Alpha capacity is 500. Current occupancy: 420. Water consumption: approximately 2 units per person per day. At current rate, water (80 units) will last 10 hours.", MemoryType.operational, locs["shelter_alpha"]),
            ("Operational: Shelter Bravo has 280 occupants with 220 water units and 200 food packs. Sufficient for 72 hours without resupply. Last restocked 45 minutes ago.", MemoryType.operational, locs["shelter_bravo"]),
            ("Episodic: Village Charlie is the most flood-vulnerable location in Region Alpha due to lowest elevation. In 2023 and 2024, it was the first area to flood and last to recover. Recommend proactive evacuation.", MemoryType.episodic, locs["village_charlie"]),
            ("Decision [2024 Monsoon]: Water shortage at Shelter Alpha. Recommendation: Route 500 units via Road 5. Rationale: Road 17 blocked, Road 5 passable for trucks. Outcome: Delivered in 45 min, shortage resolved. Confidence: 94%", MemoryType.decision, locs["shelter_alpha"]),
            ("Episodic: Hospital Central overflow protocol: When ICU exceeds 80% capacity, non-critical patients transferred to Hospital East. Hospital East has historically had 40+ beds available. Transfer takes 20 minutes by ambulance.", MemoryType.episodic, locs["hospital_central"]),
            ("Operational: Road 5 confirmed passable 30 minutes ago. High-clearance vehicles only. One lane passable. Time to Shelter Alpha from Depot Main: 28 minutes via Road 5. Road 17 remains flooded and blocked.", MemoryType.operational, locs["road_5"]),
            ("Episodic: Team Alpha-4 specializes in water/sanitation operations. They successfully ran 3 simultaneous shelter resupply missions in the 2024 flood. They are currently at Team Base Bravo.", MemoryType.episodic, None),
            ("Operational: Depot Main inventory: 600 blankets, 45 medicine kits, 3 trucks available, 200L fuel. This is the primary regional supply cache. All items ready for immediate deployment.", MemoryType.operational, locs["depot_main"]),
        ]

        for content, mtype, location in memory_contents:
            try:
                embedding = await ai.embed(content)
            except Exception:
                embedding = None
            memory = Memory(
                memory_type=mtype,
                content=content,
                embedding=embedding,
                source_type="historical",
                location_id=location.id if location else None,
                confidence=0.95 if mtype == MemoryType.episodic else 1.0,
                created_at=ago(days=random.randint(1, 400)),
                metadata_={"seeded": True, "scenario": "region_alpha_flood"},
            )
            session.add(memory)

        # Also store recent reports as semantic memories
        print("  Generating semantic memory embeddings for reports...")
        for report, content, location in report_objs[:15]:  # First 15 reports
            try:
                embedding = await ai.embed(content)
            except Exception:
                embedding = None
            memory = Memory(
                memory_type=MemoryType.semantic,
                content=content,
                embedding=embedding,
                source_type="report",
                source_id=report.id,
                location_id=location.id if location else None,
                confidence=0.9,
                created_at=report.created_at,
                metadata_={"seeded": True},
            )
            session.add(memory)

        await session.commit()
        print("\n✅ Demo data seeded successfully!")
        print("\n📊 Summary:")
        print("   3 villages, 3 shelters, 2 hospitals, 5 teams")
        print("   20 incidents (10 active, 10 historical/resolved)")
        print("   30 field reports")
        print("   10 resources + 3 alerts")
        print("   10 pre-seeded historical memories")
        print("   8 aid requests")
        print("\n🔑 Demo accounts:")
        print("   demo@resqnet.io / demo1234  (coordinator)")
        print("   field1@resqnet.io / demo1234  (field worker)")
        print("   field2@resqnet.io / demo1234  (field worker)")
        print("   hospital@resqnet.io / demo1234  (hospital)")


if __name__ == "__main__":
    asyncio.run(seed())
