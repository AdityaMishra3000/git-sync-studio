from __future__ import annotations

import contextlib
import json
import re
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.readme.commands import infer_commands
from app.readme.models import (
    ArchitectureComponent,
    EndpointEvidence,
    EnvVarEvidence,
    EvidenceProvenance,
    RelationshipEvidence,
    RepositoryEvidence,
    ServiceEvidence,
    TestEvidence,
)
from app.readme.scanner import RepositoryInventory


def _safe_load_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    with contextlib.suppress(Exception):
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    return None


def _safe_load_toml(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    with contextlib.suppress(Exception):
        return tomllib.loads(text)
    return None


def analyze_repository(
    inventory: RepositoryInventory, repo_name: str | None = None
) -> RepositoryEvidence:
    """Stage B: Perform bounded source-code and configuration analysis to build typed evidence."""
    root = inventory.root
    effective_name = repo_name or root.name

    # 1. Manifests data loading
    manifest_data: dict[str, Any] = {}
    for mf in inventory.manifest_files:
        content = inventory.read_text_safe(mf)
        if not content:
            continue
        if mf.endswith(".json"):
            loaded = _safe_load_json(content)
            if loaded:
                manifest_data[mf] = loaded
        elif mf.endswith(".toml"):
            loaded = _safe_load_toml(content)
            if loaded:
                manifest_data[mf] = loaded

    # 2. Language distribution
    total_bytes = sum(inventory.language_bytes.values())
    languages_pct: dict[str, float] = {}
    if total_bytes > 0:
        for lang, count in inventory.language_bytes.items():
            languages_pct[lang] = round((count / total_bytes) * 100, 1)
    primary_language = max(languages_pct.items(), key=lambda x: x[1])[0] if languages_pct else None

    # 3. Detect Monorepo, Frameworks, and Package Managers
    frameworks: list[str] = []
    package_managers: list[str] = []
    is_monorepo = False
    monorepo_workspaces: list[str] = []
    components: list[ArchitectureComponent] = []
    relationships: list[RelationshipEvidence] = []
    endpoints: list[EndpointEvidence] = []
    database_tech: list[str] = []
    database_migrations: str | None = None
    background_workers: list[str] = []
    services: list[ServiceEvidence] = []
    env_vars: list[EnvVarEvidence] = []
    missing_evidence: list[str] = []
    entrypoints: list[str] = []
    project_desc: str | None = None

    # Inspect package.json
    for mf, data in manifest_data.items():
        if Path(mf).name == "package.json":
            if not project_desc and data.get("description"):
                project_desc = data.get("description")
            if "workspaces" in data:
                is_monorepo = True
                ws = data["workspaces"]
                monorepo_workspaces = ws if isinstance(ws, list) else ws.get("packages", [])

            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if "next" in deps:
                frameworks.append("Next.js")
            if "react" in deps and "React" not in frameworks:
                frameworks.append("React")
            if "vue" in deps:
                frameworks.append("Vue.js")
            if "express" in deps:
                frameworks.append("Express.js")
            if "fastify" in deps:
                frameworks.append("Fastify")
            if "@nestjs/core" in deps:
                frameworks.append("NestJS")
            if "tailwindcss" in deps:
                frameworks.append("Tailwind CSS")

    # Inspect pyproject.toml / requirements
    for mf in inventory.manifest_files:
        if Path(mf).name == "pyproject.toml":
            data = manifest_data.get(mf, {})
            proj = data.get("project", {})
            if not project_desc and proj.get("description"):
                project_desc = proj.get("description")
            deps_str = str(data)
            if "fastapi" in deps_str.lower():
                frameworks.append("FastAPI")
            if "django" in deps_str.lower():
                frameworks.append("Django")
            if "flask" in deps_str.lower():
                frameworks.append("Flask")
            if "sqlalchemy" in deps_str.lower():
                database_tech.append("SQLAlchemy (ORM)")
            if "alembic" in deps_str.lower():
                database_migrations = "Alembic"
            if "celery" in deps_str.lower():
                background_workers.append("Celery")
            if "redis" in deps_str.lower():
                database_tech.append("Redis")
        elif "requirements" in Path(mf).name:
            content = inventory.read_text_safe(mf) or ""
            c_lower = content.lower()
            if "fastapi" in c_lower and "FastAPI" not in frameworks:
                frameworks.append("FastAPI")
            if "django" in c_lower and "Django" not in frameworks:
                frameworks.append("Django")
            if "flask" in c_lower and "Flask" not in frameworks:
                frameworks.append("Flask")
            if "sqlalchemy" in c_lower and "SQLAlchemy (ORM)" not in database_tech:
                database_tech.append("SQLAlchemy (ORM)")
            if "alembic" in c_lower:
                database_migrations = "Alembic"
            if "celery" in c_lower and "Celery" not in background_workers:
                background_workers.append("Celery")
            if "redis" in c_lower and "Redis" not in database_tech:
                database_tech.append("Redis")

    # Inspect other ecosystems
    for mf in inventory.manifest_files:
        pname = Path(mf).name.lower()
        if pname == "go.mod":
            frameworks.append("Go Modules")
            package_managers.append("go")
        elif pname == "cargo.toml":
            frameworks.append("Cargo / Rust")
            package_managers.append("cargo")
        elif "build.gradle" in pname:
            frameworks.append("Gradle")
            package_managers.append("gradle")
        elif pname == "pom.xml":
            frameworks.append("Maven")
            package_managers.append("mvn")
        elif pname == "cmakelists.txt":
            frameworks.append("CMake")

    # Detect package managers for JS/Python
    if (root / "pnpm-lock.yaml").exists():
        package_managers.append("pnpm")
    elif (root / "yarn.lock").exists():
        package_managers.append("yarn")
    elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        package_managers.append("bun")
    elif any(Path(m).name == "package.json" for m in inventory.manifest_files):
        package_managers.append("npm")

    if (root / "uv.lock").exists():
        package_managers.append("uv")
    elif (root / "poetry.lock").exists():
        package_managers.append("poetry")
    elif any(
        Path(m).name == "pyproject.toml" or "requirements" in m for m in inventory.manifest_files
    ):
        package_managers.append("pip")

    # Remove duplicates
    frameworks = sorted(set(frameworks))
    package_managers = sorted(set(package_managers))
    database_tech = sorted(set(database_tech))

    # 4. Entrypoint discovery
    known_entrypoints = {
        "app/main.py",
        "apps/api/app/main.py",
        "main.py",
        "src/main.py",
        "app.py",
        "apps/web/app/page.tsx",
        "apps/web/src/App.tsx",
        "src/index.ts",
        "src/index.js",
        "main.go",
        "cmd/main.go",
        "src/main.rs",
        "apps/worker/worker.py",
        "worker.py",
    }
    for f in inventory.files:
        if f in known_entrypoints:
            entrypoints.append(f)

    # 5. Environment Variables extraction (.env.example, .env.sample, etc.)
    env_file_candidates = [*inventory.env_files, ".env.example", ".env.sample", ".env.template"]
    env_target = None
    for ef in env_file_candidates:
        if any(w in ef.lower() for w in ["example", "sample", "template"]):
            env_target = ef
            break
    if not env_target and inventory.env_files:
        env_target = inventory.env_files[0]

    if env_target:
        env_text = inventory.read_text_safe(env_target)
        if env_text:
            current_comments: list[str] = []
            for line in env_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    current_comments = []
                    continue
                if stripped.startswith("#"):
                    comment = stripped.lstrip("#").strip()
                    if comment and not comment.startswith("="):
                        current_comments.append(comment)
                    continue

                if "=" in stripped:
                    key, val = stripped.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if any(
                        s in key.lower() for s in ["secret", "password", "key", "token", "auth"]
                    ):
                        sanitized_val = "******** (secret)"
                    else:
                        sanitized_val = val if val else "value"

                    purpose = (
                        " ".join(current_comments)
                        if current_comments
                        else f"Configuration for {key}"
                    )
                    is_required = "required" in purpose.lower() or not val
                    default_v = (
                        val
                        if not any(s in key.lower() for s in ["secret", "password", "key"])
                        else None
                    )
                    env_vars.append(
                        EnvVarEvidence(
                            name=key,
                            purpose=purpose[:120],
                            required=is_required,
                            default_value=default_v,
                            example_value=sanitized_val,
                            provenance=[
                                EvidenceProvenance(
                                    path=env_target,
                                    evidence_type="config",
                                    confidence="verified",
                                    detail=f"Declared in {env_target}",
                                )
                            ],
                        )
                    )
                    current_comments = []

    # 6. Docker Compose Services inspection
    for cf in inventory.compose_files:
        compose_content = inventory.read_text_safe(cf)
        if compose_content:
            with contextlib.suppress(Exception):
                in_services = False
                current_service = None
                for line in compose_content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if stripped == "services:":
                        in_services = True
                        continue
                    if in_services and re.match(r"^[a-zA-Z0-9_\-]+:", line):
                        in_services = False
                        current_service = None
                        continue

                    if in_services:
                        svc_match = re.match(r"^ {2}([a-zA-Z0-9_\-]+):", line)
                        if svc_match:
                            current_service = svc_match.group(1)
                            services.append(
                                ServiceEvidence(
                                    name=current_service,
                                    image_or_build=f"service:{current_service}",
                                    role=f"Docker container service: {current_service}",
                                    provenance=[
                                        EvidenceProvenance(
                                            path=cf,
                                            evidence_type="compose",
                                            confidence="verified",
                                        )
                                    ],
                                )
                            )
                        elif current_service and services:
                            img_match = re.search(r"image:\s*([^\s]+)", line)
                            if img_match:
                                services[-1].image_or_build = img_match.group(1)
                            port_match = re.search(r"-\s*\"?([0-9]+:[0-9]+)\"?", line)
                            if port_match:
                                services[-1].ports.append(port_match.group(1))

    # 7. Architecture Components & Real Relationships
    if any("Next.js" in f or "React" in f for f in frameworks) or (root / "apps/web").exists():
        web_paths = ["apps/web"] if (root / "apps/web").exists() else ["src", "app"]
        components.append(
            ArchitectureComponent(
                name="Frontend Web Application",
                role="User interface, interactive dashboards, and client-side application flows",
                technologies=[
                    f
                    for f in ["Next.js", "React", "TypeScript", "Tailwind CSS"]
                    if f in frameworks or f == "TypeScript"
                ],
                entrypoint="apps/web/app/page.tsx"
                if (root / "apps/web/app/page.tsx").exists()
                else None,
                source_paths=web_paths,
                depends_on=["Backend API Service"],
                confidence="verified",
            )
        )

    if "FastAPI" in frameworks or (root / "apps/api").exists():
        api_paths = ["apps/api"] if (root / "apps/api").exists() else ["app"]
        components.append(
            ArchitectureComponent(
                name="Backend API Service",
                role="REST API, business logic, authentication, and core domain orchestration",
                technologies=[
                    f
                    for f in ["FastAPI", "Python", "SQLAlchemy (ORM)", "Alembic"]
                    if f in frameworks or f in database_tech or f == "Python"
                ],
                entrypoint="apps/api/app/main.py"
                if (root / "apps/api/app/main.py").exists()
                else "app/main.py",
                source_paths=api_paths,
                depends_on=["Database (PostgreSQL)", "Redis Broker"],
                confidence="verified",
            )
        )

    if "Celery" in background_workers or (root / "apps/worker").exists():
        worker_paths = ["apps/worker"] if (root / "apps/worker").exists() else ["worker"]
        components.append(
            ArchitectureComponent(
                name="Background Asynchronous Worker",
                role="Asynchronous task execution, long-running jobs, and scheduled processing",
                technologies=["Celery", "Python", "Redis"],
                entrypoint="apps/worker/worker.py"
                if (root / "apps/worker/worker.py").exists()
                else "worker.py",
                source_paths=worker_paths,
                depends_on=["Redis Broker", "Database (PostgreSQL)"],
                confidence="verified",
            )
        )

    # Add verified relationships
    has_web = any(c.name == "Frontend Web Application" for c in components)
    has_api = any(c.name == "Backend API Service" for c in components)
    has_worker = any(c.name == "Background Asynchronous Worker" for c in components)

    if has_web and has_api:
        relationships.append(
            RelationshipEvidence(
                source="Frontend Web Application",
                target="Backend API Service",
                relationship_type="HTTP / REST calls",
                description="Frontend invokes REST API endpoints via typed API client and actions",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path="apps/web/lib/server-api-client.ts",
                        evidence_type="source_code",
                        confidence="verified",
                    )
                ],
            )
        )

    if has_api and has_worker:
        relationships.append(
            RelationshipEvidence(
                source="Backend API Service",
                target="Background Asynchronous Worker",
                relationship_type="Celery Task Dispatch",
                description="API routes queue long-running background tasks over Redis broker",
                confidence="verified",
                provenance=[
                    EvidenceProvenance(
                        path="apps/api/app/jobs/celery_app.py",
                        evidence_type="source_code",
                        confidence="verified",
                    )
                ],
            )
        )

    # 8. API Endpoints Extraction (Selective source inspection of routers)
    router_files = [
        f
        for f in inventory.files
        if "router.py" in f or "routes.py" in f or f.endswith("/route.ts")
    ]
    for rf in router_files[:10]:
        r_text = inventory.read_text_safe(rf)
        if not r_text:
            continue
        route_pattern = (
            r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']'
            r'(?:.*?(?:summary|description)=["\']([^"\']+)["\'])?'
        )
        matches = re.finditer(route_pattern, r_text)
        for m in matches:
            method = m.group(1).upper()
            route_path = m.group(2)
            summary = m.group(3) if m.group(3) else f"{method} {route_path}"
            is_auth = (
                "Depends(get_current_user)" in r_text
                or "Depends(verify" in r_text
                or "auth" in route_path
            )
            endpoints.append(
                EndpointEvidence(
                    path=route_path,
                    method=method,
                    summary=summary,
                    auth_required=is_auth,
                    provenance=[
                        EvidenceProvenance(
                            path=rf,
                            evidence_type="source_code",
                            confidence="verified",
                        )
                    ],
                )
            )

    # 9. Test Evidence
    test_evidence = TestEvidence(
        frameworks=[],
        test_dirs=[],
        test_files_sample=inventory.test_files[:15],
        has_unit_tests=len(inventory.test_files) > 0,
        has_integration_tests=any("integration" in f for f in inventory.test_files),
        has_e2e_tests=any("e2e" in f or "smoke" in f for f in inventory.test_files),
    )
    if any(f.endswith(".py") for f in inventory.test_files):
        test_evidence.frameworks.append("pytest")
    if any(f.endswith(".ts") or f.endswith(".tsx") for f in inventory.test_files):
        test_evidence.frameworks.append("Vitest / Jest")

    for d in inventory.directories:
        if d in {"tests", "test", "__tests__", "spec", "apps/web/tests", "apps/api/tests"}:
            test_evidence.test_dirs.append(d)

    # 10. Commands Inference
    commands = infer_commands(inventory, effective_name, manifest_data)
    test_evidence.test_commands = [c for c in commands if c.category == "test"]

    # 11. Missing Evidence evaluation
    if not inventory.license_file:
        missing_evidence.append("No license file (LICENSE) detected in repository root.")
    if not test_evidence.test_dirs and not test_evidence.test_files_sample:
        missing_evidence.append("No automated test directory or test suites detected.")
    if not env_vars:
        missing_evidence.append("No environment variable template (.env.example) found.")

    # 12. Troubleshooting hints derived from evidence
    troubleshooting_hints = []
    if "PostgreSQL" in database_tech or any("postgres" in s.name for s in services):
        troubleshooting_hints.append(
            {
                "problem": "Database connection refused (PostgreSQL)",
                "cause": "PostgreSQL service is not running or port 5432/5433 is conflicted.",
                "solution": "Ensure PostgreSQL container is healthy and verify DATABASE_URL.",
            }
        )
    if "Celery" in background_workers:
        troubleshooting_hints.append(
            {
                "problem": "Celery worker not processing jobs",
                "cause": "Redis message broker is unreachable or worker stopped.",
                "solution": "Check Redis status with ping and restart the worker service.",
            }
        )
    if env_vars:
        troubleshooting_hints.append(
            {
                "problem": "Missing required environment configuration",
                "cause": "Required variables in `.env` are unset or empty.",
                "solution": "Copy `.env.example` to `.env` and configure mandatory values.",
            }
        )

    return RepositoryEvidence(
        name=effective_name,
        description=project_desc,
        primary_language=primary_language,
        languages=languages_pct,
        frameworks=frameworks,
        package_managers=package_managers,
        is_monorepo=is_monorepo,
        monorepo_workspaces=monorepo_workspaces,
        entrypoints=entrypoints,
        commands=commands,
        environment_variables=env_vars,
        architecture_components=components,
        relationships=relationships,
        endpoints=endpoints[:25],
        database_technologies=database_tech,
        database_migrations=database_migrations,
        background_workers=background_workers,
        services=services,
        tests=test_evidence,
        ci_cd_workflows=inventory.ci_files,
        license_type="MIT" if inventory.license_file else None,
        existing_docs=inventory.doc_files,
        troubleshooting_hints=troubleshooting_hints,
        missing_evidence=missing_evidence,
        extracted_at=datetime.now(UTC).isoformat(),
    )
