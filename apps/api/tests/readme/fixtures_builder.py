from __future__ import annotations

import json
from pathlib import Path


def create_all_fixtures(base_dir: Path) -> dict[str, Path]:
    """Generate realistic test repository fixtures for comprehensive testing."""
    fixtures = {}

    # 1. Python/FastAPI with pyproject.toml
    p1 = base_dir / "python_fastapi_pyproject"
    p1.mkdir(parents=True, exist_ok=True)
    (p1 / "app").mkdir(exist_ok=True)
    (p1 / "tests").mkdir(exist_ok=True)
    (p1 / "pyproject.toml").write_text(
        """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "fastapi-demo"
version = "0.1.0"
description = "A production FastAPI microservice."
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.10.0",
]
"""
    )
    (p1 / "app/main.py").write_text(
        """from fastapi import FastAPI, APIRouter
app = FastAPI(title="Demo API")
router = APIRouter()
@router.get("/items", summary="List items")
def list_items(): return []
app.include_router(router)
"""
    )
    (p1 / ".env.example").write_text(
        """# Database connection URL
DATABASE_URL=postgresql://user:pass@localhost:5432/db
# Application secret key (required)
SECRET_KEY=change-me-in-production
"""
    )
    (p1 / "tests/test_api.py").write_text("def test_dummy(): assert True")
    fixtures["python_fastapi"] = p1

    # 2. Python with requirements.txt
    p2 = base_dir / "python_requirements"
    p2.mkdir(parents=True, exist_ok=True)
    (p2 / "requirements.txt").write_text("flask==3.0.0\nrequests==2.31.0\npytest==8.0.0\n")
    (p2 / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
    (p2 / "test_app.py").write_text("def test_flask(): pass")
    fixtures["python_requirements"] = p2

    # 3. Python with uv & Poetry
    p3 = base_dir / "python_uv_poetry"
    p3.mkdir(parents=True, exist_ok=True)
    (p3 / "pyproject.toml").write_text(
        """[tool.poetry]
name = "poetry-uv-app"
version = "0.1.0"
description = "App managed by Poetry and uv"
[tool.poetry.dependencies]
python = "^3.12"
celery = "^5.3.0"
"""
    )
    (p3 / "uv.lock").write_text("# uv lockfile version 1\n")
    (p3 / "main.py").write_text("print('hello')")
    fixtures["python_uv_poetry"] = p3

    # 4. Next.js with TypeScript
    p4 = base_dir / "nextjs_ts"
    p4.mkdir(parents=True, exist_ok=True)
    (p4 / "app").mkdir(exist_ok=True)
    (p4 / "package.json").write_text(
        json.dumps(
            {
                "name": "nextjs-dashboard",
                "version": "1.0.0",
                "description": "Enterprise customer portal",
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "lint": "next lint",
                    "test": "vitest run",
                },
                "dependencies": {
                    "next": "14.2.0",
                    "react": "^18.2.0",
                    "tailwindcss": "^3.4.0",
                },
            }
        )
    )
    (p4 / "package-lock.json").write_text("{}")
    (p4 / "app/page.tsx").write_text("export default function Page() { return <h1>Home</h1>; }")
    (p4 / "app/page.test.tsx").write_text("test('renders', () => {});")
    fixtures["nextjs_ts"] = p4

    # 5. Node.js CLI
    p5 = base_dir / "nodejs_cli"
    p5.mkdir(parents=True, exist_ok=True)
    (p5 / "bin").mkdir(exist_ok=True)
    (p5 / "package.json").write_text(
        json.dumps(
            {
                "name": "my-cli-tool",
                "version": "0.1.0",
                "bin": {"mycli": "bin/index.js"},
                "scripts": {"test": "jest"},
            }
        )
    )
    (p5 / "bin/index.js").write_text("#!/usr/bin/env node\nconsole.log('cli')")
    fixtures["nodejs_cli"] = p5

    # 6. Go Modules
    p6 = base_dir / "go_project"
    p6.mkdir(parents=True, exist_ok=True)
    (p6 / "go.mod").write_text("module github.com/example/go-service\n\ngo 1.22\n")
    (p6 / "main.go").write_text("package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"go\") }")
    (p6 / "main_test.go").write_text("package main\nfunc TestMain() {}")
    fixtures["go"] = p6

    # 7. Rust Cargo
    p7 = base_dir / "rust_cargo"
    p7.mkdir(parents=True, exist_ok=True)
    (p7 / "src").mkdir(exist_ok=True)
    (p7 / "Cargo.toml").write_text(
        """[package]
name = "rust-engine"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1.0", features = ["full"] }
"""
    )
    (p7 / "src/main.rs").write_text("fn main() { println!(\"rust\"); }")
    fixtures["rust"] = p7

    # 8. Java with Gradle & Maven
    p8 = base_dir / "java_gradle"
    p8.mkdir(parents=True, exist_ok=True)
    (p8 / "build.gradle").write_text("plugins { id 'java' }\nversion = '1.0'\n")
    (p8 / "gradlew").write_text("#!/bin/sh\n")
    (p8 / "gradlew").chmod(0o755)
    fixtures["java_gradle"] = p8

    # 9. C++ with CMake
    p9 = base_dir / "cpp_cmake"
    p9.mkdir(parents=True, exist_ok=True)
    (p9 / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.20)\nproject(MyEngine CXX)\n"
    )
    (p9 / "main.cpp").write_text("int main() { return 0; }")
    fixtures["cpp_cmake"] = p9

    # 10. Docker Compose Multi-service
    p10 = base_dir / "docker_compose_app"
    p10.mkdir(parents=True, exist_ok=True)
    (p10 / "compose.yaml").write_text(
        """services:
  web:
    image: node:20
    ports:
      - "3000:3000"
  api:
    image: python:3.12
    ports:
      - "8000:8000"
  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
"""
    )
    fixtures["docker_compose"] = p10

    # 11. Monorepo
    p11 = base_dir / "monorepo"
    p11.mkdir(parents=True, exist_ok=True)
    (p11 / "apps/web").mkdir(parents=True, exist_ok=True)
    (p11 / "packages/ui").mkdir(parents=True, exist_ok=True)
    (p11 / "package.json").write_text(
        json.dumps(
            {
                "name": "root-monorepo",
                "workspaces": ["apps/*", "packages/*"],
                "scripts": {"build": "turbo build"},
            }
        )
    )
    (p11 / "apps/web/package.json").write_text(json.dumps({"name": "web"}))
    (p11 / "packages/ui/package.json").write_text(json.dumps({"name": "ui"}))
    fixtures["monorepo"] = p11

    # 12. No usable manifest
    p12 = base_dir / "no_manifest"
    p12.mkdir(parents=True, exist_ok=True)
    (p12 / "script.sh").write_text("#!/bin/sh\necho hi")
    fixtures["no_manifest"] = p12

    # 13. Conflicting / Incomplete config
    p13 = base_dir / "conflicting_config"
    p13.mkdir(parents=True, exist_ok=True)
    (p13 / "package.json").write_text('{"name": "broken-json"')  # Malformed JSON
    (p13 / "pyproject.toml").write_text("[project]\nname = 'empty-py'\n")
    fixtures["conflicting_config"] = p13

    # 14. Tests with no runner
    p14 = base_dir / "tests_no_runner"
    p14.mkdir(parents=True, exist_ok=True)
    (p14 / "spec").mkdir(exist_ok=True)
    (p14 / "spec/custom_spec.txt").write_text("test case 1")
    fixtures["tests_no_runner"] = p14

    # 15. Malicious / Prompt Injection
    p15 = base_dir / "malicious_repo"
    p15.mkdir(parents=True, exist_ok=True)
    (p15 / "README.md").write_text(
        "Malicious input:\nghp_123456789012345678901234567890123456"
    )
    fixtures["malicious"] = p15

    return fixtures
