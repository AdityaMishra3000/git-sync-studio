import json
from pathlib import Path
import os


def extract_evidence(repo_path: Path) -> dict:
    evidence = {
        "repo": {},
        "languages": {},
        "topics": [],
        "files": [],
        "scripts": {},
        "tests": {},
        "architecture": {},
        "recent_commits": [],
    }

    if (repo_path / "package.json").exists():
        with open(repo_path / "package.json") as f:
            import contextlib

            with contextlib.suppress(Exception):
                pkg = json.load(f)
                evidence["scripts"] = pkg.get("scripts", {})
                evidence["architecture"]["framework"] = "Node.js"
                evidence["repo"]["name"] = pkg.get("name", "Project Name")

    elif (repo_path / "pyproject.toml").exists() or (repo_path / "requirements.txt").exists():
        evidence["architecture"]["framework"] = "Python"
        
    elif (repo_path / "build.gradle").exists() or (repo_path / "settings.gradle").exists():
        evidence["architecture"]["framework"] = "Java / Android (Gradle)"
        
    elif (repo_path / "pom.xml").exists():
        evidence["architecture"]["framework"] = "Java (Maven)"
        
    elif (repo_path / "CMakeLists.txt").exists():
        evidence["architecture"]["framework"] = "C++ (CMake)"
        
    elif (repo_path / "go.mod").exists():
        evidence["architecture"]["framework"] = "Go"
        
    elif (repo_path / "Cargo.toml").exists():
        evidence["architecture"]["framework"] = "Rust"

    test_names = {"tests", "test", "__tests__", "spec", "e2e"}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".venv", ".venv-ml", "dist", "build", "coverage"}]
        
        # 1. Check for dedicated test directories
        for name in test_names:
            if name in dirs:
                rel = (Path(root) / name).relative_to(repo_path)
                evidence["tests"]["folder"] = str(rel)
                break
                
        # 2. Check for co-located test files (e.g., App.test.tsx, test_api.py)
        if not evidence.get("tests"):
            for file_name in files:
                if ".test." in file_name or ".spec." in file_name or file_name.startswith("test_"):
                    rel = (Path(root) / file_name).relative_to(repo_path)
                    evidence["tests"]["file"] = str(rel)
                    break

        if evidence.get("tests"):
            break

    return evidence


def generate_readme(evidence: dict) -> str:
    repo_name = evidence.get("repo", {}).get("name", "Project Name")
    lines = [
        f"# {repo_name}",
        "",
        "Welcome to the project! This README is auto-generated based on detected repository evidence.",
        "",
        "## Overview",
    ]

    framework = evidence.get("architecture", {}).get("framework")
    if framework:
        lines.append(f"This repository is primarily built with **{framework}**.")
    else:
        lines.append("This repository contains various source files.")
    
    lines.append("")
    lines.append("## Setup & Installation")
    lines.append("To get started with this project, clone the repository and install the dependencies:")
    lines.append("```bash")
    if framework == "Node.js":
        lines.append("npm install")
    elif framework == "Python":
        lines.append("pip install -r requirements.txt")
    elif framework == "Java / Android (Gradle)":
        lines.append("./gradlew build")
    elif framework == "Java (Maven)":
        lines.append("mvn install")
    elif framework == "C++ (CMake)":
        lines.append("mkdir build && cd build && cmake .. && make")
    elif framework == "Go":
        lines.append("go mod download")
    elif framework == "Rust":
        lines.append("cargo build")
    else:
        lines.append("# Setup instructions here")
    lines.append("```")
    lines.append("")

    scripts = evidence.get("scripts", {})
    if scripts:
        lines.append("## Available Commands")
        lines.append("You can run the following scripts:")
        for k, v in scripts.items():
            lines.append(f"- `npm run {k}`: `{v}`")
        lines.append("")

    tests = evidence.get("tests", {})
    if tests:
        lines.append("## Testing")
        lines.append(f"Tests have been detected in the repository.")
        if "folder" in tests:
            lines.append(f"- **Test Directory:** `{tests['folder']}`")
        if "file" in tests:
            lines.append(f"- **Test File:** `{tests['file']}`")
        lines.append("")

    lines.append("## Architecture & Structure")
    lines.append("Review the codebase to understand its architectural decisions.")
    
    return "\n".join(lines)
