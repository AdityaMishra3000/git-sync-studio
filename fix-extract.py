import re

code = """import json
from pathlib import Path


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

    if (repo_path / "pyproject.toml").exists():
        evidence["architecture"]["framework"] = "Python"

    # Detect test folders
    test_folders = ["tests", "test", "__tests__", "spec", "e2e"]
    for folder in test_folders:
        if (repo_path / folder).is_dir():
            evidence["tests"]["folder"] = folder
            break

    return evidence


def generate_readme(evidence: dict) -> str:
    lines = ["# GitSync Project", ""]

    framework = evidence.get("architecture", {}).get("framework")
    if framework:
        lines.append(f"This is a {framework} project.")
        lines.append("")

    scripts = evidence.get("scripts", {})
    if scripts:
        lines.append("## Scripts")
        for k, v in scripts.items():
            lines.append(f"- `{k}`: {v}")

    return "\\n".join(lines)
"""

with open("apps/api/app/readme/extract.py", "w") as f:
    f.write(code)

print("Fixed extract.py")
