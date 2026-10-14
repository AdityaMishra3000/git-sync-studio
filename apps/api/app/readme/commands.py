from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.readme.models import CommandEvidence, EvidenceProvenance
from app.readme.scanner import RepositoryInventory


def infer_commands(
    inventory: RepositoryInventory,
    repo_name: str,
    manifest_data: dict[str, Any],
) -> list[CommandEvidence]:
    """Derive accurate, copyable commands for installation, development, testing, and builds."""
    commands: list[CommandEvidence] = []
    root = inventory.root

    # 1. Docker Compose
    if inventory.compose_files:
        compose_file = inventory.compose_files[0]
        commands.append(
            CommandEvidence(
                category="docker",
                command=f"docker compose -f {compose_file} up -d --build",
                description="Start all services in background with Docker Compose",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=compose_file,
                        evidence_type="compose",
                        confidence="verified",
                        detail="Discovered docker compose configuration file",
                    )
                ],
                verified=True,
            )
        )
        commands.append(
            CommandEvidence(
                category="docker",
                command=f"docker compose -f {compose_file} down",
                description="Stop all Docker Compose services and clean up containers",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=compose_file,
                        evidence_type="compose",
                        confidence="verified",
                    )
                ],
                verified=True,
            )
        )

    # 2. JavaScript / TypeScript / Node.js
    pkg_json_files = [f for f in inventory.manifest_files if Path(f).name == "package.json"]
    for pkg_file in pkg_json_files:
        pkg_data = manifest_data.get(pkg_file)
        if not isinstance(pkg_data, dict):
            continue

        workdir = str(Path(pkg_file).parent)

        # Detect package manager
        pm = "npm"
        if (root / "pnpm-lock.yaml").exists() or (root / workdir / "pnpm-lock.yaml").exists():
            pm = "pnpm"
        elif (root / "yarn.lock").exists() or (root / workdir / "yarn.lock").exists():
            pm = "yarn"
        elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
            pm = "bun"

        # Install command
        install_cmd = f"{pm} install"
        commands.append(
            CommandEvidence(
                category="install",
                command=install_cmd,
                working_dir=workdir,
                description=f"Install JavaScript/TypeScript dependencies using {pm}",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=pkg_file,
                        evidence_type="manifest",
                        section="dependencies",
                        confidence="verified",
                    )
                ],
                verified=True,
            )
        )

        scripts: dict[str, str] = pkg_data.get("scripts", {})
        for script_name, script_val in scripts.items():
            if "dev" in script_name:
                category = "run_dev"
            elif "build" in script_name:
                category = "build"
            elif "test" in script_name:
                category = "test"
            elif "lint" in script_name:
                category = "lint"
            else:
                category = "custom"

            if pm in {"pnpm", "bun", "yarn"}:
                cmd_str = f"{pm} {script_name}"
            elif script_name in {"start", "test"}:
                cmd_str = f"npm {script_name}"
            else:
                cmd_str = f"npm run {script_name}"

            commands.append(
                CommandEvidence(
                    category=category,
                    command=cmd_str,
                    working_dir=workdir,
                    description=f"Run '{script_name}' script ({script_val})",
                    confidence="verified",
                    provenance=[
                        EvidenceProvenance(
                            path=pkg_file,
                            evidence_type="manifest",
                            section=f"scripts.{script_name}",
                            confidence="verified",
                            detail=f"Executes: {script_val}",
                        )
                    ],
                    verified=True,
                )
            )

    # 3. Python (uv, poetry, pip, setuptools, requirements)
    pyproject_files = [f for f in inventory.manifest_files if Path(f).name == "pyproject.toml"]
    for py_file in pyproject_files:
        py_data = manifest_data.get(py_file)
        workdir = str(Path(py_file).parent)
        is_poetry = False
        is_uv = (root / "uv.lock").exists() or (root / workdir / "uv.lock").exists()

        if isinstance(py_data, dict):
            build_backend = py_data.get("build-system", {}).get("build-backend", "")
            if "poetry" in build_backend or "tool.poetry" in str(py_data):
                is_poetry = True

        if is_uv:
            commands.append(
                CommandEvidence(
                    category="install",
                    command="uv sync",
                    working_dir=workdir,
                    description="Synchronize Python dependencies and environment using uv",
                    confidence="verified",
                    provenance=[
                        EvidenceProvenance(
                            path=py_file,
                            evidence_type="manifest",
                            confidence="verified",
                            detail="uv package manager detected",
                        )
                    ],
                    verified=True,
                )
            )
            commands.append(
                CommandEvidence(
                    category="run_dev",
                    command="uv run python -m app",
                    working_dir=workdir,
                    description="Run Python application within uv environment",
                    confidence="inferred",
                    provenance=[
                        EvidenceProvenance(
                            path=py_file,
                            evidence_type="manifest",
                            confidence="inferred",
                        )
                    ],
                    verified=False,
                )
            )
        elif is_poetry:
            commands.append(
                CommandEvidence(
                    category="install",
                    command="poetry install",
                    working_dir=workdir,
                    description="Install Python dependencies using Poetry",
                    confidence="verified",
                    provenance=[
                        EvidenceProvenance(
                            path=py_file,
                            evidence_type="manifest",
                            confidence="verified",
                            detail="Poetry build backend detected",
                        )
                    ],
                    verified=True,
                )
            )
            commands.append(
                CommandEvidence(
                    category="run_dev",
                    command="poetry run python -m app",
                    working_dir=workdir,
                    description="Execute Python application within Poetry environment",
                    confidence="inferred",
                    provenance=[
                        EvidenceProvenance(
                            path=py_file,
                            evidence_type="manifest",
                            confidence="inferred",
                        )
                    ],
                    verified=False,
                )
            )
        else:
            commands.append(
                CommandEvidence(
                    category="install",
                    command="pip install -e .",
                    working_dir=workdir,
                    description="Install package in editable mode via pip",
                    confidence="verified",
                    provenance=[
                        EvidenceProvenance(
                            path=py_file,
                            evidence_type="manifest",
                            confidence="verified",
                        )
                    ],
                    verified=True,
                )
            )

    # Plain requirements.txt (if no pyproject.toml in that directory)
    req_files = [
        f
        for f in inventory.manifest_files
        if Path(f).name.startswith("requirements") and f.endswith(".txt")
    ]
    for req_file in req_files:
        workdir = str(Path(req_file).parent)
        if any(Path(p).parent == Path(req_file).parent for p in pyproject_files):
            continue
        commands.append(
            CommandEvidence(
                category="install",
                command=f"pip install -r {Path(req_file).name}",
                working_dir=workdir,
                description=f"Install Python dependencies from {Path(req_file).name}",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=req_file,
                        evidence_type="manifest",
                        confidence="verified",
                    )
                ],
                verified=True,
            )
        )

    # Python test commands (pytest check)
    if any(f.endswith(".py") and ("test" in f) for f in inventory.test_files):
        commands.append(
            CommandEvidence(
                category="test",
                command="pytest",
                working_dir="." if not pyproject_files else str(Path(pyproject_files[0]).parent),
                description="Run Python test suite with pytest",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=inventory.test_files[0] if inventory.test_files else "tests",
                        evidence_type="source_code",
                        confidence="verified",
                        detail="Python test files detected",
                    )
                ],
                verified=True,
            )
        )

    # 4. Go
    go_mod_files = [f for f in inventory.manifest_files if Path(f).name == "go.mod"]
    for go_file in go_mod_files:
        workdir = str(Path(go_file).parent)
        commands.append(
            CommandEvidence(
                category="install",
                command="go mod download",
                working_dir=workdir,
                description="Download and verify Go module dependencies",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=go_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )
        commands.append(
            CommandEvidence(
                category="build",
                command="go build ./...",
                working_dir=workdir,
                description="Compile Go packages and packages",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=go_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )
        commands.append(
            CommandEvidence(
                category="test",
                command="go test -v ./...",
                working_dir=workdir,
                description="Execute Go test suites with verbose output",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=go_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )

    # 5. Rust (Cargo)
    cargo_files = [f for f in inventory.manifest_files if Path(f).name == "Cargo.toml"]
    for cargo_file in cargo_files:
        workdir = str(Path(cargo_file).parent)
        commands.append(
            CommandEvidence(
                category="build",
                command="cargo build",
                working_dir=workdir,
                description="Build Rust project and binaries",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=cargo_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )
        commands.append(
            CommandEvidence(
                category="test",
                command="cargo test",
                working_dir=workdir,
                description="Run Rust unit and integration test harnesses",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=cargo_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )
        commands.append(
            CommandEvidence(
                category="run_dev",
                command="cargo run",
                working_dir=workdir,
                description="Compile and execute the default Rust binary target",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=cargo_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )

    # 6. Java (Gradle / Maven)
    gradle_files = [f for f in inventory.manifest_files if "build.gradle" in Path(f).name]
    for gradle_file in gradle_files:
        workdir = str(Path(gradle_file).parent)
        has_wrapper = (root / workdir / "gradlew").exists() or (root / "gradlew").exists()
        g_bin = "./gradlew" if has_wrapper else "gradle"
        commands.append(
            CommandEvidence(
                category="build",
                command=f"{g_bin} build",
                working_dir=workdir,
                description="Build project artifacts via Gradle",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=gradle_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )
        commands.append(
            CommandEvidence(
                category="test",
                command=f"{g_bin} test",
                working_dir=workdir,
                description="Execute Gradle test tasks",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=gradle_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )

    maven_files = [f for f in inventory.manifest_files if Path(f).name == "pom.xml"]
    for maven_file in maven_files:
        workdir = str(Path(maven_file).parent)
        has_wrapper = (root / workdir / "mvnw").exists() or (root / "mvnw").exists()
        m_bin = "./mvnw" if has_wrapper else "mvn"
        commands.append(
            CommandEvidence(
                category="build",
                command=f"{m_bin} clean install",
                working_dir=workdir,
                description="Clean and build Maven modules",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=maven_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )
        commands.append(
            CommandEvidence(
                category="test",
                command=f"{m_bin} test",
                working_dir=workdir,
                description="Run Maven test phase with Surefire plugin",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=maven_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )

    # 7. C++ / C (CMake)
    cmake_files = [f for f in inventory.manifest_files if Path(f).name.lower() == "cmakelists.txt"]
    for cmake_file in cmake_files:
        workdir = str(Path(cmake_file).parent)
        commands.append(
            CommandEvidence(
                category="build",
                command="cmake -B build -S . && cmake --build build",
                working_dir=workdir,
                description="Configure CMake project and compile build targets",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=cmake_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )
        commands.append(
            CommandEvidence(
                category="test",
                command="ctest --test-dir build --output-on-failure",
                working_dir=workdir,
                description="Run CMake test suite using CTest",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path=cmake_file, evidence_type="manifest", confidence="verified"
                    )
                ],
                verified=True,
            )
        )

    # 8. Makefile targets
    makefile_paths = [f for f in inventory.manifest_files if Path(f).name.lower() == "makefile"]
    for mf in makefile_paths:
        content = inventory.read_text_safe(mf)
        if content:
            targets = re.findall(r"^([a-zA-Z0-9_\-]+):", content, flags=re.MULTILINE)
            workdir = str(Path(mf).parent)
            for t in targets[:6]:
                if t in {".PHONY", "all", "default"}:
                    continue
                if "test" in t:
                    cat = "test"
                elif "build" in t:
                    cat = "build"
                elif "lint" in t:
                    cat = "lint"
                else:
                    cat = "custom"

                commands.append(
                    CommandEvidence(
                        category=cat,
                        command=f"make {t}",
                        working_dir=workdir,
                        description=f"Run Makefile target '{t}'",
                        confidence="verified",
                        provenance=[
                            EvidenceProvenance(
                                path=mf,
                                evidence_type="manifest",
                                section=f"target.{t}",
                                confidence="verified",
                            )
                        ],
                        verified=True,
                    )
                )

    return commands
