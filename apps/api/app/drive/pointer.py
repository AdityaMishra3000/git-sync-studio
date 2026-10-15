from __future__ import annotations

import re

POINTER_VERSION = "https://gitsync.studio/spec/v1"
COMPAT_VERSION = "gitsync-studio/v1"

OID_REGEX = re.compile(r"^sha256:([a-fA-F0-9]{64})$")


def create_pointer(oid: str, size_bytes: int) -> str:
    """Create a deterministic GitSync Studio large-file pointer text."""
    clean_oid = oid.lower().strip()
    if clean_oid.startswith("sha256:"):
        clean_oid = clean_oid[7:]
    if len(clean_oid) != 64 or not all(c in "0123456789abcdef" for c in clean_oid):
        raise ValueError(f"Invalid SHA-256 hex digest: {oid}")

    return f"version {POINTER_VERSION}\noid sha256:{clean_oid}\nsize {size_bytes}\n"


def parse_pointer(content: str | bytes) -> dict[str, str | int] | None:
    """Parse and strictly validate a large-file pointer file.

    Returns dict with keys ('version', 'oid', 'size_bytes') or None if invalid.
    """
    if isinstance(content, bytes):
        try:
            # Pointers are small ASCII/UTF-8 text (< 500 bytes)
            if len(content) > 1024:
                return None
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return None
    else:
        text = content

    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) < 3:
        return None

    data: dict[str, str] = {}
    for line in lines:
        parts = line.split(" ", 1)
        if len(parts) == 2:
            data[parts[0]] = parts[1]

    version = data.get("version")
    if version not in {POINTER_VERSION, COMPAT_VERSION}:
        return None

    raw_oid = data.get("oid")
    if not raw_oid:
        return None

    match = OID_REGEX.match(raw_oid)
    if not match:
        return None
    oid = match.group(1).lower()

    raw_size = data.get("size")
    if raw_size is None or not raw_size.isdigit():
        return None
    size_bytes = int(raw_size)
    if size_bytes < 0:
        return None

    return {
        "version": version,
        "oid": oid,
        "size_bytes": size_bytes,
    }


def is_pointer(content: str | bytes) -> bool:
    """Check if content represents a valid GitSync pointer."""
    return parse_pointer(content) is not None
