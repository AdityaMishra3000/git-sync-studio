from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LargeObjectItem(BaseModel):
    id: UUID
    repository_id: UUID
    oid: str
    size_bytes: int
    path: str
    drive_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LargeObjectListResponse(BaseModel):
    objects: list[LargeObjectItem]
    total_count: int
    total_size_bytes: int
    unique_blobs: int
    dedup_savings_bytes: int


class UploadResponse(BaseModel):
    status: str
    oid: str
    size_bytes: int
    path: str
    reused: bool
    pointer: str
    storage_id: str


class VerifyResponse(BaseModel):
    oid: str
    valid: bool
    size_bytes: int
    provider: str
    message: str


class DriveStatusResponse(BaseModel):
    provider: str
    configured: bool
    live_drive_active: bool
    storage_root: str
    total_objects: int
    total_size_bytes: int
    unique_blobs: int
    dedup_savings_bytes: int
