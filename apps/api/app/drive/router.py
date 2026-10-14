import hashlib
import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.db.models import DriveObject, LargeObject

router = APIRouter(prefix="/drive", tags=["drive"])


@router.post("/upload")
async def upload_large_file(
    repo_id: UUID = Form(...),
    path: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    data = await file.read()
    oid = hashlib.sha256(data).hexdigest()

    result = await session.execute(select(LargeObject).where(LargeObject.oid == oid))
    existing = result.scalar_one_or_none()
    if existing:
        return {"status": "ok", "oid": oid, "reused": True}

    cache_dir = os.path.expanduser("~/.gitsync/drive_mock")  # noqa: ASYNC240
    os.makedirs(cache_dir, exist_ok=True)

    with open(os.path.join(cache_dir, oid), "wb") as f:  # noqa: ASYNC230
        f.write(data)

    obj = LargeObject(repository_id=repo_id, oid=oid, size_bytes=len(data), path=path)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    drive_obj = DriveObject(large_object_id=obj.id, drive_file_id=f"drive_{oid}", checksum=oid)
    session.add(drive_obj)
    await session.commit()

    return {"status": "ok", "oid": oid, "reused": False}

@router.get("")
async def list_large_objects(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    from sqlalchemy import select
    from app.db.models import LargeObject, DriveObject
    result = await session.execute(select(LargeObject))
    objects = result.scalars().all()
    
    out = []
    for obj in objects:
        drive_res = await session.execute(select(DriveObject).where(DriveObject.large_object_id == obj.id))
        drive = drive_res.scalar_one_or_none()
        out.append({
            "id": str(obj.id),
            "repository_id": str(obj.repository_id),
            "oid": obj.oid,
            "size_bytes": obj.size_bytes,
            "path": obj.path,
            "drive_status": "synced" if drive else "pending",
            "created_at": obj.created_at.isoformat(),
        })
    return out
