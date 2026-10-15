#!/usr/bin/env python3
"""GitSync Studio CLI.

Provides Git-LFS-inspired large file tracking backed by GitSync Studio API
and Google Drive. Handles git clean/smudge filters, pointer file generation,
deduplication, download caching, and repository restoration.

Designed to run seamlessly both with standard library dependencies (argparse, urllib)
and enriched packages (typer, httpx).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# Optional enriched dependencies
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    httpx = None  # type: ignore[assignment]
    HAS_HTTPX = False

try:
    import typer
    HAS_TYPER = True
except ImportError:
    typer = None  # type: ignore[assignment]
    HAS_TYPER = False

API_URL = os.environ.get("GITSYNC_API_URL", "http://localhost:8000/api/v1")


def get_git_root() -> Path | None:
    """Find the root directory of the current git repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(res.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def get_cache_dir() -> Path:
    """Get cache directory, falling back to workspace or /tmp if home is read-only."""
    env_dir = os.environ.get("GITSYNC_CACHE_DIR")
    if env_dir:
        p = Path(env_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    home_cache = Path.home() / ".gitsync" / "cache"
    try:
        home_cache.mkdir(parents=True, exist_ok=True)
        return home_cache
    except (OSError, PermissionError):
        git_root = get_git_root()
        fallback = (git_root / ".gitsync" / "cache") if git_root else Path("/tmp/gitsync_cache")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


class CacheDirProxy(os.PathLike[str]):
    """Dynamic path proxy that resolves cache directory at runtime."""

    def __fspath__(self) -> str:
        return str(get_cache_dir())

    def __truediv__(self, other: str | Path) -> Path:
        return get_cache_dir() / other

    def __str__(self) -> str:
        return str(get_cache_dir())

    def __repr__(self) -> str:
        return repr(get_cache_dir())

    def __getattr__(self, name: str) -> Any:
        return getattr(get_cache_dir(), name)


CACHE_DIR = CacheDirProxy()

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


def parse_pointer(content: str | bytes) -> dict[str, Any] | None:
    """Parse and validate a large-file pointer file."""
    if isinstance(content, bytes):
        try:
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
    """Check if content represents a valid pointer."""
    return parse_pointer(content) is not None




def get_repo_id() -> str | None:
    """Get configured repository UUID from local config or environment."""
    env_id = os.environ.get("GITSYNC_REPO_ID")
    if env_id:
        return env_id

    git_root = get_git_root()
    if git_root:
        config_file = git_root / ".gitsync" / "config.json"
        if config_file.is_file():
            try:
                data = json.loads(config_file.read_text())
                return data.get("repo_id")
            except Exception:
                pass
    return None


# --- HTTP Utilities (supporting both httpx and urllib) ---------------------

def http_get(url: str, timeout: float = 30.0) -> tuple[int, bytes, dict[str, str]]:
    """Perform HTTP GET request returning (status_code, body_bytes, headers)."""
    if HAS_HTTPX and httpx:
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.get(url)
                return r.status_code, r.content, dict(r.headers)
        except Exception as e:
            raise ConnectionError(f"HTTP GET error to {url}: {e}") from e

    req = urllib.request.Request(url, headers={"User-Agent": "GitSync-CLI/0.1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        raise ConnectionError(f"HTTP GET error to {url}: {e}") from e


def http_post_multipart(
    url: str,
    fields: dict[str, str],
    file_field: str,
    file_name: str,
    file_bytes: bytes,
    timeout: float = 60.0,
) -> tuple[int, bytes]:
    """Perform HTTP POST multipart/form-data upload."""
    if HAS_HTTPX and httpx:
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.post(
                    url,
                    data=fields,
                    files={file_field: (file_name, file_bytes)},
                )
                return r.status_code, r.content
        except Exception as e:
            raise ConnectionError(f"HTTP POST error to {url}: {e}") from e

    boundary = "----GitSyncBoundary" + hashlib.md5(os.urandom(16)).hexdigest()
    parts: list[bytes] = []

    for name, value in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())

    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{file_name}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
    )
    parts.append(file_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode())

    body = b"".join(parts)
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "User-Agent": "GitSync-CLI/0.1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        raise ConnectionError(f"HTTP POST error to {url}: {e}") from e


# --- Command Implementations -----------------------------------------------

def do_init(repo_id: str | None = None) -> int:
    git_root = get_git_root()
    if not git_root:
        sys.stderr.write("Error: Current directory is not inside a Git repository.\n")
        return 1

    cli_path = Path(__file__).resolve()
    python_exec = sys.executable

    clean_cmd = f'"{python_exec}" "{cli_path}" clean'
    smudge_cmd = f'"{python_exec}" "{cli_path}" smudge'

    subprocess.run(["git", "config", "filter.gitsync.clean", clean_cmd], check=True)
    subprocess.run(["git", "config", "filter.gitsync.smudge", smudge_cmd], check=True)
    subprocess.run(["git", "config", "filter.gitsync.required", "true"], check=True)

    attr_file = git_root / ".gitattributes"
    current_content = attr_file.read_text() if attr_file.is_file() else ""

    patterns = ["*.zip", "*.tar.gz", "*.tgz", "*.bin", "*.iso", "*.mp4", "*.mov"]
    new_entries = []
    for pattern in patterns:
        entry = f"{pattern} filter=gitsync diff=gitsync merge=binary -text"
        if entry not in current_content:
            new_entries.append(entry)

    if new_entries:
        with open(attr_file, "a") as f:
            if current_content and not current_content.endswith("\n"):
                f.write("\n")
            f.write("# GitSync Studio large files\n")
            for entry in new_entries:
                f.write(f"{entry}\n")

    if repo_id:
        config_dir = git_root / ".gitsync"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "config.json").write_text(json.dumps({"repo_id": repo_id}, indent=2))

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print("GitSync Studio initialized successfully!")
    print("  • Git filters configured: clean & smudge")
    print(f"  • Tracked patterns in .gitattributes: {', '.join(patterns)}")
    print(f"  • Local cache: {CACHE_DIR}")
    return 0


def do_track(pattern: str) -> int:
    git_root = get_git_root()
    if not git_root:
        sys.stderr.write("Error: Not inside a Git repository.\n")
        return 1

    attr_file = git_root / ".gitattributes"
    entry = f"{pattern} filter=gitsync diff=gitsync merge=binary -text"
    current_content = attr_file.read_text() if attr_file.is_file() else ""

    if entry in current_content:
        print(f"Pattern '{pattern}' is already tracked by GitSync.")
        return 0

    with open(attr_file, "a") as f:
        if current_content and not current_content.endswith("\n"):
            f.write("\n")
        f.write(f"{entry}\n")

    print(f"Tracking '{pattern}' with GitSync Studio.")
    return 0


def do_clean() -> int:
    try:
        content = sys.stdin.buffer.read()
    except Exception as e:
        sys.stderr.write(f"GitSync clean error reading stdin: {e}\n")
        return 1

    if is_pointer(content):
        sys.stdout.buffer.write(content)
        return 0

    oid = hashlib.sha256(content).hexdigest().lower()
    size = len(content)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / oid
    if not cache_path.is_file():
        cache_path.write_bytes(content)

    pointer_text = create_pointer(oid, size)
    sys.stdout.buffer.write(pointer_text.encode("utf-8"))
    return 0


def do_smudge() -> int:
    try:
        content = sys.stdin.buffer.read()
    except Exception as e:
        sys.stderr.write(f"GitSync smudge error reading stdin: {e}\n")
        return 1

    parsed = parse_pointer(content)
    if not parsed:
        sys.stdout.buffer.write(content)
        return 0

    oid = str(parsed["oid"])
    expected_size = int(parsed["size_bytes"])
    cache_path = CACHE_DIR / oid

    if cache_path.is_file() and cache_path.stat().st_size == expected_size:
        cached_data = cache_path.read_bytes()
        if hashlib.sha256(cached_data).hexdigest().lower() == oid:
            sys.stdout.buffer.write(cached_data)
            return 0

    try:
        status, data, _ = http_get(f"{API_URL}/drive/download/{oid}", timeout=30.0)
        if status == 200:
            if hashlib.sha256(data).hexdigest().lower() == oid:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(data)
                sys.stdout.buffer.write(data)
                return 0
            sys.stderr.write(f"GitSync warning: Checksum mismatch for OID {oid}.\n")
        else:
            sys.stderr.write(f"GitSync warning: Could not download OID {oid} (HTTP {status}).\n")
    except Exception as err:
        sys.stderr.write(f"GitSync warning: Download failed for {oid}: {err}\n")

    sys.stdout.buffer.write(content)
    return 0


def do_upload(file_path: Path, repo_id: str | None = None) -> int:
    if not file_path.is_file():
        sys.stderr.write(f"Error: File {file_path} does not exist.\n")
        return 1

    target_repo_id = repo_id or get_repo_id()
    if not target_repo_id:
        sys.stderr.write("Error: Repository ID not specified. Use --repo-id or run 'gitsync init --repo-id <id>'\n")
        return 1

    content = file_path.read_bytes()
    if is_pointer(content):
        print(f"File {file_path} is already a pointer file.")
        return 0

    oid = hashlib.sha256(content).hexdigest().lower()
    size = len(content)
    print(f"Uploading {file_path.name} (SHA-256: {oid[:12]}..., Size: {size} bytes)...")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / oid).write_bytes(content)

    try:
        status, res_bytes = http_post_multipart(
            f"{API_URL}/drive/upload",
            fields={"repo_id": target_repo_id, "path": str(file_path)},
            file_field="file",
            file_name=file_path.name,
            file_bytes=content,
        )
        if status == 200:
            res_data = json.loads(res_bytes.decode())
            reused = res_data.get("reused", False)
            if reused:
                print("Binary blob deduplicated! Reusing existing stored object.")
            else:
                print("Successfully uploaded to storage.")

            pointer_text = create_pointer(oid, size)
            file_path.write_text(pointer_text)
            print(f"Replaced {file_path} with GitSync pointer file.")
            return 0
        sys.stderr.write(f"Upload failed (HTTP {status}): {res_bytes.decode()}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Network error connecting to {API_URL}: {e}\n")
        return 1


def do_download(oid: str, out: Path) -> int:
    clean_oid = oid.lower().strip()
    if clean_oid.startswith("sha256:"):
        clean_oid = clean_oid[7:]

    cache_path = CACHE_DIR / clean_oid
    if cache_path.is_file():
        data = cache_path.read_bytes()
        if hashlib.sha256(data).hexdigest().lower() == clean_oid:
            print(f"Restoring from local cache: {clean_oid[:12]}...")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            print(f"Written to {out} (verified bit-for-bit match).")
            return 0

    print(f"Downloading OID {clean_oid[:12]}... from API...")
    try:
        status, data, _ = http_get(f"{API_URL}/drive/download/{clean_oid}", timeout=60.0)
        if status != 200:
            sys.stderr.write(f"Failed to download object (HTTP {status}): {data.decode(errors='replace')}\n")
            return 1

        actual_digest = hashlib.sha256(data).hexdigest().lower()
        if actual_digest != clean_oid:
            sys.stderr.write(f"Integrity check failed: expected {clean_oid}, got {actual_digest}\n")
            return 1

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"Downloaded and verified {clean_oid[:12]}... -> {out}")
        return 0
    except Exception as e:
        sys.stderr.write(f"Network error: {e}\n")
        return 1


def do_restore() -> int:
    git_root = get_git_root()
    search_root = git_root or Path.cwd()

    print(f"Scanning for pointer files in {search_root}...")
    restored = 0
    total_bytes = 0

    for path in search_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".git") for part in path.parts):
            continue

        try:
            content = path.read_bytes()
        except (OSError, PermissionError):
            continue

        parsed = parse_pointer(content)
        if not parsed:
            continue

        oid = str(parsed["oid"])
        size = int(parsed["size_bytes"])
        print(f"Restoring pointer: {path.relative_to(search_root)} (OID: {oid[:12]}..., {size} bytes)...")

        cache_path = CACHE_DIR / oid
        data: bytes | None = None

        if cache_path.is_file() and cache_path.stat().st_size == size:
            cached_bytes = cache_path.read_bytes()
            if hashlib.sha256(cached_bytes).hexdigest().lower() == oid:
                data = cached_bytes

        if data is None:
            try:
                status, downloaded, _ = http_get(f"{API_URL}/drive/download/{oid}", timeout=60.0)
                if status == 200 and hashlib.sha256(downloaded).hexdigest().lower() == oid:
                    data = downloaded
                    cache_path.write_bytes(data)
            except Exception as err:
                sys.stderr.write(f"  Warning: failed to download {oid}: {err}\n")

        if data is not None:
            path.write_bytes(data)
            restored += 1
            total_bytes += len(data)
            print(f"  Restored {path.name} ({len(data)} bytes).")
        else:
            sys.stderr.write(f"  Could not restore {path.name} (not found in cache or remote API).\n")

    print(f"Restoration complete: {restored} file(s) restored ({total_bytes} bytes).")
    return 0


def do_verify(oid: str | None = None) -> int:
    if oid:
        clean_oid = oid.lower().strip()
        if clean_oid.startswith("sha256:"):
            clean_oid = clean_oid[7:]
        target_file = CACHE_DIR / clean_oid
        if not target_file.is_file():
            sys.stderr.write(f"OID {clean_oid} not found in local cache.\n")
            return 1
        data = target_file.read_bytes()
        actual = hashlib.sha256(data).hexdigest().lower()
        if actual == clean_oid:
            print(f"OID {clean_oid}: VALID (Size: {len(data)} bytes)")
            return 0
        sys.stderr.write(f"OID {clean_oid}: CORRUPT (Calculated: {actual})\n")
        return 1

    print(f"Verifying local cache at {CACHE_DIR}...")
    if not CACHE_DIR.is_dir():
        print("Cache directory is empty.")
        return 0

    files = [f for f in CACHE_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    valid_count = 0
    corrupt_count = 0

    for f in files:
        expected = f.name.lower()
        data = f.read_bytes()
        actual = hashlib.sha256(data).hexdigest().lower()
        if actual == expected:
            valid_count += 1
        else:
            corrupt_count += 1
            sys.stderr.write(f"  CORRUPT: {f.name} (Calculated: {actual})\n")

    print(f"Verification complete: {valid_count} valid, {corrupt_count} corrupt.")
    return 0 if corrupt_count == 0 else 1


def do_status() -> int:
    print("=== GitSync Studio Status ===")
    git_root = get_git_root()
    if git_root:
        print(f"Git Repository: {git_root}")
        try:
            clean_cfg = subprocess.run(["git", "config", "filter.gitsync.clean"], capture_output=True, text=True).stdout.strip()
            smudge_cfg = subprocess.run(["git", "config", "filter.gitsync.smudge"], capture_output=True, text=True).stdout.strip()
            print(f"Git Clean Filter:  {clean_cfg or 'Not configured'}")
            print(f"Git Smudge Filter: {smudge_cfg or 'Not configured'}")
        except Exception:
            pass
    else:
        print("Git Repository: Not in a Git repository")

    repo_id = get_repo_id()
    print(f"Repository UUID: {repo_id or 'None'}")
    print(f"API URL:         {API_URL}")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached_files = [f for f in CACHE_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    total_cache_size = sum(f.stat().st_size for f in cached_files)
    print(f"Local Cache:     {len(cached_files)} files ({total_cache_size} bytes) in {CACHE_DIR}")

    try:
        status, data, _ = http_get(f"{API_URL}/drive/status", timeout=3.0)
        if status == 200:
            parsed = json.loads(data.decode())
            provider = parsed.get("provider", "unknown")
            configured = parsed.get("configured", False)
            live_active = parsed.get("live_drive_active", False)
            total_objs = parsed.get("total_objects", 0)
            dedup_savings = parsed.get("dedup_savings_bytes", 0)

            print(f"Storage Provider: {provider} (Configured: {configured}, Live Drive: {live_active})")
            print(f"Remote Objects:   {total_objs} tracked, {dedup_savings} bytes saved via deduplication")
        else:
            print(f"API Status: HTTP {status}")
    except Exception as e:
        print(f"API Status: Unreachable ({e})")
    return 0


# --- Typer and Argparse Entrypoints ----------------------------------------

if HAS_TYPER and typer:
    app = typer.Typer(help="GitSync Studio CLI — Large-file pointer management.")

    @app.command()
    def init(repo_id: str | None = typer.Option(None, "--repo-id", help="Repository UUID")) -> None:
        """Initialize GitSync filters in current repository."""
        code = do_init(repo_id)
        if code != 0:
            raise typer.Exit(code)

    @app.command()
    def track(pattern: str = typer.Argument(..., help="File pattern to track")) -> None:
        """Track file pattern with GitSync Studio."""
        code = do_track(pattern)
        if code != 0:
            raise typer.Exit(code)

    @app.command(name="clean")
    def clean() -> None:
        """Git clean filter: Stdin (binary) -> Stdout (pointer)."""
        sys.exit(do_clean())

    @app.command(name="smudge")
    def smudge() -> None:
        """Git smudge filter: Stdin (pointer) -> Stdout (binary)."""
        sys.exit(do_smudge())

    @app.command()
    def upload(file_path: Path, repo_id: str | None = None) -> None:
        """Upload large file to GitSync and replace with pointer."""
        code = do_upload(file_path, repo_id)
        if code != 0:
            raise typer.Exit(code)

    @app.command()
    def download(oid: str, out: Path = typer.Option(..., "--out", "-o")) -> None:
        """Download large file by OID and verify integrity."""
        code = do_download(oid, out)
        if code != 0:
            raise typer.Exit(code)

    @app.command()
    def restore() -> None:
        """Scan repository and restore all pointer files."""
        code = do_restore()
        if code != 0:
            raise typer.Exit(code)

    @app.command()
    def verify(oid: str | None = typer.Option(None, "--oid")) -> None:
        """Verify local cache integrity."""
        code = do_verify(oid)
        if code != 0:
            raise typer.Exit(code)

    @app.command()
    def status() -> None:
        """Show GitSync Studio status."""
        code = do_status()
        if code != 0:
            raise typer.Exit(code)


def main() -> None:
    if HAS_TYPER and typer and len(sys.argv) > 1 and sys.argv[1] not in {"clean", "smudge"}:
        app()
        return

    parser = argparse.ArgumentParser(description="GitSync Studio CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    init_parser = subparsers.add_parser("init", help="Initialize GitSync repository")
    init_parser.add_argument("--repo-id", help="Repository UUID")

    track_parser = subparsers.add_parser("track", help="Track a file pattern")
    track_parser.add_argument("pattern", help="File pattern to track")

    subparsers.add_parser("clean", help="Git clean filter")
    subparsers.add_parser("smudge", help="Git smudge filter")

    upload_parser = subparsers.add_parser("upload", help="Upload large file")
    upload_parser.add_argument("file_path", type=Path, help="Path to binary file")
    upload_parser.add_argument("--repo-id", help="Repository UUID")

    download_parser = subparsers.add_parser("download", help="Download large file by OID")
    download_parser.add_argument("oid", help="SHA-256 OID")
    download_parser.add_argument("--out", "-o", type=Path, required=True, help="Output destination")

    subparsers.add_parser("restore", help="Restore pointer files in repo")

    verify_parser = subparsers.add_parser("verify", help="Verify cache integrity")
    verify_parser.add_argument("--oid", help="Specific OID to verify")

    subparsers.add_parser("status", help="Show GitSync status")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "init":
        sys.exit(do_init(args.repo_id))
    elif args.command == "track":
        sys.exit(do_track(args.pattern))
    elif args.command == "clean":
        sys.exit(do_clean())
    elif args.command == "smudge":
        sys.exit(do_smudge())
    elif args.command == "upload":
        sys.exit(do_upload(args.file_path, args.repo_id))
    elif args.command == "download":
        sys.exit(do_download(args.oid, args.out))
    elif args.command == "restore":
        sys.exit(do_restore())
    elif args.command == "verify":
        sys.exit(do_verify(args.oid))
    elif args.command == "status":
        sys.exit(do_status())


if __name__ == "__main__":
    main()
