code = """import json
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

    if (repo_path / "pyproject.toml").exists():
        evidence["architecture"]["framework"] = "Python"

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

print("Co-located test files detection added.")
