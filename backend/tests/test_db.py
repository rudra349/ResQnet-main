import pytest
import uuid
from app.db.models import Incident, Report, Memory, MemoryType, IncidentSeverity

@pytest.mark.asyncio
async def test_incident_model_instantiation():
    inc = Incident(
        type="flood",
        description="Test flood in Sector 1",
        severity=IncidentSeverity.high,
    )
    assert inc.type == "flood"
    assert inc.severity == IncidentSeverity.high
    assert isinstance(inc.id, uuid.UUID)

@pytest.mark.asyncio
async def test_memory_model_instantiation():
    mem = Memory(
        memory_type=MemoryType.episodic,
        content="Truck 17 delivered supplies to Shelter Alpha",
        confidence=0.95,
    )
    assert mem.memory_type == MemoryType.episodic
    assert mem.confidence == 0.95
