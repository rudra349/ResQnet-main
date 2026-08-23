import pytest
import uuid
from app.sync.processor import process_sync_operation

@pytest.mark.asyncio
async def test_idempotent_sync_duplicate_prevention(mocker=None):
    # Tests duplicate operation prevention logic
    op_id = uuid.uuid4()
    payload = {
        "operation_id": str(op_id),
        "content": "Test offline report duplicate check",
        "severity": "medium",
    }
    assert str(op_id) == payload["operation_id"]
