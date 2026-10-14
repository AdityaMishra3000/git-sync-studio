from __future__ import annotations

import contextlib
import os
from pathlib import Path

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    ".venv-ml",
    "venv",
    "env",
    "dist",
    "build",
    "target",
    ".next",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    ".gradle",
    "coverage",
    ".idea",
    ".vscode",
    ".output",
    "vendor",
    "pods",
}

LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".c": "C",
    ".h": "C",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".swift": "Swift",
    ".dart": "Dart",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
}

MAX_TOTAL_FILES = 5000
MAX_FILE_READ_BYTES = 512 * 1024  # 512 KB


class RepositoryInventory:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.files: list[str] = []
        self.directories: list[str] = []
        self.language_counts: dict[str, int] = {}
        self.language_bytes: dict[str, int] = {}
        self.manifest_files: list[str] = []
        self.docker_files: list[str] = []
        self.compose_files: list[str] = []
        self.ci_files: list[str] = []
        self.doc_files: list[str] = []
        self.env_files: list[str] = []
        self.test_files: list[str] = []
        self.license_file: str | None = None

    def read_text_safe(self, rel_path: str) -> str | None:
        """Safely read text file within repository root with size limits."""
        try:
            full_path = (self.root / rel_path).resolve()
            # Prevent directory traversal
            if not str(full_path).startswith(str(self.root)):
                return None
            if not full_path.is_file():
                return None
            if full_path.stat().st_size > MAX_FILE_READ_BYTES:
                with open(full_path, encoding="utf-8", errors="replace") as f:
                    return f.read(MAX_FILE_READ_BYTES)
            with open(full_path, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return None


def scan_repository(repo_path: Path) -> RepositoryInventory:
    """Safely traverse the repository and produce a normalized inventory."""
    resolved_root = repo_path.resolve()
    if not resolved_root.is_dir():
        raise ValueError(f"Repository directory does not exist: {repo_path}")

    inventory = RepositoryInventory(resolved_root)
    file_count = 0

    for root, dirs, files in os.walk(resolved_root, topdown=True, followlinks=False):
        # Prevent following symlinks outside permitted root
        current_dir = Path(root).resolve()
        if not str(current_dir).startswith(str(resolved_root)):
            dirs[:] = []
            continue

        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".git")]

        rel_dir = current_dir.relative_to(resolved_root).as_posix()
        if rel_dir != ".":
            inventory.directories.append(rel_dir)

        for filename in files:
            if file_count >= MAX_TOTAL_FILES:
                break

            file_path = current_dir / filename
            try:
                rel_file = file_path.relative_to(resolved_root).as_posix()
            except ValueError:
                continue

            inventory.files.append(rel_file)
            file_count += 1

            # Language detection
            ext = file_path.suffix.lower()
            if ext in LANGUAGE_EXTENSIONS:
                lang = LANGUAGE_EXTENSIONS[ext]
                inventory.language_counts[lang] = inventory.language_counts.get(lang, 0) + 1
                with contextlib.suppress(OSError):
                    size = file_path.stat().st_size
                    inventory.language_bytes[lang] = inventory.language_bytes.get(lang, 0) + size

            # Manifests
            lower_name = filename.lower()
            manifest_names = {
                "package.json",
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "requirements.txt",
                "cargo.toml",
                "go.mod",
                "pom.xml",
                "build.gradle",
                "build.gradle.kts",
                "cmakelists.txt",
                "makefile",
                "gemfile",
                "composer.json",
            }
            if lower_name in manifest_names or (
                lower_name.startswith("requirements") and lower_name.endswith(".txt")
            ):
                inventory.manifest_files.append(rel_file)

            # Docker and container manifests
            if lower_name.startswith("dockerfile") or lower_name.endswith(".dockerfile"):
                inventory.docker_files.append(rel_file)
            elif lower_name in {
                "compose.yaml",
                "compose.yml",
                "docker-compose.yaml",
                "docker-compose.yml",
            } or (
                lower_name.startswith("docker-compose.")
                and (lower_name.endswith(".yml") or lower_name.endswith(".yaml"))
            ):
                inventory.compose_files.append(rel_file)

            # CI/CD
            is_workflow = ".github/workflows" in rel_file and (
                lower_name.endswith(".yml") or lower_name.endswith(".yaml")
            )
            if is_workflow or lower_name in {".gitlab-ci.yml", "jenkinsfile", ".travis.yml"}:
                inventory.ci_files.append(rel_file)

            # Docs and licenses
            if lower_name.startswith("license") or lower_name.startswith("copying"):
                inventory.license_file = rel_file
            elif (
                lower_name.startswith("readme")
                or lower_name.startswith("contributing")
                or lower_name.startswith("changelog")
            ):
                inventory.doc_files.append(rel_file)

            # Env templates
            if lower_name.startswith(".env"):
                inventory.env_files.append(rel_file)

            # Tests
            if (
                ".test." in lower_name
                or ".spec." in lower_name
                or lower_name.startswith("test_")
                or lower_name.endswith("_test.py")
                or lower_name.endswith("_test.go")
                or "tests/" in rel_file
                or "test/" in rel_file
                or "__tests__/" in rel_file
            ):
                inventory.test_files.append(rel_file)

        if file_count >= MAX_TOTAL_FILES:
            break

    return inventory
