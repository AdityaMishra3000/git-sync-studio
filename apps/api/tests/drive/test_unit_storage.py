from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.drive.storage import GoogleDriveStorage, LocalStorageAdapter


@pytest.mark.asyncio
async def test_local_storage_adapter_lifecycle(tmp_path: Path) -> None:
    storage = LocalStorageAdapter(root_dir=tmp_path / "storage")
    assert storage.provider_name() == "local_storage"
    assert storage.is_configured() is True

    raw_data = b"Arbitrary large binary dataset payload \x00\x01\x02\x03\xff\xfe"
    oid = hashlib.sha256(raw_data).hexdigest()

    assert await storage.exists(oid) is False

    # Upload
    storage_id = await storage.upload(oid, raw_data)
    assert storage_id == f"local_{oid}"
    assert await storage.exists(oid) is True
    assert await storage.exists(storage_id) is True

    # Check partitioned directory layout
    expected_path = tmp_path / "storage" / oid[:2] / oid
    assert expected_path.is_file()
    assert expected_path.read_bytes() == raw_data

    # Download
    downloaded = await storage.download(oid)
    assert downloaded == raw_data

    # Download stream
    streamed_chunks: list[bytes] = []
    async for chunk in storage.download_stream(oid, chunk_size=8):
        streamed_chunks.append(chunk)
    assert b"".join(streamed_chunks) == raw_data

    # Verify integrity
    assert await storage.verify(oid, oid) is True
    assert await storage.verify(oid, "f" * 64) is False

    # Idempotent upload
    re_uploaded_id = await storage.upload(oid, raw_data)
    assert re_uploaded_id == f"local_{oid}"


@pytest.mark.asyncio
async def test_local_storage_adapter_tampered_upload(tmp_path: Path) -> None:
    storage = LocalStorageAdapter(root_dir=tmp_path / "storage")
    fake_oid = "0" * 64
    real_data = b"Mismatching content"

    with pytest.raises(ValueError, match="Data integrity mismatch"):
        await storage.upload(fake_oid, real_data)

    # Ensure no leftover files
    assert await storage.exists(fake_oid) is False


@pytest.mark.asyncio
async def test_google_drive_storage_unconfigured_fallback(tmp_path: Path) -> None:
    fallback_adapter = LocalStorageAdapter(root_dir=tmp_path / "storage")
    drive_storage = GoogleDriveStorage(local_fallback=fallback_adapter)

    # Without live Google credentials, reports unconfigured
    assert drive_storage.is_configured() is False
    assert drive_storage.provider_name() == "local_storage"

    test_data = b"Drive fallback test blob"
    oid = hashlib.sha256(test_data).hexdigest()

    # Upload delegates safely to fallback
    storage_id = await drive_storage.upload(oid, test_data)
    assert await drive_storage.exists(oid) is True

    # Download succeeds from fallback
    downloaded = await drive_storage.download(storage_id)
    assert downloaded == test_data

    # Verification passes
    assert await drive_storage.verify(oid, oid) is True
