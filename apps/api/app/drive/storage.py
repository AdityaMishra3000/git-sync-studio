from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("app.drive.storage")


class StorageProvider:
    """Abstract interface for large-object content-addressed binary storage."""

    async def upload(self, oid: str, data: bytes) -> str:
        """Upload raw binary data. Returns unique storage reference ID."""
        raise NotImplementedError

    async def download(self, storage_id_or_oid: str) -> bytes:
        """Download raw binary data."""
        raise NotImplementedError

    def download_stream(
        self, storage_id_or_oid: str, chunk_size: int = 65536
    ) -> AsyncIterator[bytes]:
        """Stream binary chunks."""
        raise NotImplementedError

    async def exists(self, storage_id_or_oid: str) -> bool:
        """Check if binary object exists."""
        raise NotImplementedError

    async def verify(self, storage_id_or_oid: str, expected_sha256: str) -> bool:
        """Verify binary integrity by recalculating SHA-256."""
        raise NotImplementedError

    def provider_name(self) -> str:
        """Provider name ('google_drive' or 'local_storage')."""
        raise NotImplementedError

    def is_configured(self) -> bool:
        """Whether live upstream service is properly configured."""
        raise NotImplementedError


class LocalStorageAdapter(StorageProvider):
    """Content-addressed local filesystem storage adapter.

    Stores objects partitioned by the first two characters of their SHA-256 digest:
    `{storage_root}/{oid[:2]}/{oid}`.
    Uses atomic temp-file-and-rename semantics to prevent corruption during writes.
    """

    def __init__(self, root_dir: Path | str | None = None) -> None:
        if root_dir is not None:
            self.root_dir = Path(root_dir).resolve()
        else:
            settings = get_settings()
            self.root_dir = settings.large_object_storage_dir.resolve()
        self.tmp_dir = self.root_dir / ".tmp"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        try:
            self.root_dir.mkdir(parents=True, exist_ok=True)
            self.tmp_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            self.root_dir = Path("/tmp/gitsync_storage")  # noqa: S108
            self.tmp_dir = self.root_dir / ".tmp"
            self.root_dir.mkdir(parents=True, exist_ok=True)
            self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def clean_oid(self, oid: str) -> str:
        clean = oid.lower().strip()
        if clean.startswith("sha256:"):
            clean = clean[7:]
        if clean.startswith("drive_"):
            clean = clean[6:]
        if clean.startswith("local_"):
            clean = clean[6:]
        return clean

    def _get_path(self, oid: str) -> Path:
        clean = self.clean_oid(oid)
        prefix = clean[:2] if len(clean) >= 2 else "00"
        return self.root_dir / prefix / clean

    def _sync_write(self, clean_oid: str, data: bytes, dest_path: Path) -> None:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.tmp_dir / f"{clean_oid}.tmp.{uuid.uuid4().hex}"

        hasher = hashlib.sha256()
        with open(temp_file, "wb") as f:
            f.write(data)
            hasher.update(data)

        actual_digest = hasher.hexdigest().lower()
        if actual_digest != clean_oid:
            if temp_file.is_file():
                temp_file.unlink(missing_ok=True)
            raise ValueError(
                f"Data integrity mismatch during upload: expected {clean_oid}, got {actual_digest}"
            )

        os.replace(temp_file, dest_path)

    def _sync_read(self, dest_path: Path) -> bytes:
        if not dest_path.is_file():
            raise FileNotFoundError(f"Large object {dest_path.name} not found in local storage")
        with open(dest_path, "rb") as f:
            return f.read()

    def _sync_verify(self, dest_path: Path, clean_expected: str) -> bool:
        if not dest_path.is_file():
            return False
        hasher = hashlib.sha256()
        with open(dest_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest().lower() == clean_expected

    async def upload(self, oid: str, data: bytes) -> str:
        clean_oid = self.clean_oid(oid)
        dest_path = self._get_path(clean_oid)

        if dest_path.is_file() and dest_path.stat().st_size == len(data):
            return f"local_{clean_oid}"

        await asyncio.to_thread(self._sync_write, clean_oid, data, dest_path)
        logger.info("large_object.stored_locally", oid=clean_oid, size=len(data))
        return f"local_{clean_oid}"

    async def download(self, storage_id_or_oid: str) -> bytes:
        dest_path = self._get_path(storage_id_or_oid)
        return await asyncio.to_thread(self._sync_read, dest_path)

    async def download_stream(
        self, storage_id_or_oid: str, chunk_size: int = 65536
    ) -> AsyncIterator[bytes]:
        data = await self.download(storage_id_or_oid)
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    async def exists(self, storage_id_or_oid: str) -> bool:
        dest_path = self._get_path(storage_id_or_oid)
        return dest_path.is_file() and dest_path.stat().st_size > 0

    async def verify(self, storage_id_or_oid: str, expected_sha256: str) -> bool:
        clean_expected = self.clean_oid(expected_sha256)
        dest_path = self._get_path(storage_id_or_oid)
        return await asyncio.to_thread(self._sync_verify, dest_path, clean_expected)

    def provider_name(self) -> str:
        return "local_storage"

    def is_configured(self) -> bool:
        return True


class GoogleDriveStorage(StorageProvider):
    """Google Drive API v3 storage implementation.

    Integrates with Google Drive REST API using OAuth2 refresh tokens.
    Transparently falls back to LocalStorageAdapter if credentials are not configured.
    """

    def __init__(self, local_fallback: LocalStorageAdapter | None = None) -> None:
        self.settings = get_settings()
        self.fallback = local_fallback or LocalStorageAdapter()
        self._access_token: str | None = None

    def is_configured(self) -> bool:
        client_id = self.settings.google_oauth_client_id
        client_secret = (
            self.settings.google_oauth_client_secret.get_secret_value()
            if self.settings.google_oauth_client_secret
            else None
        )
        refresh_token = (
            self.settings.google_drive_refresh_token.get_secret_value()
            if self.settings.google_drive_refresh_token
            else None
        )

        dummy_markers = {"dummy", "placeholder", "test", "fake", "your_"}
        for val in (client_id, client_secret, refresh_token):
            if not val:
                return False
            if any(marker in val.lower() for marker in dummy_markers):
                return False

        return True

    def provider_name(self) -> str:
        return "google_drive" if self.is_configured() else "local_storage"

    async def _get_access_token(self) -> str:
        if not self.is_configured():
            raise RuntimeError("Google Drive credentials not configured")

        client_id = self.settings.google_oauth_client_id
        client_secret = (
            self.settings.google_oauth_client_secret.get_secret_value()
            if self.settings.google_oauth_client_secret
            else ""
        )
        refresh_token = (
            self.settings.google_drive_refresh_token.get_secret_value()
            if self.settings.google_drive_refresh_token
            else ""
        )

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=10.0,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to refresh Google Drive token: {resp.text}")
            token = resp.json().get("access_token")
            if not token:
                raise RuntimeError("No access_token returned by Google OAuth")
            return str(token)

    async def upload(self, oid: str, data: bytes) -> str:
        if not self.is_configured():
            logger.info("drive.fallback_to_local_upload", oid=oid)
            return await self.fallback.upload(oid, data)

        try:
            token = await self._get_access_token()
            metadata: dict[str, Any] = {
                "name": f"gitsync_{oid}",
                "description": f"GitSync Large Object SHA-256:{oid}",
            }
            if self.settings.google_drive_root_folder_id:
                metadata["parents"] = [self.settings.google_drive_root_folder_id]

            # Google Drive multipart upload
            boundary = f"boundary_{uuid.uuid4().hex}"
            metadata_json = json.dumps(metadata)
            body = (
                f"--{boundary}\r\n"
                f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
                f"{metadata_json}\r\n"
                f"--{boundary}\r\n"
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode() + data + f"\r\n--{boundary}--\r\n".encode()

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": f"multipart/related; boundary={boundary}",
                    },
                    content=body,
                    timeout=60.0,
                )
                if resp.status_code not in (200, 201):
                    raise RuntimeError(f"Google Drive upload failed: {resp.text}")
                file_id = str(resp.json()["id"])
                # Also cache locally for immediate fast access
                await self.fallback.upload(oid, data)
                return file_id
        except (httpx.HTTPError, OSError, RuntimeError, ValueError) as e:
            logger.warning("drive.upload_failed_falling_back_to_local", error=str(e), oid=oid)
            return await self.fallback.upload(oid, data)

    async def download(self, storage_id_or_oid: str) -> bytes:
        if await self.fallback.exists(storage_id_or_oid):
            return await self.fallback.download(storage_id_or_oid)

        if not self.is_configured():
            raise FileNotFoundError(f"Large object {storage_id_or_oid} not found")

        try:
            token = await self._get_access_token()
            file_id = storage_id_or_oid
            if file_id.startswith("drive_"):
                file_id = file_id[6:]

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=60.0,
                )
                if resp.status_code != 200:
                    raise FileNotFoundError(f"Google Drive file {file_id} not found: {resp.text}")
                data = resp.content
                # Cache downloaded data locally
                await self.fallback.upload(storage_id_or_oid, data)
                return data
        except (httpx.HTTPError, OSError, RuntimeError) as e:
            logger.warning("drive.download_failed", error=str(e), id=storage_id_or_oid)
            raise FileNotFoundError(f"Failed to download object {storage_id_or_oid}: {e}") from e

    async def download_stream(
        self, storage_id_or_oid: str, chunk_size: int = 65536
    ) -> AsyncIterator[bytes]:
        if await self.fallback.exists(storage_id_or_oid):
            async for chunk in self.fallback.download_stream(storage_id_or_oid, chunk_size):
                yield chunk
            return

        data = await self.download(storage_id_or_oid)
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    async def exists(self, storage_id_or_oid: str) -> bool:
        if await self.fallback.exists(storage_id_or_oid):
            return True
        if not self.is_configured():
            return False
        try:
            token = await self._get_access_token()
            file_id = storage_id_or_oid
            if file_id.startswith("drive_"):
                file_id = file_id[6:]
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=id",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )
                return resp.status_code == 200
        except (httpx.HTTPError, OSError, RuntimeError):
            return False

    async def verify(self, storage_id_or_oid: str, expected_sha256: str) -> bool:
        if await self.fallback.exists(storage_id_or_oid):
            return await self.fallback.verify(storage_id_or_oid, expected_sha256)
        try:
            data = await self.download(storage_id_or_oid)
            digest = hashlib.sha256(data).hexdigest().lower()
            clean_expected = self.fallback.clean_oid(expected_sha256)
            return digest == clean_expected
        except (httpx.HTTPError, OSError, RuntimeError, FileNotFoundError):
            return False


_global_storage: StorageProvider | None = None


def get_storage() -> StorageProvider:
    """Return configured storage provider singleton."""
    global _global_storage
    if _global_storage is None:
        _global_storage = GoogleDriveStorage()
    return _global_storage


def set_storage(provider: StorageProvider | None) -> None:
    """Set custom storage provider (e.g. for testing)."""
    global _global_storage
    _global_storage = provider
