from __future__ import annotations

import hashlib
import io
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.db.models import DriveObject, LargeObject
from app.drive.pointer import create_pointer, parse_pointer
from app.drive.schemas import (
    DriveStatusResponse,
    UploadResponse,
    VerifyResponse,
)
from app.drive.storage import get_storage

router = APIRouter(prefix="/drive", tags=["drive"])


@router.post("/upload", response_model=UploadResponse)
async def upload_large_file(
    repo_id: UUID = Form(...),
    path: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> UploadResponse:
    """Upload a binary file, compute SHA-256 OID, deduplicate, and persist to storage."""
    data = await file.read()
    size = len(data)
    oid = hashlib.sha256(data).hexdigest().lower()
    storage = get_storage()

    # Deduplication check: does an object with this exact SHA-256 already exist?
    existing_stmt = select(LargeObject).where(LargeObject.oid == oid)
    existing_result = await session.execute(existing_stmt)
    existing_blob = existing_result.scalars().first()

    if existing_blob:
        # Check if already mapped for this specific repo and path
        specific_stmt = select(LargeObject).where(
            LargeObject.repository_id == repo_id,
            LargeObject.path == path,
            LargeObject.oid == oid,
        )
        specific_result = await session.execute(specific_stmt)
        specific_obj = specific_result.scalars().first()

        drive_stmt = select(DriveObject).where(DriveObject.checksum == oid)
        drive_result = await session.execute(drive_stmt)
        drive_obj = drive_result.scalars().first()
        storage_id = drive_obj.drive_file_id if drive_obj else f"local_{oid}"

        if not specific_obj:
            # Map this repository/path to the existing deduplicated blob
            new_mapping = LargeObject(
                repository_id=repo_id,
                oid=oid,
                size_bytes=size,
                path=path,
            )
            session.add(new_mapping)
            await session.commit()
            await session.refresh(new_mapping)

            new_drive_obj = DriveObject(
                large_object_id=new_mapping.id,
                drive_file_id=storage_id,
                checksum=oid,
                drive_version="1",
            )
            session.add(new_drive_obj)
            await session.commit()

        return UploadResponse(
            status="ok",
            oid=oid,
            size_bytes=size,
            path=path,
            reused=True,
            pointer=create_pointer(oid, size),
            storage_id=storage_id,
        )

    # New unique object: write to storage
    storage_id = await storage.upload(oid, data)

    new_obj = LargeObject(
        repository_id=repo_id,
        oid=oid,
        size_bytes=size,
        path=path,
    )
    session.add(new_obj)
    await session.commit()
    await session.refresh(new_obj)

    drive_obj = DriveObject(
        large_object_id=new_obj.id,
        drive_file_id=storage_id,
        checksum=oid,
        drive_version="1",
    )
    session.add(drive_obj)
    await session.commit()

    return UploadResponse(
        status="ok",
        oid=oid,
        size_bytes=size,
        path=path,
        reused=False,
        pointer=create_pointer(oid, size),
        storage_id=storage_id,
    )


@router.get("/download/{oid}")
async def download_large_file(
    oid: str,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Download a binary blob by its SHA-256 OID with integrity validation."""
    clean_oid = oid.lower().strip()
    if clean_oid.startswith("sha256:"):
        clean_oid = clean_oid[7:]

    storage = get_storage()
    if not await storage.exists(clean_oid):
        # Look up in DB for drive_file_id
        stmt = (
            select(DriveObject.drive_file_id)
            .join(LargeObject, LargeObject.id == DriveObject.large_object_id)
            .where(LargeObject.oid == clean_oid)
        )
        res = await session.execute(stmt)
        drive_file_id = res.scalar_one_or_none()
        if not drive_file_id or not await storage.exists(drive_file_id):
            raise HTTPException(status_code=404, detail=f"Large object {clean_oid} not found")
        target_id = drive_file_id
    else:
        target_id = clean_oid

    # Fetch filename metadata from DB if available
    obj_stmt = select(LargeObject.path).where(LargeObject.oid == clean_oid).limit(1)
    obj_res = await session.execute(obj_stmt)
    sample = obj_res.scalar_one_or_none()
    sample_path = sample.path if isinstance(sample, LargeObject) else sample
    filename = str(sample_path).rsplit("/", 1)[-1] if sample_path else f"{clean_oid}.bin"

    try:
        data = await storage.download(target_id)
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Object {clean_oid} not found: {err}") from err

    # Strictly verify integrity before dispatching to client
    calculated_digest = hashlib.sha256(data).hexdigest().lower()
    if calculated_digest != clean_oid:
        raise HTTPException(
            status_code=500,
            detail=f"Integrity check failed: expected {clean_oid}, got {calculated_digest}",
        )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(len(data)),
        "X-OID-SHA256": clean_oid,
    }
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/octet-stream",
        headers=headers,
    )


@router.get("", response_model=list[dict[str, Any]])
async def list_large_objects(
    session: AsyncSession = Depends(get_db_session),
) -> list[dict[str, Any]]:
    """List all tracked large objects with storage sync status."""
    stmt = select(LargeObject).order_by(LargeObject.created_at.desc())
    result = await session.execute(stmt)
    objects = result.scalars().all()

    storage = get_storage()
    out: list[dict[str, Any]] = []

    for obj in objects:
        drive_res = await session.execute(
            select(DriveObject).where(
                (DriveObject.large_object_id == obj.id) | (DriveObject.checksum == obj.oid)
            )
        )
        drive = drive_res.scalar_one_or_none()

        status = "pending"
        if drive:
            if storage.is_configured() and storage.provider_name() == "google_drive":
                status = "synced"
            else:
                status = "local_storage"

        out.append(
            {
                "id": str(obj.id),
                "repository_id": str(obj.repository_id),
                "oid": obj.oid,
                "size_bytes": obj.size_bytes,
                "path": obj.path,
                "drive_status": status,
                "created_at": obj.created_at.isoformat(),
            }
        )
    return out


@router.get("/status", response_model=DriveStatusResponse)
async def get_drive_status(
    session: AsyncSession = Depends(get_db_session),
) -> DriveStatusResponse:
    """Return storage provider status and deduplication statistics."""
    storage = get_storage()

    total_objs_stmt = select(func.count(LargeObject.id))
    total_objs_res = await session.execute(total_objs_stmt)
    total_objects = total_objs_res.scalar() or 0

    total_size_stmt = select(func.coalesce(func.sum(LargeObject.size_bytes), 0))
    total_size_res = await session.execute(total_size_stmt)
    total_size_bytes = int(total_size_res.scalar() or 0)

    # Unique blobs by OID
    unique_stmt = select(
        LargeObject.oid, func.max(LargeObject.size_bytes)
    ).group_by(LargeObject.oid)
    unique_res = await session.execute(unique_stmt)
    unique_rows = unique_res.all()
    unique_blobs = len(unique_rows)
    unique_size_bytes = sum(int(r[1]) for r in unique_rows)

    dedup_savings_bytes = max(0, total_size_bytes - unique_size_bytes)

    storage_root = (
        str(getattr(storage, "root_dir", ""))
        if hasattr(storage, "root_dir")
        else str(getattr(getattr(storage, "fallback", None), "root_dir", "cloud:google-drive"))
    )

    return DriveStatusResponse(
        provider=storage.provider_name(),
        configured=storage.is_configured(),
        live_drive_active=storage.is_configured() and storage.provider_name() == "google_drive",
        storage_root=storage_root,
        total_objects=total_objects,
        total_size_bytes=total_size_bytes,
        unique_blobs=unique_blobs,
        dedup_savings_bytes=dedup_savings_bytes,
    )


@router.post("/verify/{oid}", response_model=VerifyResponse)
async def verify_large_object(
    oid: str,
    session: AsyncSession = Depends(get_db_session),
) -> VerifyResponse:
    """Verify integrity of a stored large object against its SHA-256 digest."""
    clean_oid = oid.lower().strip()
    if clean_oid.startswith("sha256:"):
        clean_oid = clean_oid[7:]

    stmt = select(LargeObject).where(LargeObject.oid == clean_oid).limit(1)
    res = await session.execute(stmt)
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Object {clean_oid} not found in database")

    storage = get_storage()
    is_valid = await storage.verify(clean_oid, clean_oid)

    return VerifyResponse(
        oid=clean_oid,
        valid=is_valid,
        size_bytes=obj.size_bytes,
        provider=storage.provider_name(),
        message="Integrity check passed (SHA-256 bit-for-bit match)"
        if is_valid
        else "Storage object missing or checksum mismatch",
    )


@router.get("/pointer/{oid}")
async def get_pointer_for_oid(
    oid: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Retrieve the deterministic Git pointer text for a tracked large object."""
    clean_oid = oid.lower().strip()
    if clean_oid.startswith("sha256:"):
        clean_oid = clean_oid[7:]

    stmt = select(LargeObject).where(LargeObject.oid == clean_oid).limit(1)
    res = await session.execute(stmt)
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Object {clean_oid} not found")

    pointer_text = create_pointer(clean_oid, obj.size_bytes)
    return {
        "oid": clean_oid,
        "size_bytes": obj.size_bytes,
        "pointer": pointer_text,
    }


@router.post("/pointer/parse")
async def parse_pointer_endpoint(
    content: str = Form(...),
) -> dict[str, Any]:
    """Parse and validate a pointer file text."""
    parsed = parse_pointer(content)
    if not parsed:
        raise HTTPException(status_code=400, detail="Invalid pointer content")
    return parsed
