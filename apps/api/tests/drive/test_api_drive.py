from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.dependencies import get_db_session
from app.db.models import DriveObject, LargeObject
from app.drive.pointer import is_pointer, parse_pointer
from app.drive.storage import LocalStorageAdapter, set_storage


class FakeScalarResult:
    def __init__(self, items: Sequence[Any]) -> None:
        self.items = list(items)

    def scalars(self) -> FakeScalarResult:
        return self

    def all(self) -> list[Any]:
        return self.items

    def first(self) -> Any | None:
        return self.items[0] if self.items else None

    def scalar_one_or_none(self) -> Any | None:
        return self.items[0] if self.items else None

    def scalar(self) -> Any | None:
        return self.items[0] if self.items else None


@pytest.fixture
def drive_env(app: FastAPI, tmp_path: Path) -> Iterator[dict[str, list[object]]]:
    storage = LocalStorageAdapter(root_dir=tmp_path / "storage")
    set_storage(storage)

    db_state: dict[str, list[object]] = {
        "large_objects": [],
        "drive_objects": [],
    }

    mock_session = AsyncMock()

    async def fake_execute(statement: object) -> FakeScalarResult:
        sql_str = str(statement)
        params: dict[str, object] = {}
        if hasattr(statement, "compile"):
            try:
                comp = statement.compile()
                params = comp.params or {}
            except (ValueError, TypeError, AttributeError):
                params = {}

        if "FROM large_objects" in sql_str:
            objs = list(db_state["large_objects"])
            target_oid = params.get("oid_1") or params.get("oid")
            if target_oid:
                filtered_lo: list[Any] = [
                    lo for lo in objs if isinstance(lo, LargeObject) and lo.oid == target_oid
                ]
                return FakeScalarResult(filtered_lo)
            if "count(" in sql_str.lower():
                return FakeScalarResult([len(objs)])
            if "sum(" in sql_str.lower():
                total = sum(lo.size_bytes for lo in objs if isinstance(lo, LargeObject))
                return FakeScalarResult([total])
            if "group by" in sql_str.lower():
                rows = [(lo.oid, lo.size_bytes) for lo in objs if isinstance(lo, LargeObject)]
                return FakeScalarResult(rows)
            return FakeScalarResult(objs)

        if "FROM drive_objects" in sql_str:
            drives = list(db_state["drive_objects"])
            target_oid = params.get("checksum_1") or params.get("checksum") or params.get("oid_1")
            if target_oid:
                filtered_drives: list[Any] = [
                    d for d in drives if isinstance(d, DriveObject) and d.checksum == target_oid
                ]
                return FakeScalarResult(filtered_drives)
            return FakeScalarResult(drives)

        return FakeScalarResult([])

    def fake_add(instance: object) -> None:
        if isinstance(instance, LargeObject):
            if not instance.id:
                instance.id = uuid.uuid4()
            if not instance.created_at:
                instance.created_at = datetime.now(UTC)
            db_state["large_objects"].append(instance)
        elif isinstance(instance, DriveObject):
            if not instance.id:
                instance.id = uuid.uuid4()
            if not instance.created_at:
                instance.created_at = datetime.now(UTC)
            db_state["drive_objects"].append(instance)

    async def fake_refresh(instance: Any) -> None:
        if not getattr(instance, "id", None):
            instance.id = uuid.uuid4()

    mock_session.execute.side_effect = fake_execute
    mock_session.add = MagicMock(side_effect=fake_add)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=fake_refresh)

    async def _mock_db_session() -> AsyncIterator[AsyncMock]:
        yield mock_session

    app.dependency_overrides[get_db_session] = _mock_db_session
    yield db_state
    app.dependency_overrides.pop(get_db_session, None)
    set_storage(None)


@pytest.mark.asyncio
async def test_drive_upload_flow_and_pointer_generation(
    client: AsyncClient, drive_env: dict[str, list[object]]
) -> None:
    repo_id = str(uuid.uuid4())
    raw_payload = b"GitSync Test Binary Content 1234567890"
    expected_oid = hashlib.sha256(raw_payload).hexdigest()

    response = await client.post(
        "/api/v1/drive/upload",
        data={"repo_id": repo_id, "path": "models/weights.bin"},
        files={"file": ("weights.bin", raw_payload, "application/octet-stream")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["oid"] == expected_oid
    assert data["size_bytes"] == len(raw_payload)
    assert data["reused"] is False
    assert is_pointer(data["pointer"]) is True

    parsed_ptr = parse_pointer(data["pointer"])
    assert parsed_ptr is not None
    assert parsed_ptr["oid"] == expected_oid
    assert parsed_ptr["size_bytes"] == len(raw_payload)

    # Deduplication test: uploading same binary
    dup_response = await client.post(
        "/api/v1/drive/upload",
        data={"repo_id": repo_id, "path": "backup/weights.bin"},
        files={"file": ("weights.bin", raw_payload, "application/octet-stream")},
    )

    assert dup_response.status_code == 200
    dup_data = dup_response.json()
    assert dup_data["status"] == "ok"
    assert dup_data["oid"] == expected_oid
    assert dup_data["reused"] is True


@pytest.mark.asyncio
async def test_drive_download_and_integrity(
    client: AsyncClient, drive_env: dict[str, list[object]]
) -> None:
    repo_id = str(uuid.uuid4())
    raw_payload = b"Streaming download test content \x00\xff"
    oid = hashlib.sha256(raw_payload).hexdigest()

    # Upload first
    up_res = await client.post(
        "/api/v1/drive/upload",
        data={"repo_id": repo_id, "path": "data.bin"},
        files={"file": ("data.bin", raw_payload, "application/octet-stream")},
    )
    assert up_res.status_code == 200

    # Download by OID
    dl_res = await client.get(f"/api/v1/drive/download/{oid}")
    assert dl_res.status_code == 200
    assert dl_res.content == raw_payload
    assert dl_res.headers["x-oid-sha256"] == oid

    # Verify endpoint
    verify_res = await client.post(f"/api/v1/drive/verify/{oid}")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["valid"] is True
    assert verify_data["oid"] == oid


@pytest.mark.asyncio
async def test_drive_status_and_list_endpoints(
    client: AsyncClient, drive_env: dict[str, list[object]]
) -> None:
    status_res = await client.get("/api/v1/drive/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["provider"] == "local_storage"
    assert "storage_root" in status_data

    list_res = await client.get("/api/v1/drive")
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)
