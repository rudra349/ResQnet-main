"""ResQNet — Evidence Upload API"""
from __future__ import annotations
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.engine import get_session
from app.db.models import Evidence, Incident
from app.aws.s3 import get_s3
from app.schemas.schemas import EvidenceOut

router = APIRouter(prefix="/evidence", tags=["evidence"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE_MB = 10


@router.post("/upload", response_model=EvidenceOut, status_code=201)
async def upload_evidence(
    incident_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    # Validate incident exists
    try:
        iid = uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(400, "Invalid incident_id")

    result = await session.execute(select(Incident).where(Incident.id == iid))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Incident not found")

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"File type not allowed: {file.content_type}")

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large (max {MAX_SIZE_MB}MB)")

    # Upload to S3 (or mock)
    s3 = get_s3()
    key = await s3.upload_file(file_bytes, file.filename, file.content_type)

    # Store metadata in CockroachDB
    evidence = Evidence(
        incident_id=iid,
        s3_key=key,
        file_type=file.content_type,
        original_filename=file.filename,
    )
    session.add(evidence)
    await session.flush()

    # Get presigned URL
    url = await s3.get_presigned_url(key)

    out = EvidenceOut.model_validate(evidence)
    out.url = url
    return out


@router.get("/{incident_id}", response_model=List[EvidenceOut])
async def list_evidence(incident_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Evidence).where(Evidence.incident_id == uuid.UUID(incident_id))
    )
    items = result.scalars().all()
    s3 = get_s3()
    output = []
    for ev in items:
        url = await s3.get_presigned_url(ev.s3_key)
        out = EvidenceOut.model_validate(ev)
        out.url = url
        output.append(out)
    return output
