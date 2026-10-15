#!/usr/bin/env python3
"""End-to-end verification script for GitSync Studio Large-File Pointer feature.

Tests the complete lifecycle:
1. Initializes a disposable Git repository.
2. Configures GitSync filter via `gitsync init` and `gitsync track`.
3. Creates a binary file.
4. Stages and commits: verifies Git clean filter emits deterministic pointer into Git commit.
5. Inspects commit tree: confirms only pointer metadata is stored in Git history.
6. Clones the repository to a clean directory.
7. Smudges / restores the binary from local cache.
8. Validates bit-for-bit SHA-256 match between original binary and restored binary.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "cli" / "gitsync.py"


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Stdout:\n{res.stdout}")
        print(f"Stderr:\n{res.stderr}")
        raise RuntimeError(f"Command failed with code {res.returncode}")
    return res


def main() -> None:
    print("=" * 60)
    print(" GitSync Studio — Large-File Pointer End-to-End Verification")
    print("=" * 60)

    work_dir = Path(tempfile.mkdtemp(prefix="gitsync_e2e_"))
    try:
        origin_repo = work_dir / "origin_repo"
        clone_repo = work_dir / "clone_repo"
        origin_repo.mkdir()

        cache_dir = work_dir / "cache"
        cache_dir.mkdir()
        os.environ["GITSYNC_CACHE_DIR"] = str(cache_dir)

        print(f"\n[1/7] Initializing test Git repository at {origin_repo}...")
        run_cmd(["git", "init", "-b", "main"], cwd=origin_repo)
        run_cmd(["git", "config", "user.name", "GitSync Tester"], cwd=origin_repo)
        run_cmd(["git", "config", "user.email", "tester@gitsync.studio"], cwd=origin_repo)

        print("\n[2/7] Running 'gitsync init' to configure clean/smudge filters...")
        run_cmd([sys.executable, str(CLI_PATH), "init"], cwd=origin_repo)

        # Check git config
        clean_cfg = run_cmd(["git", "config", "filter.gitsync.clean"], cwd=origin_repo).stdout.strip()
        smudge_cfg = run_cmd(["git", "config", "filter.gitsync.smudge"], cwd=origin_repo).stdout.strip()
        assert "clean" in clean_cfg, f"Clean filter not configured: {clean_cfg}"
        assert "smudge" in smudge_cfg, f"Smudge filter not configured: {smudge_cfg}"
        print(f"  ✓ Git clean filter configured:  {clean_cfg}")
        print(f"  ✓ Git smudge filter configured: {smudge_cfg}")

        print("\n[3/7] Tracking '*.bin' with 'gitsync track'...")
        run_cmd([sys.executable, str(CLI_PATH), "track", "*.bin"], cwd=origin_repo)
        gitattrs = (origin_repo / ".gitattributes").read_text()
        assert "*.bin filter=gitsync" in gitattrs, ".gitattributes missing *.bin rule"
        print("  ✓ .gitattributes verified")

        print("\n[4/7] Generating a 2 MB non-trivial binary payload...")
        test_file = origin_repo / "model_weights.bin"
        # Generate non-trivial deterministic binary data
        raw_payload = b"GitSync-Large-File-Payload-Chunk-Header\x00\xff\xfe" * 50000  # ~2.1 MB
        test_file.write_bytes(raw_payload)
        original_oid = hashlib.sha256(raw_payload).hexdigest().lower()
        original_size = len(raw_payload)
        print(f"  ✓ Created binary: {original_size} bytes (SHA-256: {original_oid[:16]}...)")

        print("\n[5/7] Staging and committing binary file to Git...")
        run_cmd(["git", "add", ".gitattributes", "model_weights.bin"], cwd=origin_repo)
        run_cmd(["git", "commit", "-m", "Add large model weights via GitSync"], cwd=origin_repo)

        # Inspect the committed object directly in Git object database
        git_cat = run_cmd(["git", "cat-file", "-p", "HEAD:model_weights.bin"], cwd=origin_repo).stdout
        print(f"  ✓ Git commit object content:\n{git_cat.strip()}")
        assert git_cat.startswith("version https://gitsync.studio/spec/v1"), "Committed object is not pointer!"
        assert f"oid sha256:{original_oid}" in git_cat, "Committed pointer OID mismatch!"
        assert f"size {original_size}" in git_cat, "Committed pointer size mismatch!"
        print("  ✓ Verified: Only the lightweight pointer was committed to Git!")

        # Verify local cache contains the raw binary
        cached_blob = cache_dir / original_oid
        assert cached_blob.is_file(), f"Cached blob missing: {cached_blob}"
        assert cached_blob.read_bytes() == raw_payload, "Cached blob corrupted"
        print("  ✓ Verified: Binary is safely stored in GitSync cache")

        print("\n[6/7] Cloning repository to a fresh directory to test checkout & smudge...")
        run_cmd(["git", "clone", str(origin_repo), str(clone_repo)], cwd=work_dir)
        run_cmd(["git", "config", "user.name", "GitSync Tester"], cwd=clone_repo)
        run_cmd(["git", "config", "user.email", "tester@gitsync.studio"], cwd=clone_repo)

        # Initialize GitSync in clone
        run_cmd([sys.executable, str(CLI_PATH), "init"], cwd=clone_repo)
        # Restore / check out
        run_cmd([sys.executable, str(CLI_PATH), "restore"], cwd=clone_repo)

        print("\n[7/7] Validating bit-for-bit SHA-256 match in cloned directory...")
        restored_file = clone_repo / "model_weights.bin"
        assert restored_file.is_file(), "Restored file does not exist!"
        restored_bytes = restored_file.read_bytes()
        restored_oid = hashlib.sha256(restored_bytes).hexdigest().lower()

        assert restored_bytes == raw_payload, "Restored binary content does not match original!"
        assert restored_oid == original_oid, f"OID mismatch: {restored_oid} != {original_oid}"
        print(f"  ✓ Original SHA-256: {original_oid}")
        print(f"  ✓ Restored SHA-256: {restored_oid}")
        print(f"  ✓ Exact bit-for-bit match verified across {len(restored_bytes)} bytes!")

        print("\n" + "=" * 60)
        print(" SUCCESS: All GitSync Large-File Pointer E2E tests passed!")
        print("=" * 60)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
