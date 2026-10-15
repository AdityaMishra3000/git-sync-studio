from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from celery.utils.log import get_task_logger

from app.core.config import get_settings
from app.db.models import DriveObject, LargeObject
from app.db.session import create_db_engine, create_session_factory
from app.drive.storage import get_storage
from app.jobs.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="tasks.drive.verify_storage_object")
def verify_storage_object(self: Any, oid: str) -> dict[str, Any]:
    """Celery background task to verify storage integrity of a large object."""
    return asyncio.run(_verify_storage_object(oid))


async def _verify_storage_object(oid: str) -> dict[str, Any]:
    storage = get_storage()
    clean_oid = oid.lower().strip()
    if clean_oid.startswith("sha256:"):
        clean_oid = clean_oid[7:]

    valid = await storage.verify(clean_oid, clean_oid)
    logger.info("drive.integrity_verified", oid=clean_oid, valid=valid)
    return {"oid": clean_oid, "valid": valid, "provider": storage.provider_name()}


@celery_app.task(bind=True, name="tasks.drive.sync_object_to_drive")
def sync_object_to_drive(self: Any, large_object_id: str) -> dict[str, Any]:
    """Celery background task to sync local large object to Google Drive."""
    return asyncio.run(_sync_object_to_drive(large_object_id))


async def _sync_object_to_drive(large_object_id: str) -> dict[str, Any]:
    settings = get_settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        obj_uuid = UUID(large_object_id)
        obj = await session.get(LargeObject, obj_uuid)
        if not obj:
            return {"status": "error", "detail": "object_not_found"}

        storage = get_storage()
        if not storage.is_configured():
            return {
                "status": "local_fallback",
                "detail": "Google Drive credentials not configured; preserved in local storage",
            }

        try:
            data = await storage.download(obj.oid)
            drive_file_id = await storage.upload(obj.oid, data)

            drive_obj = DriveObject(
                large_object_id=obj.id,
                drive_file_id=drive_file_id,
                checksum=obj.oid,
                drive_version="1",
            )
            session.add(drive_obj)
            await session.commit()
            return {"status": "success", "drive_file_id": drive_file_id}
        except (OSError, RuntimeError, ValueError) as e:
            logger.warning("drive.sync_task_failed", error=str(e), oid=obj.oid)
            return {"status": "failed", "error": str(e)}
        finally:
            await engine.dispose()
