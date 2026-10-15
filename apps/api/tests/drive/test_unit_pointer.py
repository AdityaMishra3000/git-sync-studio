from __future__ import annotations

import hashlib

import pytest

from app.drive.pointer import POINTER_VERSION, create_pointer, is_pointer, parse_pointer


def test_create_pointer_deterministic() -> None:
    raw_bytes = b"Hello, GitSync Large Binary Object Test!"
    oid = hashlib.sha256(raw_bytes).hexdigest()
    size = len(raw_bytes)

    ptr1 = create_pointer(oid, size)
    ptr2 = create_pointer(f"sha256:{oid}", size)

    assert ptr1 == ptr2
    assert ptr1.startswith(f"version {POINTER_VERSION}\n")
    assert f"oid sha256:{oid}\n" in ptr1
    assert f"size {size}\n" in ptr1
    assert ptr1.endswith("\n")


def test_create_pointer_invalid_oid() -> None:
    with pytest.raises(ValueError, match="Invalid SHA-256"):
        create_pointer("not_a_valid_sha256_hex", 100)

    with pytest.raises(ValueError, match="Invalid SHA-256"):
        create_pointer("a" * 63, 100)  # 63 chars instead of 64


def test_parse_pointer_valid_string_and_bytes() -> None:
    raw_bytes = b"Sample dataset binary blob"
    oid = hashlib.sha256(raw_bytes).hexdigest()
    size = len(raw_bytes)

    pointer_text = create_pointer(oid, size)
    parsed_from_str = parse_pointer(pointer_text)
    assert parsed_from_str is not None
    assert parsed_from_str["version"] == POINTER_VERSION
    assert parsed_from_str["oid"] == oid
    assert parsed_from_str["size_bytes"] == size

    parsed_from_bytes = parse_pointer(pointer_text.encode("utf-8"))
    assert parsed_from_bytes is not None
    assert parsed_from_bytes["oid"] == oid
    assert parsed_from_bytes["size_bytes"] == size


def test_parse_pointer_compat_version_and_crlf() -> None:
    oid = "a" * 64
    crlf_content = f"version gitsync-studio/v1\r\noid sha256:{oid}\r\nsize 2048\r\n"
    parsed = parse_pointer(crlf_content)
    assert parsed is not None
    assert parsed["version"] == "gitsync-studio/v1"
    assert parsed["oid"] == oid
    assert parsed["size_bytes"] == 2048


def test_parse_pointer_invalid_inputs() -> None:
    # Binary random data
    assert parse_pointer(b"\x00\x01\x02\x03\xff\xfe\xfd") is None
    # Empty string
    assert parse_pointer("") is None
    # Regular markdown or source code
    assert parse_pointer("# My Project Readme\nThis is a test.") is None
    # Missing size
    assert parse_pointer(f"version {POINTER_VERSION}\noid sha256:{'0'*64}\n") is None
    # Negative size
    assert parse_pointer(f"version {POINTER_VERSION}\noid sha256:{'0'*64}\nsize -10\n") is None
    # Bad version
    assert parse_pointer(f"version invalid/v9\noid sha256:{'0'*64}\nsize 100\n") is None


def test_is_pointer() -> None:
    oid = "b" * 64
    valid_ptr = create_pointer(oid, 500)
    assert is_pointer(valid_ptr) is True
    assert is_pointer(valid_ptr.encode("utf-8")) is True

    # Real binaries or non-pointers
    assert is_pointer(b"PNG\r\n\x1a\n...") is False
    assert is_pointer("just regular text") is False
    assert is_pointer(b"") is False
